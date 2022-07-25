import re
import shlex
import subprocess

import pytest
import requests
from funcy import silent

from .utils import wait_until


class MockedS3Server:
    def __init__(self):
        self.port = None
        self.proc = None

    @property
    def endpoint_url(self):
        if self.port is None:
            raise ValueError("start() must be called first.")
        return f"http://localhost:{self.port}"

    def __enter__(self):
        self.start()
        return self

    def start(self):
        """Starts moto s3 on a random port"""
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
                "moto_server s3 -p 0",  # get a random port
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out = self.proc.stderr.readline()
        self.port = int(re.match(b".*http://127.0.0.1:(\\d+).*", out).group(1))
        wait_until(
            silent(lambda: requests.get(self.endpoint_url, timeout=5).ok), 5
        )

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
    s3_fake_creds_file,  # pylint: disable=unused-argument,redefined-outer-name
):
    """Spins up a moto s3 server. Returns the endpoint URL."""
    with MockedS3Server() as server:
        yield server.endpoint_url
