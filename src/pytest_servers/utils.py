import time


def wait_until(pred, timeout: float, pause: float = 0.1):
    start = time.perf_counter()
    while (time.perf_counter() - start) < timeout:
        value = pred()
        if value:
            return value
        time.sleep(pause)
    raise TimeoutError("timed out waiting")
