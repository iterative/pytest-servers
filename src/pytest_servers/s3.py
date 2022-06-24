import shlex
import subprocess
from typing import Optional

import pytest
import requests
from funcy import silent

from .utils import wait_until


class MockedS3Server:
    DEFAULT_PORT = 5555

    def __init__(self, port: Optional[int] = None):
        self.endpoint_url = f"http://127.0.0.1:{port or self.DEFAULT_PORT}"
        self.port = port
        self.proc = None

    def __enter__(self):
        try:
            # should fail since we didn't start server yet
            r = requests.get(self.endpoint_url)
        except:  # noqa: E722, B001 # pylint: disable=bare-except
            pass
        else:
            if r.ok:
                raise RuntimeError("moto server already up")
        self.proc = subprocess.Popen(
            shlex.split(
                f"moto_server s3 -p {self.port}",
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        wait_until(silent(lambda: requests.get(self.endpoint_url).ok), 5)

        return self

    def close(self):
        if self.proc is not None:
            self.proc.terminate()
            self.proc.wait()
        self.proc = None

    def __exit__(self, *exc_args):
        self.close()


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
            yield
    finally:
        if aws_creds.exists() and not initially_exists:
            aws_creds.unlink()


@pytest.fixture(scope="session")
def s3_server(
    request,
    s3_fake_creds_file,  # pylint: disable=unused-argument,redefined-outer-name
):
    """Spins up a moto s3 server."""
    pytest.importorskip("s3fs")
    with MockedS3Server(request.config.getoption("--moto-port")) as server:
        yield server
