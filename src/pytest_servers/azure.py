from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
import requests
from filelock import FileLock

from .exceptions import HealthcheckTimeout
from .utils import wait_until, wait_until_running

if TYPE_CHECKING:
    from docker import DockerClient
    from docker.models import Container

AZURITE_PORT = 10000
AZURITE_URL = "http://localhost:{port}"
AZURITE_ACCOUNT_NAME = "devstoreaccount1"
AZURITE_KEY = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="  # noqa: E501
AZURITE_ENDPOINT = f"{AZURITE_URL}/{AZURITE_ACCOUNT_NAME}"
AZURITE_CONNECTION_STRING = f"DefaultEndpointsProtocol=http;AccountName={AZURITE_ACCOUNT_NAME};AccountKey={AZURITE_KEY};BlobEndpoint={AZURITE_ENDPOINT};"  # noqa: E501

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def azurite(
    docker_client: DockerClient,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    """Spins up an azurite container. Returns the connection string."""
    from docker.errors import NotFound

    container_name = "pytest-servers-azurite"

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    azurite_lock = root_tmp_dir / "azurite.lock"

    with FileLock(azurite_lock):
        try:
            container: Container = docker_client.containers.get(container_name)
        except NotFound:
            container = docker_client.containers.run(
                "mcr.microsoft.com/azure-storage/azurite:3.32.0",  # renovate
                command="azurite-blob --loose --blobHost 0.0.0.0",
                name=container_name,
                stdout=True,
                stderr=True,
                detach=True,
                remove=True,
                ports={f"{AZURITE_PORT}/tcp": None},  # assign a random port
            )

        wait_until_running(container)
        port = container.ports.get(f"{AZURITE_PORT}/tcp")[0]["HostPort"]

    def is_healthy() -> bool:
        r = requests.get(AZURITE_URL.format(port=port), timeout=3)
        return (
            r.status_code == 400
            and "Server" in r.headers
            and "Azurite" in r.headers["Server"]
        )

    try:
        wait_until(
            is_healthy,
            timeout=30,
        )
    except TimeoutError:
        raise HealthcheckTimeout(
            container.name,
            container.logs().decode(),
        ) from None

    return AZURITE_CONNECTION_STRING.format(port=port)
