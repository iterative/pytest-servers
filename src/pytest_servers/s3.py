import pytest


class MockedS3Server:
    def __init__(
        self,
        ip_address: str = "localhost",
        port: int = 0,
        verbose: bool = True,
    ):
        from moto.server import ThreadedMotoServer

        self._server = ThreadedMotoServer(
            ip_address, port=port, verbose=verbose
        )

    @property
    def endpoint_url(self):
        # pylint: disable-next=protected-access
        return f"http://{self._server._server.host}:{self.port}"

    @property
    def port(self):
        return self._server._server.port  # pylint: disable=protected-access

    def __enter__(self):
        self._server.start()
        return self

    def __exit__(self, *exc_args):
        self._server.stop()


@pytest.fixture(scope="session")
def s3_fake_creds_file(monkeypatch_session):
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
def s3_server_config():
    """Override to change default config of the server."""
    return {}


@pytest.fixture(scope="session")
def s3_server(
    s3_server_config,  # pylint: disable=redefined-outer-name
    s3_fake_creds_file,  # pylint: disable=unused-argument,redefined-outer-name
):
    """Spins up a moto s3 server. Returns the endpoint URL."""
    assert isinstance(s3_server_config, dict)
    with MockedS3Server(**s3_server_config) as server:
        yield server.endpoint_url
