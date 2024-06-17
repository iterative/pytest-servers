from __future__ import annotations

import os
import sys
import tempfile
from typing import Any, ClassVar

import pytest
from upath import UPath

from pytest_servers.exceptions import RemoteUnavailable
from pytest_servers.local import LocalPath
from pytest_servers.utils import random_string

from .utils import MockRemote


class TempUPathFactory:
    """Factory for temporary directories with universal-pathlib and mocked servers."""

    mock_remotes: ClassVar[dict[str, MockRemote]] = {
        "azure": MockRemote(
            "azurite",
            "_azure_connection_string",
            requires_docker=True,
        ),
        "gcs": MockRemote(
            "fake_gcs_server",
            "_gcs_endpoint_url",
            requires_docker=True,
        ),
        "gs": MockRemote(
            "fake_gcs_server",
            "_gcs_endpoint_url",
            requires_docker=True,
        ),
        "s3": MockRemote(
            "s3_server",
            "_s3_client_kwargs",
            requires_docker=False,
        ),
    }

    def __init__(
        self,
        s3_client_kwargs: dict[str, str] | None = None,
        azure_connection_string: str | None = None,
        gcs_endpoint_url: str | None = None,
    ) -> None:
        self._request: pytest.FixtureRequest | None = None

        self._local_path_factory: pytest.TempPathFactory | None = None
        self._azure_connection_string = azure_connection_string
        self._gcs_endpoint_url = gcs_endpoint_url
        self._s3_client_kwargs = s3_client_kwargs

    @classmethod
    def from_request(
        cls: type[TempUPathFactory],
        request: pytest.FixtureRequest,
        tmp_path_factory: pytest.TempPathFactory,
        *args,
        **kwargs,
    ) -> TempUPathFactory:
        """Create a factory according to pytest configuration."""
        tmp_upath_factory = cls(*args, **kwargs)
        tmp_upath_factory._local_path_factory = tmp_path_factory  # noqa: SLF001
        tmp_upath_factory._request = request  # noqa: SLF001

        return tmp_upath_factory

    def _mock_remote_setup(self, fs: str) -> None:
        try:
            fixture, config_attr, needs_docker = self.mock_remotes[fs]
        except KeyError:
            msg = f"No mock remote available for fs: {fs}"
            raise RemoteUnavailable(msg) from None

        if getattr(self, config_attr):
            # remote is already configured
            return

        if needs_docker and os.environ.get("CI") and sys.platform == "win32":
            pytest.skip(
                "disabled for Windows on Github Actions: "
                "https://github.com/actions/runner-images/issues/1143",
            )

        assert self._request
        remote_config = self._request.getfixturevalue(fixture)

        setattr(self, config_attr, remote_config)

    def mktemp(  # noqa: C901 # complex-structure
        self,
        fs: str = "local",
        *,
        mock: bool = True,
        version_aware: bool = False,
        **kwargs,
    ) -> UPath:
        """Create a new temporary directory managed by the factory.

        :param fs:
            Filesystem type, one of
            - local (default)
            - memory
            - s3
            - azure
            - gcs
            - gs (alias for gcs)

        :param mock:
            Set to False to use real remotes

        :returns:
            :class:`upath.Upath` to the new directory.
        """
        if fs == "local":
            if version_aware:
                msg = f"not implemented for {fs=}"
                raise NotImplementedError(msg)
            return self.local()
        if fs == "memory":
            if version_aware:
                msg = f"not implemented for {fs=}"
                raise NotImplementedError(msg)
            return self.memory(**kwargs)

        if mock:
            try:
                self._mock_remote_setup(fs)
            except Exception as exc:  # noqa: BLE001
                assert self._request
                from_exc = exc if self._request.config.option.verbose >= 1 else None
                msg = f"{fs}: Failed to setup mock remote: {exc}" + (
                    "" if from_exc else "\nRun `pytest -v` for more details"
                )
                raise RemoteUnavailable(msg) from from_exc

        if fs == "s3":
            return self.s3(
                client_kwargs=self._s3_client_kwargs,
                version_aware=version_aware,
                **kwargs,
            )
        if fs == "azure":
            if version_aware and mock:
                msg = f"not implemented for {fs=}"
                raise NotImplementedError(msg)
            if not self._azure_connection_string:
                msg = "missing connection string"
                raise RemoteUnavailable(msg)
            return self.azure(connection_string=self._azure_connection_string, **kwargs)

        if fs == "gcs":
            return self.gcs(
                endpoint_url=self._gcs_endpoint_url,
                version_aware=version_aware,
                **kwargs,
            )

        if fs == "gs":
            return self.gs(
                endpoint_url=self._gcs_endpoint_url,
                version_aware=version_aware,
                **kwargs,
            )
        raise ValueError(fs)

    def local(self) -> LocalPath:
        """Create a local temporary path."""
        mktemp = (
            self._local_path_factory.mktemp
            if self._local_path_factory is not None
            else tempfile.mktemp
        )
        return LocalPath(mktemp("pytest-servers"))  # type: ignore[operator]

    def s3(
        self,
        client_kwargs: dict[str, Any] | None = None,
        *,
        version_aware: bool = False,
        **kwargs,
    ) -> UPath:
        """Create a new S3 bucket and returns an UPath instance.

        `client_kwargs` can be used to configure the underlying boto client
        """
        bucket_name = f"pytest-servers-{random_string()}"
        path = UPath(
            f"s3://{bucket_name}",
            endpoint_url=client_kwargs.get("endpoint_url") if client_kwargs else None,
            client_kwargs=client_kwargs,
            version_aware=version_aware,
            **kwargs,
        )
        if version_aware:
            from botocore.session import Session

            session = Session()
            client = session.create_client("s3", **client_kwargs)
            client.create_bucket(
                Bucket=bucket_name,
                ACL="public-read",
                CreateBucketConfiguration={
                    "LocationConstraint": client_kwargs.get("region_name"),
                }
                if client_kwargs
                else None,
            )

            client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={"Status": "Enabled"},
            )
        else:
            path.mkdir()

        return path

    def azure(
        self,
        connection_string: str,
        **kwargs,
    ) -> UPath:
        """Create a new container and return an UPath instance."""
        from azure.storage.blob import BlobServiceClient

        container_name = f"pytest-servers-{random_string()}"
        client = BlobServiceClient.from_connection_string(conn_str=connection_string)
        client.create_container(container_name)

        return UPath(
            f"az://{container_name}",
            connection_string=connection_string,
            **kwargs,
        )

    def memory(
        self,
        **kwargs,
    ) -> UPath:
        """Create a new temporary in-memory path returns an UPath instance."""
        path = UPath(
            f"memory:/{random_string()}",
            **kwargs,
        )
        path.mkdir()
        return path

    def gs(
        self,
        endpoint_url: str | None = None,
        *,
        version_aware: bool = False,
        **kwargs,
    ) -> UPath:
        return self._gs(
            "gs",
            endpoint_url=endpoint_url,
            version_aware=version_aware,
            **kwargs,
        )

    def gcs(
        self,
        endpoint_url: str | None = None,
        *,
        version_aware: bool = False,
        **kwargs,
    ) -> UPath:
        return self._gs(
            "gcs",
            endpoint_url=endpoint_url,
            version_aware=version_aware,
            **kwargs,
        )

    def _gs(
        self,
        scheme: str,
        endpoint_url: str | None = None,
        *,
        version_aware: bool = False,
        **kwargs,
    ) -> UPath:
        """Create a new gcs bucket and return an UPath instance.

        `endpoint_url` can be used to use custom servers
        (e.g. fake-gcs-server).
        """
        client_kwargs: dict[str, Any] = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        bucket_name = f"pytest-servers-{random_string()}"

        path = UPath(
            f"{scheme}://{bucket_name}",
            version_aware=version_aware,
            **client_kwargs,
            **kwargs,
        )
        path.fs.mkdir(bucket_name, enable_versioning=version_aware, exist_ok=False)
        return path
