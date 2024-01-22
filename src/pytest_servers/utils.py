import logging
import random
import socket
import string
import time
from typing import TYPE_CHECKING, Callable, NamedTuple, TypeVar

import pytest

if TYPE_CHECKING:
    from docker import DockerClient
    from docker.models.containers import Container


logger = logging.getLogger(__name__)

_T = TypeVar("_T")


def wait_until(pred: Callable[..., _T], timeout: float, pause: float = 0.1) -> _T:
    start = time.perf_counter()
    exc = None
    while (time.perf_counter() - start) < timeout:
        try:
            value = pred()
        except Exception as e:  # noqa: BLE001
            exc = e
        else:
            return value
        time.sleep(pause)

    msg = "timed out waiting"
    raise TimeoutError(msg) from exc


def random_string(n: int = 6) -> str:
    return "".join(
        random.choices(  # nosec B311 # noqa: S311
            string.ascii_lowercase,
            k=n,
        ),
    )


@pytest.fixture(scope="session")
def monkeypatch_session() -> pytest.MonkeyPatch:  # type: ignore[misc]
    """Session-scoped monkeypatch."""
    m = pytest.MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session")
def docker_client() -> "DockerClient":
    """Run docker commands using the python API."""
    import docker

    client = docker.from_env()

    yield client

    client.close()


def wait_until_running(
    container: "Container",
    timeout: int = 30,
    pause: float = 0.5,
) -> None:
    def check() -> bool:
        container.reload()
        return container.status == "running"

    wait_until(check, timeout=timeout, pause=pause)


def get_free_port() -> int:
    retries = 3
    while retries >= 0:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.listen()
                free_port = s.getsockname()[1]
        except OSError as exc:  # noqa: PERF203
            retries -= 1
            exception = exc
        else:
            return free_port

    msg = "Could not get a free port"
    raise SystemError(msg) from exception


class MockRemote(NamedTuple):
    fixture_name: str
    config_attribute_name: str
    requires_docker: bool
