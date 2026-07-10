"""Read API for evaluations — GET /evaluations/ with scope + filters (BCKND read surface for F6)."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import OrganizationFactory, RegionFactory
from apps.scoring.factories import EvaluationFactory

pytestmark = pytest.mark.django_db

EVALS = "/api/v1/evaluations/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _eval(region, org=None, coach=None):
    # organization is NOT nullable — let the factory default it when not given.
    kwargs = {"region": region, "coach": coach}
    if org is not None:
        kwargs["organization"] = org
    athlete = AthleteFactory(**kwargs)
    return EvaluationFactory(
        session__athlete=athlete,
        session__region=region,
        session__organization=athlete.organization,
    )


def test_requires_auth():
    assert _client().get(EVALS).status_code == 401


def test_super_admin_sees_all_and_shape():
    region = RegionFactory()
    ev = _eval(region)
    data = _client(UserFactory(role="super_admin")).get(EVALS).json()
    assert data["count"] == 1
    row = data["results"][0]
    assert row["evaluation_id"] == ev.id
    assert row["physical_total"] == ev.physical_total
    assert "indicators" in row


def test_region_admin_scoped():
    region_a, region_b = RegionFactory(), RegionFactory()
    _eval(region_a)
    _eval(region_b)
    admin = UserFactory(role="region_admin", region=region_a)
    data = _client(admin).get(EVALS).json()
    assert data["count"] == 1
    assert data["results"][0]["region"] == region_a.id


def test_coach_scoped():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    _eval(region, org=org, coach=coach)
    _eval(region, org=org)  # different (no) coach
    data = _client(coach).get(EVALS).json()
    assert data["count"] == 1


def test_filter_by_athlete():
    region = RegionFactory()
    ev = _eval(region)
    _eval(region)
    data = _client(UserFactory(role="super_admin")).get(EVALS, {"athlete": ev.athlete_id}).json()
    assert data["count"] == 1
    assert data["results"][0]["athlete"] == ev.athlete_id
