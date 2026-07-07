"""Athlete scope enforcement — get_queryset filtering and create guards (BCKND-37).

Who sees which athletes, out-of-scope 404s, and the per-role create restrictions in
`_guard_scope`. Scope is enforced server-side, never trusting client filters.
"""
import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.athletes.models import Athlete
from apps.catalog.factories import OrganizationFactory, RegionFactory, SportTypeFactory

pytestmark = pytest.mark.django_db

ATHLETES = "/api/v1/athletes/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _payload(region, org, sport, **overrides):
    payload = {
        "last_name": "T", "first_name": "A", "birth_year": 2010, "gender": "male",
        "region": region.id, "organization": org.id, "sport_type": sport.id,
    }
    payload.update(overrides)
    return payload


# --- list scoping ------------------------------------------------------------------

def test_region_admin_sees_only_own_region():
    region_a, region_b = RegionFactory(), RegionFactory()
    AthleteFactory(region=region_a)
    AthleteFactory(region=region_a)
    AthleteFactory(region=region_b)
    admin = UserFactory(role="region_admin", region=region_a)
    data = _client(admin).get(ATHLETES).json()
    assert data["count"] == 2
    assert {a["region"] for a in data["results"]} == {region_a.id}


def test_lab_operator_sees_only_own_organization():
    region = RegionFactory()
    org_a, org_b = OrganizationFactory(region=region), OrganizationFactory(region=region)
    AthleteFactory(region=region, organization=org_a)
    AthleteFactory(region=region, organization=org_b)
    operator = UserFactory(role="lab_operator", organization=org_a)
    data = _client(operator).get(ATHLETES).json()
    assert data["count"] == 1
    assert {a["organization"] for a in data["results"]} == {org_a.id}


def test_coach_sees_only_own_athletes():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    AthleteFactory(region=region, organization=org, coach=coach)
    AthleteFactory(region=region, organization=org)  # no coach
    data = _client(coach).get(ATHLETES).json()
    assert data["count"] == 1
    assert data["results"][0]["coach"] == coach.id


def test_ministry_and_super_admin_see_all():
    AthleteFactory()
    AthleteFactory()
    for role in ("ministry", "super_admin"):
        data = _client(UserFactory(role=role)).get(ATHLETES).json()
        assert data["count"] == 2


# --- out-of-scope detail / sub-route → 404 -----------------------------------------

def test_coach_out_of_scope_detail_is_404():
    coach = UserFactory(role="coach", organization=OrganizationFactory())
    other = AthleteFactory()
    assert _client(coach).get(f"{ATHLETES}{other.id}/").status_code == 404


def test_region_admin_out_of_scope_detail_is_404():
    region_a, region_b = RegionFactory(), RegionFactory()
    admin = UserFactory(role="region_admin", region=region_a)
    other = AthleteFactory(region=region_b)
    assert _client(admin).get(f"{ATHLETES}{other.id}/").status_code == 404


def test_coach_out_of_scope_subroute_is_404():
    coach = UserFactory(role="coach", organization=OrganizationFactory())
    other = AthleteFactory()
    resp = _client(coach).get(f"{ATHLETES}{other.id}/latest-evaluation/")
    assert resp.status_code == 404


# --- create guards -----------------------------------------------------------------

def test_coach_create_forces_coach_self():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    other_coach = UserFactory(role="coach", organization=org)
    sport = SportTypeFactory()
    payload = _payload(region, org, sport, coach=other_coach.id)  # override attempt
    resp = _client(coach).post(ATHLETES, payload, format="json")
    assert resp.status_code == 201
    athlete = Athlete.objects.get(id=resp.json()["id"])
    assert athlete.coach_id == coach.id


def test_coach_create_foreign_org_is_403():
    region = RegionFactory()
    coach = UserFactory(role="coach", organization=OrganizationFactory(region=region))
    foreign_org = OrganizationFactory(region=region)
    sport = SportTypeFactory()
    resp = _client(coach).post(
        ATHLETES, _payload(region, foreign_org, sport), format="json"
    )
    assert resp.status_code == 403


def test_lab_operator_create_foreign_org_is_403():
    region = RegionFactory()
    operator = UserFactory(role="lab_operator", organization=OrganizationFactory(region=region))
    foreign_org = OrganizationFactory(region=region)
    sport = SportTypeFactory()
    resp = _client(operator).post(
        ATHLETES, _payload(region, foreign_org, sport), format="json"
    )
    assert resp.status_code == 403


def test_lab_operator_create_own_org_is_201():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    operator = UserFactory(role="lab_operator", organization=org)
    sport = SportTypeFactory()
    resp = _client(operator).post(ATHLETES, _payload(region, org, sport), format="json")
    assert resp.status_code == 201


def test_region_admin_create_foreign_region_is_403():
    region_a, region_b = RegionFactory(), RegionFactory()
    admin = UserFactory(role="region_admin", region=region_a)
    org_b = OrganizationFactory(region=region_b)
    sport = SportTypeFactory()
    resp = _client(admin).post(ATHLETES, _payload(region_b, org_b, sport), format="json")
    assert resp.status_code == 403


def test_region_admin_create_in_region_is_201():
    region_a = RegionFactory()
    admin = UserFactory(role="region_admin", region=region_a)
    org_a = OrganizationFactory(region=region_a)
    sport = SportTypeFactory()
    resp = _client(admin).post(ATHLETES, _payload(region_a, org_a, sport), format="json")
    assert resp.status_code == 201
