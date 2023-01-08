import json
import logging

import pytest
import requests
from filelock import FileLock

from .utils import get_free_port, wait_until, wait_until_running

logger = logging.getLogger(__name__)

GCS_DEFAULT_PORT = 4443


@pytest.fixture(scope="session")
def fake_gcs_creds(monkeypatch_session, tmp_path_factory):
    tmp_path = tmp_path_factory.getbasetemp() / "fake_gcs_creds.json"

    fake_creds = {
        "type": "service_account",
        "private_key_id": "dummy key id",
        "private_key": "dummy key",
        "client_email": "dummy@dummy.iam.gserviceaccount.com",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    with open(tmp_path, "w", encoding="utf-8") as fobj:
        json.dump(fake_creds, fobj)
    with monkeypatch_session.context() as m:
        m.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(tmp_path))
        yield tmp_path


@pytest.fixture(scope="session")
def fake_gcs_server(
    docker_client,
    tmp_path_factory,
    fake_gcs_creds,  # pylint: disable=redefined-outer-name,unused-argument
):
    """Spins up a fake-gcs-server container. Returns the endpoint URL."""
    from docker.errors import NotFound

    # Some features, such as signed URLs and resumable uploads, require
    # `fake-gcs-server` to know the actual url it will be accessed
    # with. We can provide that with -public-host and -external-url.
    port = get_free_port()

    container_name = "pytest-servers-fake-gcs-server"

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    fake_gcs_server_lock = root_tmp_dir / "fake_gcs_server.lock"

    with FileLock(fake_gcs_server_lock):
        try:
            port = docker_client.api.port(container_name, GCS_DEFAULT_PORT)[0][
                "HostPort"
            ]
            url = f"http://localhost:{port}"
            container = None
        except NotFound:
            url = f"http://localhost:{port}"
            command = (
                "-backend memory -scheme http "
                f"-public-host {url} -external-url {url} "
            )
            container = docker_client.containers.run(
                "fsouza/fake-gcs-server:1.42.2",  # renovate
                name=container_name,
                command=command,
                stdout=True,
                stderr=True,
                detach=True,
                remove=True,
                ports={f"{GCS_DEFAULT_PORT}/tcp": port},
            )
            wait_until_running(container)

    # make sure the container is healthy
    wait_until(lambda: requests.get(f"{url}/storage/v1/b", timeout=10).ok, 10)

    yield url
