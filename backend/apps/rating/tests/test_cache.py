"""Rating cache — hit, invalidation on Evaluation write, and per-scope key isolation (BCKND-51)."""

from types import SimpleNamespace

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.catalog.factories import AgeCategoryFactory, RegionFactory, SportTypeFactory
from apps.common.permissions import REGION_ADMIN
from apps.rating.cache import bump_generation, generation, scope_token
from apps.rating.tests.helpers import make_eval, make_partition, partition_query
from apps.scoring.models import Evaluation

pytestmark = pytest.mark.django_db

TOP = "/api/v1/rating/top/"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_bump_generation_advances_from_missing_key():
    assert generation() == 0
    bump_generation()
    assert generation() == 1
    bump_generation()
    assert generation() == 2


def test_response_is_served_from_cache():
    partition = make_partition()
    evaluation = make_eval(partition, 50)
    client = _client(UserFactory(role="super_admin"))
    first = client.get(TOP, partition_query(partition)).json()
    # Mutate via queryset.update() — bypasses post_save, so the cache is NOT invalidated.
    Evaluation.objects.filter(id=evaluation.id).update(ranking_score=10, physical_total=10)
    second = client.get(TOP, partition_query(partition)).json()
    assert second == first  # stale-but-cached proves the hit
    assert second["results"][0]["ranking_score"] == 50


def test_new_evaluation_invalidates_cache(django_capture_on_commit_callbacks):
    partition = make_partition()
    make_eval(partition, 40)
    client = _client(UserFactory(role="super_admin"))
    first = client.get(TOP, partition_query(partition)).json()
    assert first["results"][0]["ranking_score"] == 40
    # A new, higher-scoring athlete: the post_save → on_commit bump must bust the cache.
    with django_capture_on_commit_callbacks(execute=True):
        make_eval(partition, 50)
    second = client.get(TOP, partition_query(partition)).json()
    assert second["results"][0]["ranking_score"] == 50


def test_scope_token_isolates_region_admins():
    admin_a = SimpleNamespace(role=REGION_ADMIN, region_id=1, id=1)
    admin_b = SimpleNamespace(role=REGION_ADMIN, region_id=2, id=2)
    assert scope_token(admin_a) != scope_token(admin_b)


def test_scope_isolation_prevents_cross_region_leak():
    # Two region_admins hit /top/ with identical (empty) filters but must not share a cache
    # entry — otherwise region B's admin would see region A's cached ranking.
    region_a, region_b = RegionFactory(), RegionFactory()
    s, c = SportTypeFactory(), AgeCategoryFactory()
    make_eval({"region": region_a, "sport_type": s, "age_category": c, "gender": "male"}, 50)
    make_eval({"region": region_b, "sport_type": s, "age_category": c, "gender": "male"}, 42)
    a = _client(UserFactory(role="region_admin", region=region_a)).get(TOP).json()
    b = _client(UserFactory(role="region_admin", region=region_b)).get(TOP).json()
    assert a["results"][0]["ranking_score"] == 50
    assert b["results"][0]["ranking_score"] == 42  # not region A's cached 50
