import importlib

import pytest
import upath.implementations.cloud
import upath.implementations.memory

from pytest_servers.local import LocalPath

for module in ["s3fs", "adlfs", "gcsfs"]:
    importlib.import_module(module)


implementations = [
    pytest.param("local", LocalPath),
    pytest.param(
        "memory",
        upath.implementations.memory.MemoryPath,
    ),
    pytest.param(
        "s3",
        upath.implementations.cloud.S3Path,
    ),
    pytest.param(
        "azure",
        upath.implementations.cloud.AzurePath,
    ),
    pytest.param(
        "gcs",
        upath.implementations.cloud.GCSPath,
    ),
]


@pytest.mark.parametrize(
    "fs,cls",
    implementations,
    ids=(param.values[0] for param in implementations),  # type: ignore
)
class TestTmpUPathFactory:
    def test_init(self, tmp_upath_factory, fs, cls):
        path = tmp_upath_factory.mktemp(fs)
        assert isinstance(path, cls)
        if fs != "gcs":  # for empty buckets on gcs path.exists() == False
            assert path.exists()

    def test_is_empty(self, tmp_upath_factory, fs, cls):
        path = tmp_upath_factory.mktemp(fs)
        assert list(path.iterdir()) == []

    def test_write_text(self, tmp_upath_factory, fs, cls):
        file = tmp_upath_factory.mktemp(fs) / "foo"
        assert file.write_text("bar")
        assert file.read_text() == "bar"

    def test_multiple_paths(self, tmp_upath_factory, fs, cls):
        path_1 = tmp_upath_factory.mktemp(fs)
        path_2 = tmp_upath_factory.mktemp(fs)
        assert str(path_1) != str(path_2)
