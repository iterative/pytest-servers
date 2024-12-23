import pathlib

from fsspec.implementations.local import LocalFileSystem


class LocalPath(type(pathlib.Path())):  # type: ignore[misc]
    fs = LocalFileSystem()

    @property
    def path(self) -> str:
        return str(self)
