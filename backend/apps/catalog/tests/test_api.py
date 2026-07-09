import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    DistrictFactory,
    ExerciseFactory,
    OrganizationFactory,
    RegionFactory,
    TestBatteryFactory,
)
from apps.catalog.models import Organization, SportType
from apps.common.models import Gender

pytestmark = pytest.mark.django_db

REGIONS = "/api/v1/catalog/regions/"
SPORT_TYPES = "/api/v1/catalog/sport-types/"
DISTRICTS = "/api/v1/catalog/districts/"
ORGANIZATIONS = "/api/v1/catalog/organizations/"
EXERCISES = "/api/v1/catalog/exercises/"
BATTERIES = "/api/v1/catalog/batteries/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


# --- read: any authenticated user, no special role ---------------------------------


def test_coach_can_read_reference_list():
    RegionFactory()
    resp = _client(UserFactory(role="coach")).get(REGIONS)
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


def test_ministry_can_read_reference_list():
    ExerciseFactory()
    resp = _client(UserFactory(role="ministry")).get(EXERCISES)
    assert resp.status_code == 200


def test_unauthenticated_read_is_401():
    resp = _client().get(REGIONS)
    assert resp.status_code == 401


# --- write: super_admin only -------------------------------------------------------


def test_super_admin_can_write():
    resp = _client(UserFactory(role="super_admin")).post(
        SPORT_TYPES, {"name": "Yangi sport", "code": "NEW"}, format="json"
    )
    assert resp.status_code == 201
    assert SportType.objects.filter(code="NEW").exists()


def test_coach_write_is_403():
    resp = _client(UserFactory(role="coach")).post(
        SPORT_TYPES, {"name": "X", "code": "XX"}, format="json"
    )
    assert resp.status_code == 403
    assert not SportType.objects.filter(code="XX").exists()


def test_region_admin_write_is_403():
    admin = UserFactory(role="region_admin", region=RegionFactory())
    resp = _client(admin).post(SPORT_TYPES, {"name": "X", "code": "XX"}, format="json")
    assert resp.status_code == 403


# --- filters -----------------------------------------------------------------------


def test_districts_filtered_by_region():
    r1, r2 = RegionFactory(), RegionFactory()
    DistrictFactory(region=r1)
    DistrictFactory(region=r1)
    DistrictFactory(region=r2)
    resp = _client(UserFactory(role="super_admin")).get(DISTRICTS, {"region": r1.id})
    data = resp.json()
    assert data["count"] == 2
    assert {d["region"] for d in data["results"]} == {r1.id}


def test_organizations_filtered_by_type_and_region():
    r1, r2 = RegionFactory(), RegionFactory()
    OrganizationFactory(region=r1, type=Organization.Type.OTM)
    OrganizationFactory(region=r1, type=Organization.Type.OPSTTM)
    OrganizationFactory(region=r2, type=Organization.Type.OPSTTM)
    resp = _client(UserFactory(role="ministry")).get(
        ORGANIZATIONS, {"type": "OPSTTM", "region": r1.id}
    )
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["type"] == "OPSTTM"
    assert results[0]["region"] == r1.id


def test_exercises_filtered_by_is_active():
    ExerciseFactory(is_active=True)
    ExerciseFactory(is_active=False)
    resp = _client(UserFactory(role="coach")).get(EXERCISES, {"is_active": "true"})
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["is_active"] is True


def test_batteries_filtered_by_age_category_and_gender_return_ordered_items():
    cat = AgeCategoryFactory()
    battery = TestBatteryFactory(age_category=cat, gender=Gender.MALE)
    ex1, ex2, ex3 = ExerciseFactory(), ExerciseFactory(), ExerciseFactory()
    # Insert out of order to prove the response is ordered by `order`.
    BatteryItemFactory(battery=battery, exercise=ex3, order=3)
    BatteryItemFactory(battery=battery, exercise=ex1, order=1)
    BatteryItemFactory(battery=battery, exercise=ex2, order=2)
    # A different (gender/category) battery that the filter must exclude.
    TestBatteryFactory(gender=Gender.FEMALE)

    resp = _client(UserFactory(role="coach")).get(
        BATTERIES, {"age_category": cat.id, "gender": "male"}
    )
    results = resp.json()["results"]
    assert len(results) == 1
    items = results[0]["items"]
    assert [i["order"] for i in items] == [1, 2, 3]
    assert [i["exercise"]["id"] for i in items] == [ex1.id, ex2.id, ex3.id]
    assert items[0]["exercise"]["value_type"] == "seconds"
