# pylint: disable=redefined-outer-name

import pytest
from upath import UPath

from .local import LocalPath
from .s3 import MockedS3Server


@pytest.fixture
def aws_region_name():
    return "eu-west-1"


@pytest.fixture
def s3_server(monkeypatch):
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "foo")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "foo")
    with MockedS3Server() as server:
        yield server


@pytest.fixture
def s3path(s3_server, aws_region_name):
    path = UPath(
        "s3://test",
        client_kwargs={
            "endpoint_url": s3_server.endpoint_url,
            # NOTE: When not providing a region, moto returns 400
            "region_name": aws_region_name,
        },
    )
    path.mkdir()
    yield path


@pytest.fixture
def local_path(tmp_path_factory, monkeypatch):
    ret = LocalPath(tmp_path_factory.mktemp("pytest-servers"))
    monkeypatch.chdir(ret)
    yield ret


@pytest.fixture
def tmp_upath(request):
    param = getattr(request, "param", "local")
    if param == "local":
        return request.getfixturevalue("local_path")
    elif param == "s3":
        return request.getfixturevalue("s3path")
    raise ValueError(f"unknown {param=}")
