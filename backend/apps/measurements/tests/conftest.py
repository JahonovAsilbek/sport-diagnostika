import pytest


@pytest.fixture(autouse=True)
def _import_media_root(settings, tmp_path):
    """Keep uploaded import files out of the repo — each test writes to its own tmp dir."""
    settings.MEDIA_ROOT = str(tmp_path)
