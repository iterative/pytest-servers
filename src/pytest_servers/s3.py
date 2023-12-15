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
def s3_server_config() -> dict:
    """Override to change default config of the moto server."""
    return {}


@pytest.fixture(scope="session")
def s3_server(  # type: ignore[misc]
    monkeypatch_session: pytest.MonkeyPatch,
    s3_server_config: dict,
) -> dict[str, str | None]:
    """Spins up a moto s3 server.

    Returns a client_kwargs dict that can be used with a boto client.
    """
    assert isinstance(s3_server_config, dict)
    monkeypatch_session.setenv("MOTO_ALLOW_NONEXISTENT_REGION", "true")

    with MockedS3Server(**s3_server_config) as server:
        yield {
            "endpoint_url": server.endpoint_url,
            "aws_access_key_id": "pytest-servers",
            "aws_secret_access_key": "pytest-servers",
            "aws_session_token": "pytest-servers",
            "region_name": "pytest-servers-region",
        }
