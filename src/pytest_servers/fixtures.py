from typing import TYPE_CHECKING

import pytest
from upath import UPath

from .azure import azurite  # noqa: F401
from .factory import TempUPathFactory
from .gcs import fake_gcs_server  # noqa: F401
from .s3 import MockedS3Server, s3_server, s3_server_config  # noqa: F401
from .utils import docker_client, monkeypatch_session  # noqa: F401

if TYPE_CHECKING:
    from pytest import MonkeyPatch  # noqa: PT013


def _version_aware(request: pytest.FixtureRequest) -> bool:
    return "versioning" in request.fixturenames


@pytest.fixture
def versioning():  # noqa: ANN201
    """Enable versioning for supported remotes."""


@pytest.fixture(scope="session")
def tmp_upath_factory(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> TempUPathFactory:
    """Return a TempUPathFactory instance for the test session."""
    return TempUPathFactory.from_request(request, tmp_path_factory)


@pytest.fixture
def tmp_s3_path(
    tmp_upath_factory: TempUPathFactory,
    request: pytest.FixtureRequest,
) -> UPath:
    """Temporary path on a mocked S3 remote."""
    return tmp_upath_factory.mktemp("s3", version_aware=_version_aware(request))


@pytest.fixture
def tmp_local_path(
    tmp_upath_factory: TempUPathFactory,
    monkeypatch: "MonkeyPatch",
) -> UPath:
    """Return a temporary path."""
    ret = tmp_upath_factory.mktemp()
    monkeypatch.chdir(ret)
    return ret


@pytest.fixture
def tmp_azure_path(tmp_upath_factory: TempUPathFactory) -> UPath:
    """Return a temporary path."""
    return tmp_upath_factory.mktemp("azure")


@pytest.fixture
def tmp_memory_path(tmp_upath_factory: TempUPathFactory) -> UPath:
    """Return a temporary path in a MemoryFileSystem."""
    return tmp_upath_factory.mktemp("memory")


@pytest.fixture
def tmp_gcs_path(
    tmp_upath_factory: TempUPathFactory,
    request: pytest.FixtureRequest,
) -> UPath:
    """Return a temporary path."""
    return tmp_upath_factory.mktemp(
        "gcs",
        version_aware=_version_aware(request),
    )


@pytest.fixture
def tmp_upath(
    tmp_upath_factory: TempUPathFactory,
    request: pytest.FixtureRequest,
) -> UPath:
    """Temporary directory on different filesystems.

    Usage:
    >>> @pytest.mark.parametrize("tmp_upath", ["local", "s3", "azure"], indirect=True)
    >>> def test_something(tmp_upath):
    >>>     pass
    """
    param = getattr(request, "param", "local")
    version_aware = _version_aware(request)
    if version_aware and param not in ("gcs", "s3"):
        msg = f"Versioning is not supported for {param}"
        raise NotImplementedError(msg)
    if param == "local":
        return tmp_upath_factory.mktemp()
    if param == "memory":
        return tmp_upath_factory.mktemp("memory")
    if param == "s3":
        return tmp_upath_factory.mktemp("s3", version_aware=version_aware)
    if param == "azure":
        return tmp_upath_factory.mktemp("azure")
    if param == "gcs":
        return tmp_upath_factory.mktemp("gcs", version_aware=version_aware)
    if param == "gs":
        return tmp_upath_factory.mktemp("gs", version_aware=version_aware)
    msg = f"unknown {param=}"
    raise ValueError(msg)
