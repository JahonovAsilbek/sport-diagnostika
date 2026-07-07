"""Root conftest for the backend test suite.

Its presence puts backend/ on sys.path so `config` and `apps` import cleanly, and it
holds shared fixtures.
"""
import pytest

from apps.accounts.factories import UserFactory


@pytest.fixture
def superuser(db):
    return UserFactory(is_staff=True, is_superuser=True)
