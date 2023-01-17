def test_gcs_versioning(tmp_gcs_path, versioning):
    assert tmp_gcs_path.fs.version_aware


def test_gcs_versioning_disabled(tmp_gcs_path):
    assert not tmp_gcs_path.fs.version_aware


def test_s3_versioning(tmp_s3_path, versioning):
    assert tmp_s3_path.fs.version_aware


def test_s3_versioning_disabled(tmp_s3_path):
    assert not tmp_s3_path.fs.version_aware
