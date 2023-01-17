import os
from pathlib import Path

from pytest_servers.fixtures import _version_aware


def test_s3_fake_creds_file(
    s3_fake_creds_file,  # pylint: disable=unused-argument
):
    assert os.getenv("AWS_PROFILE") is None
    assert os.getenv("AWS_ACCESS_KEY_ID") == "pytest-servers"
    assert os.getenv("AWS_SECRET_ACCESS_KEY") == "pytest-servers"
    assert os.getenv("AWS_SECURITY_TOKEN") == "pytest-servers"
    assert os.getenv("AWS_SESSION_TOKEN") == "pytest-servers"
    assert os.getenv("AWS_DEFAULT_REGION") == "us-east-1"
    assert (Path("~").expanduser() / ".aws").exists()


def test_version_aware(request):
    assert not _version_aware(request)
    request.getfixturevalue("versioning")
    assert _version_aware(request)
