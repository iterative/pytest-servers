import pathlib

from dvc_objects.fs.implementations.local import LocalFileSystem


class LocalPath(type(pathlib.Path())):  # type: ignore[misc]
    def __init__(self, *args):
        super().__init__()
        if not getattr(self._accessor, "_fs", None):
            self._accessor._fs = LocalFileSystem()

    @property
    def fs(self):
        return self._accessor._fs
