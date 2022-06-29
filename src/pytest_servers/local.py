import pathlib

from dvc_objects.fs.implementations.local import LocalFileSystem


class LocalPath(type(pathlib.Path())):  # type: ignore[misc]
    fs = LocalFileSystem()
