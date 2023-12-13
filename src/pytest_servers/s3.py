from __future__ import annotations

import pytest


class MockedS3Server:
    def __init__(
        self,
        ip_address: str = "127.0.0.1",
        port: int = 0,
        *,
        verbose: bool = True,
    ):
        from moto.server import ThreadedMotoServer

        self._server = ThreadedMotoServer(ip_address, port=port, verbose=verbose)

    @property
    def endpoint_url(self) -> str:
        return f"http://{self.ip_address}:{self.port}"

    @property
    def port(self) -> int:
        # grab the port from the _server attribute, which has the bound port
        assert self._server._server  # noqa: SLF001
        return self._server._server.port  # noqa: SLF001

    @property
    def ip_address(self) -> str:
        return self._server._ip_address  # noqa: SLF001

    def __enter__(self):
        self._server.start()
        return self

    def __exit__(self, *exc_args):
        self._server.stop()


@pytest.fixture(scope="session")
def s3_fake_creds_file(monkeypatch_session: pytest.MonkeyPatch) -> None:  # type: ignore[misc]
    # https://github.com/spulec/moto#other-caveats
    import pathlib

    aws_dir = pathlib.Path("~").expanduser() / ".aws"
    aws_dir.mkdir(exist_ok=True)

    aws_creds = aws_dir / "credentials"
    initially_exists = aws_creds.exists()

    if not initially_exists:
        aws_creds.touch()

    try:
        with monkeypatch_session.context() as m:
            try:
                m.delenv("AWS_PROFILE")
            except KeyError:
                pass
            m.setenv("AWS_ACCESS_KEY_ID", "pytest-servers")
            m.setenv("AWS_SECRET_ACCESS_KEY", "pytest-servers")
            m.setenv("AWS_SECURITY_TOKEN", "pytest-servers")
            m.setenv("AWS_SESSION_TOKEN", "pytest-servers")
            m.setenv("AWS_DEFAULT_REGION", "us-east-1")
            yield
    finally:
        if aws_creds.exists() and not initially_exists:
            aws_creds.unlink()


@pytest.fixture(scope="session")
def s3_server_config() -> dict:
    """Override to change default config of the server."""
    return {}


@pytest.fixture(scope="session")
def s3_server(  # type: ignore[misc]
    s3_server_config: dict,
    s3_fake_creds_file: None,  # noqa: ARG001
) -> str:
    """Spins up a moto s3 server. Returns the endpoint URL."""
    assert isinstance(s3_server_config, dict)
    with MockedS3Server(**s3_server_config) as server:
        yield server.endpoint_url
