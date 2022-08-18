import logging
import time

import pytest
import requests

from .utils import get_free_port

logger = logging.getLogger(__name__)

GCS_DEFAULT_PORT = 4443


@pytest.fixture(scope="session")
def fake_gcs_server(docker_client):
    """Spins up a fake-gcs-server container. Returns the endpoint URL."""
    # Some features, such as signed URLs and resumable uploads, require
    # `fake-gcs-server` to know the actual url it will be accessed
    # with. We can provide that with -public-host and -external-url.
    port = get_free_port()
    url = f"http://localhost:{port}"
    command = f"-scheme http -public-host {url} -external-url {url}"

    container = docker_client.containers.run(
        "fsouza/fake-gcs-server:latest",
        command=command,
        name="pytest-servers-fake-gcs-server",
        stdout=True,
        stderr=True,
        detach=True,
        remove=True,
        ports={f"{GCS_DEFAULT_PORT}/tcp": port},
    )
    retries = 3
    while True:
        try:
            r = requests.get(f"{url}/storage/v1/b", timeout=10)
            if r.ok:
                break
        except Exception as exc:  # noqa: E722 # pylint: disable=broad-except
            retries -= 1
            if retries < 0:
                raise SystemError from exc
            time.sleep(1)

    yield url

    container.stop()
