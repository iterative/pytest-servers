import importlib
import sys
from typing import TYPE_CHECKING

import pytest
import upath.implementations.cloud
import upath.implementations.memory

from pytest_servers.local import LocalPath

if TYPE_CHECKING:
    from _pytest.mark import MarkDecorator

for module in ["s3fs", "adlfs", "gcsfs"]:
    try:
        importlib.import_module(module)
    except ModuleNotFoundError:
        pass


def skip_if_module_missing(name: str) -> "MarkDecorator":
    """Returns a mark that can be used to skip a test if a module is missing"""
    return pytest.mark.skipif(
        name not in sys.modules, reason=f"{name} is not installed"
    )


implementations = [
    pytest.param("local", LocalPath),
    pytest.param(
        "memory",
        upath.implementations.memory.MemoryPath,
    ),
    pytest.param(
        "s3",
        upath.implementations.cloud.S3Path,
        marks=[skip_if_module_missing("s3fs")],
    ),
    pytest.param(
        "azure",
        upath.implementations.cloud.AzurePath,
        marks=[skip_if_module_missing("adlfs")],
    ),
    pytest.param(
        "gcs",
        upath.implementations.cloud.GCSPath,
        marks=[skip_if_module_missing("gcsfs")],
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
