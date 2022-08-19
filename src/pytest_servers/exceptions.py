class PytestServersException(Exception):
    """Base class for all pytest-servers exceptions."""

    def __init__(self, msg: str, *args):
        assert msg
        self.msg = msg
        super().__init__(msg, *args)


class RemoteUnavailable(PytestServersException):
    """Raise when the given remote is not available"""
