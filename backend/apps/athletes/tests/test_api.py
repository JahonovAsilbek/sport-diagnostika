"""Athlete registry API — permissions, serializer contract, CRUD, sub-routes (BCKND-37)."""
from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.athletes.models import Athlete
from apps.catalog.factories import (
    AgeCategoryFactory,
    OrganizationFactory,
    RegionFactory,
    SportTypeFactory,
)
from apps.catalog.models import Organization

pytestmark = pytest.mark.django_db

ATHLETES = "/api/v1/athletes/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _create_payload():
    """A valid create body (super_admin) with fresh, consistent FKs. Returns the org too
    so callers can assert the derived `block`."""
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    sport = SportTypeFactory()
    payload = {
        "last_name": "T", "first_name": "A", "birth_year": 2010, "gender": "male",
        "region": region.id, "organization": org.id, "sport_type": sport.id,
    }
    return payload, org


# --- auth --------------------------------------------------------------------------

def test_unauthenticated_list_is_401():
    assert _client().get(ATHLETES).status_code == 401


def test_unauthenticated_create_is_401():
    payload, _ = _create_payload()
    assert _client().post(ATHLETES, payload, format="json").status_code == 401


# --- read --------------------------------------------------------------------------

def test_super_admin_list_returns_created_athletes():
    AthleteFactory()
    AthleteFactory()
    resp = _client(UserFactory(role="super_admin")).get(ATHLETES)
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


def test_retrieve_exposes_full_name_block_and_age_category():
    athlete = AthleteFactory()  # organization defaults to OTM
    age = date.today().year - athlete.birth_year
    cat = AgeCategoryFactory(ordinal=1, age_min=age, age_max=age)
    resp = _client(UserFactory(role="super_admin")).get(f"{ATHLETES}{athlete.id}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == athlete.full_name
    assert data["block"] == Organization.Type.OTM
    assert data["age_category"]["id"] == cat.id
    assert data["age_category"]["age_min"] == age


def test_retrieve_age_category_null_when_out_of_range():
    athlete = AthleteFactory(birth_year=1900)  # age far outside every TOIFA
    AgeCategoryFactory(ordinal=1, age_min=10, age_max=12)
    resp = _client(UserFactory(role="super_admin")).get(f"{ATHLETES}{athlete.id}/")
    assert resp.status_code == 200
    assert resp.json()["age_category"] is None


# --- write -------------------------------------------------------------------------

def test_super_admin_create_is_201():
    payload, org = _create_payload()
    before = Athlete.objects.count()
    resp = _client(UserFactory(role="super_admin")).post(ATHLETES, payload, format="json")
    assert resp.status_code == 201
    assert Athlete.objects.count() == before + 1
    assert resp.json()["block"] == org.type


def test_create_missing_region_is_400():
    payload, _ = _create_payload()
    del payload["region"]
    resp = _client(UserFactory(role="super_admin")).post(ATHLETES, payload, format="json")
    assert resp.status_code == 400


def test_ministry_write_is_403():
    payload, _ = _create_payload()
    resp = _client(UserFactory(role="ministry")).post(ATHLETES, payload, format="json")
    assert resp.status_code == 403


def test_super_admin_patch_updates_field():
    athlete = AthleteFactory()
    resp = _client(UserFactory(role="super_admin")).patch(
        f"{ATHLETES}{athlete.id}/", {"razryad": "KMS"}, format="json"
    )
    assert resp.status_code == 200
    athlete.refresh_from_db()
    assert athlete.razryad == "KMS"


def test_super_admin_delete_is_soft():
    athlete = AthleteFactory()
    resp = _client(UserFactory(role="super_admin")).delete(f"{ATHLETES}{athlete.id}/")
    assert resp.status_code == 204
    athlete.refresh_from_db()
    assert athlete.is_active is False
    assert Athlete.objects.filter(id=athlete.id).exists()


# --- sub-route stubs ---------------------------------------------------------------

def test_subroutes_return_stub_bodies():
    athlete = AthleteFactory()
    client = _client(UserFactory(role="super_admin"))
    base = f"{ATHLETES}{athlete.id}/"

    sessions = client.get(f"{base}sessions/")
    assert sessions.status_code == 200 and sessions.json() == []

    evaluations = client.get(f"{base}evaluations/")
    assert evaluations.status_code == 200 and evaluations.json() == []

    assert client.get(f"{base}latest-evaluation/").status_code == 204

    recommendations = client.get(f"{base}recommendations/")
    assert recommendations.status_code == 200 and recommendations.json() == []
