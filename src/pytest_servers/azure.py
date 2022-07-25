import logging
import time

import pytest
import requests

AZURITE_PORT = 10000
AZURITE_URL = "http://localhost:{port}"
AZURITE_ACCOUNT_NAME = "devstoreaccount1"
AZURITE_KEY = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="  # noqa: E501
AZURITE_ENDPOINT = f"{AZURITE_URL}/{AZURITE_ACCOUNT_NAME}"
AZURITE_CONNECTION_STRING = f"DefaultEndpointsProtocol=http;AccountName={AZURITE_ACCOUNT_NAME};AccountKey={AZURITE_KEY};BlobEndpoint={AZURITE_ENDPOINT};"  # noqa: E501

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def azurite(docker_client):
    """Spins up an azurite container. Returns the connection string."""
    if docker_client is None:
        logger.warning(
            "Azurite cannot be started because docker is not available."
        )
        yield None
        return

    container = docker_client.containers.run(
        "mcr.microsoft.com/azure-storage/azurite",
        command="azurite-blob --loose --blobHost 0.0.0.0",
        name="pytest-servers-azurite",
        stdout=True,
        stderr=True,
        detach=True,
        remove=True,
        ports={f"{AZURITE_PORT}/tcp": None},  # assign a random port
    )

    port = docker_client.api.port("pytest-servers-azurite", AZURITE_PORT)[0][
        "HostPort"
    ]
    retries = 3
    while True:
        try:
            # wait until the container is up, even a 400 status code is ok
            r = requests.get(AZURITE_URL.format(port=port), timeout=10)
            if (
                r.status_code == 400
                and "Server" in r.headers
                and "Azurite" in r.headers["Server"]
            ):
                break
        except Exception as exc:  # noqa: E722 # pylint: disable=broad-except
            retries -= 1
            if retries < 0:
                raise SystemError from exc
            time.sleep(1)

    yield AZURITE_CONNECTION_STRING.format(port=port)

    container.stop()
