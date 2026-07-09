import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_stats_cache():
    """The overview endpoint caches per scope token — clear between tests so one test's
    counts don't leak into the next."""
    cache.clear()
    yield
    cache.clear()
