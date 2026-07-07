from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import AgeCategoryFactory, OrganizationFactory
from apps.common.models import Gender

pytestmark = pytest.mark.django_db

ATHLETES = "/api/v1/athletes/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _super_admin():
    return UserFactory(role="super_admin")


def test_filter_by_age_category():
    cat = AgeCategoryFactory(ordinal=4, age_min=13, age_max=15)
    year = date.today().year
    in_14 = AthleteFactory(birth_year=year - 14)
    in_15 = AthleteFactory(birth_year=year - 15)  # lower boundary, in
    AthleteFactory(birth_year=year - 12)  # age 12, out
    AthleteFactory(birth_year=year - 16)  # age 16, out

    resp = _client(_super_admin()).get(ATHLETES, {"age_category": cat.id})
    data = resp.json()
    assert data["count"] == 2
    assert {a["id"] for a in data["results"]} == {in_14.id, in_15.id}


def test_filter_by_gender():
    AthleteFactory(gender=Gender.MALE)
    AthleteFactory(gender=Gender.FEMALE)
    resp = _client(_super_admin()).get(ATHLETES, {"gender": "female"})
    assert resp.json()["count"] == 1


def test_filter_by_is_active():
    AthleteFactory(is_active=True)
    inactive = AthleteFactory(is_active=False)
    resp = _client(_super_admin()).get(ATHLETES, {"is_active": "false"})
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == inactive.id


def test_filter_by_coach():
    coach = UserFactory(role="coach", organization=OrganizationFactory())
    with_coach = AthleteFactory(coach=coach)
    AthleteFactory()
    resp = _client(_super_admin()).get(ATHLETES, {"coach": coach.id})
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["id"] == with_coach.id
