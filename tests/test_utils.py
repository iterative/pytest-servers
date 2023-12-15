from pytest_servers.fixtures import _version_aware


def test_version_aware(request):
    assert not _version_aware(request)
    request.getfixturevalue("versioning")
    assert _version_aware(request)
