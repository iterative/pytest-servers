import logging
import os
import random
import socket
import string
import time

import pytest

logger = logging.getLogger(__name__)


def wait_until(pred, timeout: float, pause: float = 0.1):
    start = time.perf_counter()
    while (time.perf_counter() - start) < timeout:
        value = pred()
        if value:
            return value
        time.sleep(pause)
    raise TimeoutError("timed out waiting")


def random_string(n: int = 6):
    return "".join(random.choices(string.ascii_lowercase, k=n))


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

    yield docker.from_env()


def is_pytest_session() -> bool:
    """returns true if currently running a pytest session"""
    return "PYTEST_CURRENT_TEST" in os.environ


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
