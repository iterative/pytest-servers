# pylint: disable=unused-import,redefined-outer-name
from typing import TYPE_CHECKING

import pytest

from .azure import azurite  # noqa: F401
from .factory import TempUPathFactory
from .s3 import MockedS3Server, s3_fake_creds_file, s3_server  # noqa: F401
from .utils import docker_client, monkeypatch_session  # noqa: F401

if TYPE_CHECKING:
    from pytest import FixtureRequest


@pytest.fixture
def aws_region_name():
    return "eu-west-1"


@pytest.fixture(scope="session")
def tmp_upath_factory(request: "FixtureRequest", s3_server, azurite):
    """Return a TempUPathFactory instance for the test session."""
    yield TempUPathFactory.from_config(
        request.config,
        s3_endpoint_url=s3_server.endpoint_url,
        azure_connection_string=azurite,
    )


@pytest.fixture
def s3path(tmp_upath_factory):
    """Temporary path on a mocked S3 remote."""
    yield tmp_upath_factory.mktemp("s3")


@pytest.fixture
def local_path(tmp_upath_factory, monkeypatch):
    """Return a temporary path."""
    ret = tmp_upath_factory.mktemp()
    monkeypatch.chdir(ret)
    yield ret


@pytest.fixture
def azure_path(tmp_upath_factory):
    """Return a temporary path."""
    yield tmp_upath_factory.mktemp("azure")


@pytest.fixture
def tmp_upath(
    request: "FixtureRequest",
    tmp_upath_factory,
):
    """Temporary directory on different filesystems.

    Usage:
    >>> @pytest.mark.parametrize("tmp_upath", ["local", "s3", "azure"], indirect=True]) # noqa: E501
    >>> def test_something(tmp_upath):
    >>>     pass
    """
    param = getattr(request, "param", "local")
    if param == "local":
        return tmp_upath_factory.mktemp()
    elif param == "s3":
        return tmp_upath_factory.mktemp("s3")
    elif param == "azure":
        return tmp_upath_factory.mktemp("azure")
    raise ValueError(f"unknown {param=}")


def pytest_addoption(parser):
    """Adds flags to configure mock remotes paths"""
    group = parser.getgroup("pytest-servers", "pytest-servers options")

    group.addoption(
        "--moto-port",
        help="Port for moto s3 server (defaults to %(default)s)",
        default=MockedS3Server.DEFAULT_PORT,
    )
