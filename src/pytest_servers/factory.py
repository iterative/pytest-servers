import tempfile
from typing import TYPE_CHECKING, Optional

from pytest import TempPathFactory
from upath import UPath

from pytest_servers.local import LocalPath
from pytest_servers.utils import random_string

if TYPE_CHECKING:
    from pytest import Config


class TempUPathFactory:
    """Factory for temporary directories with universal-pathlib and mocked servers"""  # noqa: E501

    def __init__(self):
        self._local_path_factory = None
        self._s3_endpoint_url = None

    @classmethod
    def from_config(
        cls, config: "Config", s3_endpoint_url: Optional[str] = None
    ) -> "TempUPathFactory":
        """Create a factory according to pytest configuration.

        :meta private:
        """
        tmp_upath_factory = cls()
        tmp_upath_factory._local_path_factory = TempPathFactory.from_config(
            config, _ispytest=True
        )
        tmp_upath_factory._s3_endpoint_url = s3_endpoint_url

        return tmp_upath_factory

    def mktemp(self, fs: str = "local") -> "UPath":
        """Create a new temporary directory managed by the factory.

        :param fs:
            Filesystem type, one of "local" (default), "s3"

        :returns:
            :class:`upath.Upath` to the new directory.
        """
        if fs == "local":
            mktemp = (
                self._local_path_factory.mktemp
                if self._local_path_factory
                else tempfile.mktemp
            )
            return LocalPath(mktemp("pytest-servers"))

        elif fs == "s3":
            return self.s3_temp_path(
                "eu-south-1", endpoint_url=self._s3_endpoint_url
            )
        else:
            raise ValueError(fs)

    def s3_temp_path(
        self,
        region_name: str,
        endpoint_url: Optional[str] = None,
    ):
        """Creates a new S3 bucket and returns an UPath instance  .

        endpoint_url can be used to use custom servers (e.g. moto s3)."""
        client_kwargs = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        if region_name:
            client_kwargs["region_name"] = region_name

        bucket_name = f"pytest-servers-{random_string()}"
        path = UPath(f"s3://{bucket_name}", client_kwargs=client_kwargs)
        path.mkdir()
        return path
