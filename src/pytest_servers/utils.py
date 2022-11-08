import logging
import random
import socket
import string
import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from docker.models.containers import Container

logger = logging.getLogger(__name__)


def wait_until(pred, timeout: float, pause: float = 0.1):
    start = time.perf_counter()
    exc = None
    while (time.perf_counter() - start) < timeout:
        try:
            value = pred()
        except Exception as e:  # pylint: disable=broad-except
            exc = e
        else:
            if value:
                return value
        time.sleep(pause)

    raise TimeoutError("timed out waiting") from exc


def random_string(n: int = 6):
    return "".join(random.choices(string.ascii_lowercase, k=n))  # nosec B311


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch"""
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session")
def docker_client():
    """Run docker commands using the python API"""
    import docker

    client = docker.from_env()

    yield client

    client.close()


def wait_until_running(
    container: "Container", timeout: int = 30, pause: float = 0.5
):
    def check():
        container.reload()
        return container.status == "running"

    wait_until(check, timeout=timeout, pause=pause)


def get_free_port() -> None:
    retries = 3
    while retries >= 0:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.listen()
                free_port = s.getsockname()[1]
            return free_port
        except OSError as exc:
            retries -= 1
            if retries <= 0:
                raise SystemError("Could not get a free port") from exc
