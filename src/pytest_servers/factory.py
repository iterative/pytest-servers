import os
import sys
import tempfile
from typing import Any, Dict, Optional

import pytest
from upath import UPath

from pytest_servers.exceptions import RemoteUnavailable
from pytest_servers.local import LocalPath
from pytest_servers.utils import random_string


class TempUPathFactory:
    """Factory for temporary directories with universal-pathlib and mocked servers"""  # noqa: E501

    mock_remotes = {
        # remote: (fixture_name, config attribute name, requires docker)
        "azure": ("azurite", "_azure_connection_string", True),
        "gcs": ("fake_gcs_server", "_gcs_endpoint_url", True),
        "s3": ("s3_server", "_s3_endpoint_url", False),
    }

    def __init__(
        self,
        s3_endpoint_url: Optional[str] = None,
        azure_connection_string: Optional[str] = None,
        gcs_endpoint_url: Optional[str] = None,
    ):
        self._request: Optional["pytest.FixtureRequest"] = None

        self._local_path_factory: Optional["pytest.TempPathFactory"] = None
        self._azure_connection_string = azure_connection_string
        self._gcs_endpoint_url = gcs_endpoint_url
        self._s3_endpoint_url = s3_endpoint_url

    @classmethod
    def from_request(
        cls, request: "pytest.FixtureRequest", *args, **kwargs
    ) -> "TempUPathFactory":
        """Create a factory according to pytest configuration."""
        tmp_upath_factory = cls(*args, **kwargs)
        tmp_upath_factory._local_path_factory = (
            pytest.TempPathFactory.from_config(request.config, _ispytest=True)
        )
        tmp_upath_factory._request = request

        return tmp_upath_factory

    def _mock_remote_setup(self, fs: "str") -> None:
        try:
            (
                mock_remote_fixture,
                remote_config_name,
                needs_docker,
            ) = self.mock_remotes[fs]
        except KeyError:
            raise RemoteUnavailable(f"No mock remote available for fs: {fs}")

        if getattr(self, remote_config_name):  # remote is already configured
            return

        if needs_docker and os.environ.get("CI"):
            if sys.platform == "win32":
                pytest.skip(
                    "disabled for Windows on Github Actions: "
                    "https://github.com/actions/runner-images/issues/1143"
                )
            elif sys.platform == "darwin":
                pytest.skip(
                    "disabled for MacOS on Github Actions: "
                    "https://github.com/actions/runner-images/issues/2150"
                )

        assert self._request
        try:
            remote_config = self._request.getfixturevalue(mock_remote_fixture)
        except pytest.FixtureLookupError:
            raise RemoteUnavailable(
                f'{fs}: Failed to setup "{mock_remote_fixture}" fixture'
            )
        setattr(self, remote_config_name, remote_config)

    def mktemp(
        self,
        fs: str = "local",
        mock: bool = True,
        version_aware: bool = False,
        **kwargs,
    ) -> "UPath":
        """Create a new temporary directory managed by the factory.

        :param fs:
            Filesystem type, one of
            - local (default)
            - memory
            - s3
            - azure
            - gcs

        :param mock:
            Set to False to use real remotes

        :returns:
            :class:`upath.Upath` to the new directory.
        """
        if fs == "local":
            if version_aware:
                raise NotImplementedError(f"not implemented for {fs=}")
            return self.local()
        elif fs == "memory":
            if version_aware:
                raise NotImplementedError(f"not implemented for {fs=}")
            return self.memory(**kwargs)

        if mock:
            self._mock_remote_setup(fs)

        if fs == "s3":
            return self.s3(
                endpoint_url=self._s3_endpoint_url,
                version_aware=version_aware,
                **kwargs,
            )
        elif fs == "azure":
            if version_aware and mock:
                raise NotImplementedError(f"not implemented for {fs=}")
            if not self._azure_connection_string:
                raise RemoteUnavailable("missing connection string")
            return self.azure(
                connection_string=self._azure_connection_string, **kwargs
            )
        elif fs == "gcs":
            return self.gcs(
                endpoint_url=self._gcs_endpoint_url,
                version_aware=version_aware,
                **kwargs,
            )
        else:
            raise ValueError(fs)

    def local(self):
        mktemp = (
            self._local_path_factory.mktemp
            if self._local_path_factory is not None
            else tempfile.mktemp
        )
        return LocalPath(mktemp("pytest-servers"))

    def s3(
        self,
        endpoint_url: Optional[str] = None,
        version_aware: bool = False,
        **kwargs,
    ) -> UPath:
        """Creates a new S3 bucket and returns an UPath instance  .

        `endpoint_url` can be used to use custom servers (e.g. moto s3)."""
        client_kwargs: Dict[str, Any] = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        bucket_name = f"pytest-servers-{random_string()}"
        path = UPath(
            f"s3://{bucket_name}",
            client_kwargs=client_kwargs,
            version_aware=version_aware,
            **kwargs,
        )
        if version_aware:
            from botocore.session import Session

            session = Session()
            client = session.create_client("s3", endpoint_url=endpoint_url)
            client.create_bucket(Bucket=bucket_name, ACL="public-read")

            client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={"Status": "Enabled"},
            )
        else:
            path.mkdir()

        return path

    def azure(self, connection_string: str, **kwargs) -> UPath:
        """Creates a new container and returns an UPath instance"""
        container_name = f"pytest-servers-{random_string()}"
        path = UPath(
            f"az://{container_name}",
            connection_string=connection_string,
            **kwargs,
        )
        path.mkdir(parents=True, exist_ok=False)
        return path

    def memory(self, **kwargs) -> UPath:
        """Creates a new temporary in-memory path returns an UPath instance"""
        path = UPath(
            f"memory:/{random_string()}",
            **kwargs,
        )
        path.mkdir()
        return path

    def gcs(
        self,
        endpoint_url: Optional[str] = None,
        version_aware: bool = False,
        **kwargs,
    ) -> UPath:
        """Creates a new gcs bucket and returns an UPath instance.

        `endpoint_url` can be used to use custom servers
        (e.g. fake-gcs-server).
        """
        client_kwargs: Dict[str, Any] = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        bucket_name = f"pytest-servers-{random_string()}"

        path = UPath(
            f"gcs://{bucket_name}",
            version_aware=version_aware,
            **client_kwargs,
            **kwargs,
        )
        if version_aware:
            path.fs.mkdir(bucket_name, enable_versioning=True, exist_ok=False)
        else:
            path.mkdir(parents=True, exist_ok=False)

        # UPath adds a trailing slash here, due to which
        # gcsfs.isdir() returns False.
        # pylint: disable=protected-access,assigning-non-slot
        original = path._accessor._format_path
        path._accessor._format_path = lambda p: original(p).rstrip("/")
        return path
