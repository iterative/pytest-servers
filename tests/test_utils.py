import os
from pathlib import Path


def test_s3_fake_creds_file(s3_fake_creds_file):
    assert os.getenv("AWS_PROFILE") is None
    assert os.getenv("AWS_ACCESS_KEY_ID") == "pytest-servers"
    assert os.getenv("AWS_SECRET_ACCESS_KEY") == "pytest-servers"
    assert os.getenv("AWS_SECURITY_TOKEN") == "pytest-servers"
    assert os.getenv("AWS_SESSION_TOKEN") == "pytest-servers"
    assert (Path("~").expanduser() / ".aws").exists()
