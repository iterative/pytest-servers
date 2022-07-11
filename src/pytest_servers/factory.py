import tempfile
from typing import TYPE_CHECKING, Optional

from pytest import TempPathFactory
from upath import UPath

from pytest_servers.exceptions import RemoteUnavailable
from pytest_servers.local import LocalPath
from pytest_servers.utils import random_string, skip_or_raise_on

if TYPE_CHECKING:
    from pytest import Config


class TempUPathFactory:
    """Factory for temporary directories with universal-pathlib and mocked servers"""  # noqa: E501

    def __init__(
        self,
        s3_endpoint_url: Optional[str] = None,
        azure_connection_string: Optional[str] = None,
        gcs_endpoint_url: Optional[str] = None,
    ):
        self._local_path_factory: Optional["TempPathFactory"] = None
        self._s3_endpoint_url = s3_endpoint_url
        self._azure_connection_string = azure_connection_string
        self._gcs_endpoint_url = gcs_endpoint_url

    @classmethod
    def from_config(
        cls, config: "Config", *args, **kwargs
    ) -> "TempUPathFactory":
        """Create a factory according to pytest configuration."""
        tmp_upath_factory = cls(*args, **kwargs)
        tmp_upath_factory._local_path_factory = TempPathFactory.from_config(
            config, _ispytest=True
        )

        return tmp_upath_factory

    @skip_or_raise_on(ImportError, RemoteUnavailable)
    def mktemp(self, fs: str = "local", **kwargs) -> "UPath":
        """Create a new temporary directory managed by the factory.

        :param fs:
            Filesystem type, one of
            - local (default)
            - memory
            - s3
            - azure
            - gcs

        :returns:
            :class:`upath.Upath` to the new directory.
        """
        if fs == "local":
            return self.local_temp_path()
        elif fs == "memory":
            return self.memory_temp_path(**kwargs)
        elif fs == "s3":
            if not self._s3_endpoint_url:
                raise RemoteUnavailable(fs)
            return self.s3_temp_path(
                region_name="eu-south-1",
                endpoint_url=self._s3_endpoint_url,
                **kwargs,
            )
        elif fs == "azure":
            if not self._azure_connection_string:
                raise RemoteUnavailable(fs)
            return self.azure_temp_path(
                connection_string=self._azure_connection_string, **kwargs
            )
        elif fs == "gcs":
            if not self._gcs_endpoint_url:
                raise RemoteUnavailable(fs)
            return self.gcs_temp_path(
                endpoint_url=self._gcs_endpoint_url,
                **kwargs,
            )
        else:
            raise ValueError(fs)

    def local_temp_path(self):
        mktemp = (
            self._local_path_factory.mktemp
            if self._local_path_factory is not None
            else tempfile.mktemp
        )
        return LocalPath(mktemp("pytest-servers"))

    def s3_temp_path(
        self, region_name: str, endpoint_url: Optional[str] = None, **kwargs
    ) -> UPath:
        """Creates a new S3 bucket and returns an UPath instance  .

        `endpoint_url` can be used to use custom servers (e.g. moto s3)."""
        client_kwargs = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        if region_name:
            client_kwargs["region_name"] = region_name

        bucket_name = f"pytest-servers-{random_string()}"
        path = UPath(
            f"s3://{bucket_name}", client_kwargs=client_kwargs, **kwargs
        )
        path.mkdir()
        return path

    def azure_temp_path(self, connection_string: str, **kwargs) -> UPath:
        """Creates a new container and returns an UPath instance"""
        container_name = f"pytest-servers-{random_string()}"
        path = UPath(
            f"az://{container_name}",
            connection_string=connection_string,
            **kwargs,
        )
        path.mkdir()
        return path

    def memory_temp_path(self, **kwargs) -> UPath:
        """Creates a new temporary in-memory path returns an UPath instance"""
        path = UPath(
            f"memory:/{random_string()}",
            **kwargs,
        )
        path.mkdir()
        return path

    def gcs_temp_path(
        self, endpoint_url: Optional[str] = None, **kwargs
    ) -> UPath:
        """Creates a new gcs bucket and returns an UPath instance.

        `endpoint_url` can be used to use custom servers
        (e.g. fake-gcs-server).
        """
        client_kwargs = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        bucket_name = f"pytest-servers-{random_string()}"
        path = UPath(f"gcs://{bucket_name}", **client_kwargs, **kwargs)
        path.mkdir()
        return path
