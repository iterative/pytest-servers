import pytest


@pytest.fixture(scope="session")
def s3_server_config() -> dict:
    return {"ip_address": "0.0.0.0"}


def test_s3_endpoint_url_is_localhost_when_bound_to_wildcard(s3_server):
    assert s3_server["endpoint_url"].startswith("http://127.0.0.1:")
