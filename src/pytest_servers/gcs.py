from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
import requests
from filelock import FileLock

from .exceptions import HealthcheckTimeout
from .utils import get_free_port, wait_until, wait_until_running

if TYPE_CHECKING:
    from docker import DockerClient
    from docker.models import Container


logger = logging.getLogger(__name__)

GCS_DEFAULT_PORT = 4443


@pytest.fixture(scope="session")
def fake_gcs_server(
    docker_client: DockerClient,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    """Spins up a fake-gcs-server container. Returns the endpoint URL."""
    from docker.errors import NotFound

    container_name = "pytest-servers-fake-gcs-server"

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    fake_gcs_server_lock = root_tmp_dir / "fake_gcs_server.lock"

    with FileLock(fake_gcs_server_lock):
        container: Container
        try:
            container = docker_client.containers.get(container_name)
            port = container.ports.get(f"{GCS_DEFAULT_PORT}/tcp")[0]["HostPort"]
            url = f"http://localhost:{port}"
        except NotFound:
            # Some features, such as signed URLs and resumable uploads, require
            # `fake-gcs-server` to know the actual url it will be accessed
            # with. We can provide that with -public-host and -external-url.
            port = get_free_port()
            url = f"http://localhost:{port}"
            command = (
                "-backend memory -scheme http "
                f"-public-host {url} -external-url {url} "
            )
            container = docker_client.containers.run(
                "fsouza/fake-gcs-server:1.49.3",  # renovate
                name=container_name,
                command=command,
                stdout=True,
                stderr=True,
                detach=True,
                remove=True,
                ports={f"{GCS_DEFAULT_PORT}/tcp": port},
            )

        wait_until_running(container)

    try:
        wait_until(
            lambda: requests.get(f"{url}/storage/v1/b", timeout=10).ok,
            timeout=30,
        )
    except TimeoutError:
        raise HealthcheckTimeout(
            container.name,
            container.logs().decode(),
        ) from None

    return url
