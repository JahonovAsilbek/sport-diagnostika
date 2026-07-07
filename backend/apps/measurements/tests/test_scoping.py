"""Test-session scope enforcement — get_queryset filtering, out-of-scope 404s, and the
create scope guard (B6). A session is scoped by its snapshot region/organization and the
athlete's coach; scope is server-side, never trusting client filters."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import AgeCategoryFactory, OrganizationFactory, RegionFactory
from apps.measurements.factories import TestSessionFactory

pytestmark = pytest.mark.django_db

SESSIONS = "/api/v1/sessions/"
SESSION_DATE = "2026-06-01"  # an athlete born 2012 is age 14 on this date


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


# --- list scoping ------------------------------------------------------------------

def test_region_admin_sees_only_own_region():
    region_a, region_b = RegionFactory(), RegionFactory()
    mine_1 = TestSessionFactory(athlete=AthleteFactory(region=region_a))
    mine_2 = TestSessionFactory(athlete=AthleteFactory(region=region_a))
    TestSessionFactory(athlete=AthleteFactory(region=region_b))
    admin = UserFactory(role="region_admin", region=region_a)
    data = _client(admin).get(SESSIONS).json()
    assert data["count"] == 2
    assert {row["id"] for row in data["results"]} == {mine_1.id, mine_2.id}


def test_lab_operator_sees_only_own_organization():
    region = RegionFactory()
    org_a, org_b = OrganizationFactory(region=region), OrganizationFactory(region=region)
    mine = TestSessionFactory(athlete=AthleteFactory(region=region, organization=org_a))
    TestSessionFactory(athlete=AthleteFactory(region=region, organization=org_b))
    operator = UserFactory(role="lab_operator", organization=org_a)
    data = _client(operator).get(SESSIONS).json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == mine.id


def test_coach_sees_only_own_athletes():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    mine = TestSessionFactory(
        athlete=AthleteFactory(region=region, organization=org, coach=coach)
    )
    TestSessionFactory(athlete=AthleteFactory(region=region, organization=org))
    data = _client(coach).get(SESSIONS).json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == mine.id


def test_ministry_and_super_admin_see_all():
    TestSessionFactory()
    TestSessionFactory()
    for role in ("ministry", "super_admin"):
        data = _client(UserFactory(role=role)).get(SESSIONS).json()
        assert data["count"] == 2


# --- out-of-scope detail → 404 -----------------------------------------------------

def test_coach_out_of_scope_detail_is_404():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    other = TestSessionFactory(
        athlete=AthleteFactory(
            region=region, organization=org, coach=UserFactory(role="coach")
        )
    )
    coach = UserFactory(role="coach", organization=org)
    assert _client(coach).get(f"{SESSIONS}{other.id}/").status_code == 404


def test_region_admin_out_of_scope_detail_is_404():
    region_a, region_b = RegionFactory(), RegionFactory()
    other = TestSessionFactory(athlete=AthleteFactory(region=region_b))
    admin = UserFactory(role="region_admin", region=region_a)
    assert _client(admin).get(f"{SESSIONS}{other.id}/").status_code == 404


# --- create scope guard ------------------------------------------------------------

def test_coach_create_for_foreign_athlete_is_403():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    other_coach = UserFactory(role="coach", organization=org)
    AgeCategoryFactory(age_min=14, age_max=14)
    athlete = AthleteFactory(
        coach=other_coach, organization=org, region=region, birth_year=2012
    )
    body = {"athlete": athlete.id, "date": SESSION_DATE}
    assert _client(coach).post(SESSIONS, body, format="json").status_code == 403


def test_coach_create_for_own_athlete_is_201():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    AgeCategoryFactory(age_min=14, age_max=14)
    athlete = AthleteFactory(
        coach=coach, organization=org, region=region, birth_year=2012
    )
    body = {"athlete": athlete.id, "date": SESSION_DATE}
    assert _client(coach).post(SESSIONS, body, format="json").status_code == 201
