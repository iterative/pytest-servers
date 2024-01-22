class PytestServersException(Exception):  # noqa: N818
    """Base class for all pytest-servers exceptions."""

    def __init__(self, msg: str, *args):
        assert msg
        self.msg = msg
        super().__init__(msg, *args)


class RemoteUnavailable(PytestServersException):
    """Raise when the given remote is not available."""


class HealthcheckTimeout(PytestServersException):
    """Raise when the healthcheck probe for a container fails."""

    def __init__(self, container_name: str, container_logs: str):
        super().__init__(container_name)
        self.logs = container_logs

    def __str__(self):
        return f"Healthcheck timeout: Logs for {self.msg}:\n{self.logs}"
