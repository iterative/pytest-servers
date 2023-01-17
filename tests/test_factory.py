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


with_versioning = [
    param for param in implementations if param.values[0] in ("s3", "gcs")
]


@pytest.mark.parametrize(
    "fs,cls",
    implementations,
    ids=[param.values[0] for param in implementations],  # type: ignore
)
class TestTmpUPathFactory:
    def test_init(self, tmp_upath_factory, fs, cls):
        path = tmp_upath_factory.mktemp(fs)
        assert isinstance(path, cls)
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


@pytest.mark.parametrize(
    "fs,cls",
    with_versioning,
    ids=[param.values[0] for param in with_versioning],  # type: ignore
)
class TestTmpUPathFactoryVersioning:
    def test_mktemp(self, tmp_upath_factory, fs, cls):
        path = tmp_upath_factory.mktemp(fs, version_aware=True)
        assert path.fs.version_aware
