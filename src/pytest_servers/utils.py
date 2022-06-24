import random
import string
import time

import pytest


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
