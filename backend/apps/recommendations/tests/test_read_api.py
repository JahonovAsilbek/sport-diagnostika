"""Read API for generated recommendations — GET /recommendations/ with scope + athlete filter."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import RegionFactory
from apps.recommendations.models import Recommendation
from apps.scoring.factories import EvaluationFactory

pytestmark = pytest.mark.django_db

RECS = "/api/v1/recommendations/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _rec(region, text="Test tavsiya"):
    athlete = AthleteFactory(region=region)
    evaluation = EvaluationFactory(session__athlete=athlete, session__region=region)
    return Recommendation.objects.create(evaluation=evaluation, text=text)


def test_requires_auth():
    assert _client().get(RECS).status_code == 401


def test_super_admin_sees_all():
    rec = _rec(RegionFactory())
    data = _client(UserFactory(role="super_admin")).get(RECS).json()
    assert data["count"] == 1
    assert data["results"][0]["text"] == rec.text


def test_region_admin_scoped():
    region_a, region_b = RegionFactory(), RegionFactory()
    _rec(region_a)
    _rec(region_b)
    admin = UserFactory(role="region_admin", region=region_a)
    assert _client(admin).get(RECS).json()["count"] == 1


def test_filter_by_athlete():
    region = RegionFactory()
    rec = _rec(region)
    _rec(region)
    athlete_id = rec.evaluation.athlete_id
    data = _client(UserFactory(role="super_admin")).get(RECS, {"athlete": athlete_id}).json()
    assert data["count"] == 1
