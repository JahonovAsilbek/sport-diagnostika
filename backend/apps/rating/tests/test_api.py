"""Rating API — endpoint shapes, filters, pagination, and per-role scoping (BCKND-50)."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.catalog.factories import AgeCategoryFactory, RegionFactory, SportTypeFactory
from apps.rating.tests.helpers import make_eval, make_partition, partition_query

pytestmark = pytest.mark.django_db

TOP = "/api/v1/rating/top/"
ATHLETES = "/api/v1/rating/athletes/"
REGIONS = "/api/v1/rating/regions/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def test_unauthenticated_is_401():
    assert _client().get(TOP).status_code == 401


def test_top_returns_ranked_results():
    partition = make_partition()
    make_eval(partition, 50)
    make_eval(partition, 42)
    resp = _client(UserFactory(role="super_admin")).get(TOP, partition_query(partition))
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert [row["rank"] for row in results] == [1, 2]
    assert results[0]["ranking_score"] == 50
    assert results[0]["athlete"]["full_name"]


def test_top_respects_limit():
    partition = make_partition()
    for score in range(1, 6):
        make_eval(partition, score)
    resp = _client(UserFactory(role="super_admin")).get(
        TOP, {**partition_query(partition), "limit": 3}
    )
    assert len(resp.json()["results"]) == 3


def test_athletes_is_paginated():
    partition = make_partition()
    for score in range(1, 4):
        make_eval(partition, score)
    resp = _client(UserFactory(role="super_admin")).get(ATHLETES, partition_query(partition))
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert data["results"][0]["rank"] == 1


def _partition(region, sport, category, gender="male"):
    return {"region": region, "sport_type": sport, "age_category": category, "gender": gender}


def test_region_admin_sees_only_own_region():
    sport, category = SportTypeFactory(), AgeCategoryFactory()
    region_a, region_b = RegionFactory(), RegionFactory()
    make_eval(_partition(region_a, sport, category), 50)
    make_eval(_partition(region_b, sport, category), 48)
    admin = UserFactory(role="region_admin", region=region_a)
    data = _client(admin).get(ATHLETES).json()  # no filter → scoped to region A
    assert data["count"] == 1
    assert data["results"][0]["ranking_score"] == 50


def test_regions_endpoint_returns_counts():
    sport, category = SportTypeFactory(), AgeCategoryFactory()
    region = RegionFactory()
    partition = {"region": region, "sport_type": sport, "age_category": category, "gender": "male"}
    make_eval(partition, 50, daraja="I", color="green")
    make_eval(partition, 30, daraja="III", color="red")
    resp = _client(UserFactory(role="super_admin")).get(
        REGIONS, {"sport_type": sport.id, "age_category": category.id}
    )
    assert resp.status_code == 200
    row = resp.json()["results"][0]
    assert row["region"] == region.name
    assert row["daraja_i_count"] == 1
    assert row["avg_score"] == 40.0  # (50 + 30) / 2


def test_invalid_filter_pk_is_400():
    resp = _client(UserFactory(role="super_admin")).get(TOP, {"region": 999999})
    assert resp.status_code == 400
