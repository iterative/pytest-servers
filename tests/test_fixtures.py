def test_gcs_versioning(tmp_gcs_path, versioning):
    assert tmp_gcs_path.fs.version_aware


def test_gcs_versioning_disabled(tmp_gcs_path):
    assert not tmp_gcs_path.fs.version_aware


def test_s3_versioning(tmp_s3_path, versioning):
    assert tmp_s3_path.fs.version_aware


def test_s3_versioning_disabled(tmp_s3_path):
    assert not tmp_s3_path.fs.version_aware


def test_s3_server_default_config(s3_server):
    assert "endpoint_url" in s3_server
    assert s3_server["aws_access_key_id"] == "pytest-servers"
    assert s3_server["aws_secret_access_key"] == "pytest-servers"
    assert s3_server["aws_session_token"] == "pytest-servers"
    assert s3_server["region_name"] == "pytest-servers-region"
