import json
import os
from pathlib import Path


def test_s3_fake_creds_file(
    s3_fake_creds_file,  # pylint: disable=unused-argument
):
    assert os.getenv("AWS_PROFILE") is None
    assert os.getenv("AWS_ACCESS_KEY_ID") == "pytest-servers"
    assert os.getenv("AWS_SECRET_ACCESS_KEY") == "pytest-servers"
    assert os.getenv("AWS_SECURITY_TOKEN") == "pytest-servers"
    assert os.getenv("AWS_SESSION_TOKEN") == "pytest-servers"
    assert (Path("~").expanduser() / ".aws").exists()


def test_fake_gcs_creds(fake_gcs_creds):
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    with open(creds_path) as fobj:
        creds = json.load(fobj)

    assert creds["type"] == "service_account"
    assert creds["private_key_id"] == "dummy key id"
    assert creds["private_key"] == "dummy key"
    assert creds["client_email"] == "dummy@dummy.iam.gserviceaccount.com"
    assert creds["auth_uri"] == "https://accounts.google.com/o/oauth2/auth"
    assert creds["token_uri"] == "https://oauth2.googleapis.com/token"
