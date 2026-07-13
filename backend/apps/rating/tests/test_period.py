"""Period filter on the rating endpoints (BCKND-70) — latest-per-athlete within the period,
and the period must be part of the cache key so periods never collide."""

from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.rating.tests.helpers import make_eval, make_partition, partition_query

pytestmark = pytest.mark.django_db

TOP = "/api/v1/rating/top/"

Q1 = {"period_type": "quarter", "period_year": 2026, "period_index": 1}
Q2 = {"period_type": "quarter", "period_year": 2026, "period_index": 2}


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def test_top_picks_latest_within_period_and_cache_varies():
    partition = make_partition()
    athlete = AthleteFactory()
    make_eval(partition, 30, athlete=athlete, session_date=date(2026, 2, 1))  # Q1
    make_eval(partition, 50, athlete=athlete, session_date=date(2026, 5, 1))  # Q2
    client = _client(UserFactory(role="super_admin"))

    q1 = client.get(TOP, {**partition_query(partition), **Q1})
    assert q1.json()["results"][0]["ranking_score"] == 30
    # A different period must NOT return Q1's cached value → the period is in the cache key.
    q2 = client.get(TOP, {**partition_query(partition), **Q2})
    assert q2.json()["results"][0]["ranking_score"] == 50
    # No period → latest overall (the Q2 evaluation).
    no_period = client.get(TOP, partition_query(partition))
    assert no_period.json()["results"][0]["ranking_score"] == 50


def test_out_of_range_period_is_empty():
    partition = make_partition()
    make_eval(partition, 40, athlete=AthleteFactory(), session_date=date(2026, 5, 1))  # Q2 only
    resp = _client(UserFactory(role="super_admin")).get(TOP, {**partition_query(partition), **Q1})
    assert resp.json()["results"] == []


def test_invalid_period_is_400():
    partition = make_partition()
    resp = _client(UserFactory(role="super_admin")).get(
        TOP, {**partition_query(partition), "period_type": "quarter"}  # no year
    )
    assert resp.status_code == 400
