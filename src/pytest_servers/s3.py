import shlex
import subprocess

import requests
from funcy import silent

from .utils import wait_until


class MockedS3Server:
    def __init__(self, port: int = 5555):
        self.endpoint_url = f"http://127.0.0.1:{port}"
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
            shlex.split("moto_server s3 -p %s" % self.port)
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
