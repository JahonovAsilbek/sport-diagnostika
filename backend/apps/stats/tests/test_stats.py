"""Stats overview — scoping (region_admin isolation), by_daraja / by_organization_type, cache."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import OrganizationFactory, RegionFactory
from apps.measurements.factories import TestSessionFactory
from apps.scoring.factories import EvaluationFactory

pytestmark = pytest.mark.django_db

OVERVIEW = "/api/v1/stats/overview/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def test_unauthenticated_is_401():
    assert _client().get(OVERVIEW).status_code == 401


def test_region_admin_sees_only_own_region_counts():
    region_a, region_b = RegionFactory(), RegionFactory()
    AthleteFactory(region=region_a)
    AthleteFactory(region=region_a)
    AthleteFactory(region=region_b)
    admin = UserFactory(role="region_admin", region=region_a)
    data = _client(admin).get(OVERVIEW).json()
    assert data["athletes_total"] == 2
    assert data["regions"] == 1  # distinct regions in scope


def test_super_admin_sees_all_regions():
    AthleteFactory()
    data = _client(UserFactory(role="super_admin")).get(OVERVIEW).json()
    assert data["regions"] == RegionFactory._meta.model.objects.count()


def test_by_organization_type_split():
    region = RegionFactory()
    otm = OrganizationFactory(region=region, type="OTM")
    opsttm = OrganizationFactory(region=region, type="OPSTTM")
    AthleteFactory(region=region, organization=otm)
    AthleteFactory(region=region, organization=otm)
    AthleteFactory(region=region, organization=opsttm)
    data = _client(UserFactory(role="super_admin")).get(OVERVIEW).json()
    assert data["by_organization_type"] == {"OTM": 2, "OPSTTM": 1}


def test_by_daraja_counts_latest_per_athlete():
    EvaluationFactory(daraja="I")
    EvaluationFactory(daraja="II")
    EvaluationFactory(daraja="II")
    EvaluationFactory(daraja="none")
    data = _client(UserFactory(role="super_admin")).get(OVERVIEW).json()
    assert data["by_daraja"] == {"I": 1, "II": 2, "III": 0, "none": 1}


def test_recent_sessions_counts_scoped():
    TestSessionFactory()
    TestSessionFactory()
    data = _client(UserFactory(role="super_admin")).get(OVERVIEW).json()
    assert data["recent_sessions"] == 2
