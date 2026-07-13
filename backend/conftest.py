"""Root conftest for the backend test suite.

Its presence puts backend/ on sys.path so `config` and `apps` import cleanly, and it
holds shared fixtures.
"""

import pytest

from apps.accounts.factories import UserFactory


@pytest.fixture(autouse=True)
def _isolate_cache():
    """Give every test a clean cache. DRF throttling + the login lockout (BCKND-69) and the
    stats/rating caches all live in the cache; without this they leak counters across tests."""
    from django.core.cache import cache

    cache.clear()
    yield


@pytest.fixture
def superuser(db):
    return UserFactory(is_staff=True, is_superuser=True)
