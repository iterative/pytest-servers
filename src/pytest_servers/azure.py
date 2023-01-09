import logging

import pytest
import requests
from filelock import FileLock

from .utils import wait_until, wait_until_running

AZURITE_PORT = 10000
AZURITE_URL = "http://localhost:{port}"
AZURITE_ACCOUNT_NAME = "devstoreaccount1"
AZURITE_KEY = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="  # noqa: E501
AZURITE_ENDPOINT = f"{AZURITE_URL}/{AZURITE_ACCOUNT_NAME}"
AZURITE_CONNECTION_STRING = f"DefaultEndpointsProtocol=http;AccountName={AZURITE_ACCOUNT_NAME};AccountKey={AZURITE_KEY};BlobEndpoint={AZURITE_ENDPOINT};"  # noqa: E501

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def azurite(docker_client, tmp_path_factory):
    """Spins up an azurite container. Returns the connection string."""
    from docker.errors import NotFound

    container_name = "pytest-servers-azurite"

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    azurite_lock = root_tmp_dir / "azurite.lock"

    with FileLock(azurite_lock):
        try:
            port = docker_client.api.port(container_name, AZURITE_PORT)[0][
                "HostPort"
            ]
            container = None
        except NotFound:
            container = docker_client.containers.run(
                "mcr.microsoft.com/azure-storage/azurite:3.21.0",  # renovate
                command="azurite-blob --loose --blobHost 0.0.0.0",
                name=container_name,
                stdout=True,
                stderr=True,
                detach=True,
                remove=True,
                ports={f"{AZURITE_PORT}/tcp": None},  # assign a random port
            )
            port = docker_client.api.port(container_name, AZURITE_PORT)[0][
                "HostPort"
            ]
            wait_until_running(container)

    def is_healthy():
        r = requests.get(AZURITE_URL.format(port=port), timeout=3)
        return (
            r.status_code == 400
            and "Server" in r.headers
            and "Azurite" in r.headers["Server"]
        )

    wait_until(is_healthy, 10)

    yield AZURITE_CONNECTION_STRING.format(port=port)
