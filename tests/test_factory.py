import pytest
import upath

from pytest_servers.local import LocalPath


class TestFactory:
    def test_local_path(self, tmp_upath_factory):
        local_path = tmp_upath_factory.mktemp()
        assert isinstance(local_path, LocalPath)
        assert local_path.is_dir()
        assert list(local_path.iterdir()) == []

    def test_s3_path(self, tmp_upath_factory):
        s3_path = tmp_upath_factory.mktemp("s3")
        assert isinstance(s3_path, upath.implementations.cloud.S3Path)
        assert s3_path.exists()
        assert list(s3_path.iterdir()) == []

    def test_azure_path(self, tmp_upath_factory):
        azure_path = tmp_upath_factory.mktemp("azure")
        assert isinstance(azure_path, upath.implementations.cloud.AzurePath)
        assert azure_path.exists()
        assert list(azure_path.iterdir()) == []

    @pytest.mark.parametrize("fs", ["local", "s3", "azure"])
    def test_multiple_paths(self, tmp_upath_factory, fs):
        path_1 = tmp_upath_factory.mktemp(fs)
        path_2 = tmp_upath_factory.mktemp(fs)
        assert str(path_1) != str(path_2)
