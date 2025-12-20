import platform

import pytest


@pytest.fixture(autouse=True)
def _disable_adlfs_memoryview_optimization_on_pypy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if platform.python_implementation() != "PyPy":
        return

    # Remove this whole fixture when either:
    # - PyPy exposes an iterable `memoryview` compatible with Azure SDK request-body
    #   checks, or
    # - adlfs updates its own support check / stops using `memoryview` for uploads.
    #
    # This is intentionally a hard failure: it forces us to re-evaluate whether this
    # workaround is still needed.
    if hasattr(memoryview(b""), "__iter__"):
        pytest.fail(
            (
                "PyPy memoryview now appears iterable; the adlfs/Azure workaround in "
                "tests/conftest.py is likely obsolete and should be removed."
            ),
        )

    try:
        import adlfs.spec
    except Exception:  # noqa: BLE001
        return

    azure_blob_file = getattr(adlfs.spec, "AzureBlobFile", None)
    if azure_blob_file is None:
        return

    # If adlfs itself no longer claims memoryview support, then this workaround should
    # be unnecessary and must be removed.
    try:
        if not azure_blob_file._sdk_supports_memoryview_for_writes(None):  # noqa: SLF001
            pytest.fail(
                (
                    "adlfs no longer reports memoryview support for writes; the PyPy "
                    "workaround in tests/conftest.py should be removed."
                ),
            )
    except Exception:  # noqa: BLE001
        # If this API shape changes, we also want a visible signal rather than
        # silently masking.
        pytest.fail(
            "adlfs AzureBlobFile._sdk_supports_memoryview_for_writes API changed; "
            "re-evaluate/remove the PyPy workaround in tests/conftest.py.",
        )

    monkeypatch.setattr(
        azure_blob_file,
        "_sdk_supports_memoryview_for_writes",
        lambda *_args, **_kwargs: False,
        raising=False,
    )
