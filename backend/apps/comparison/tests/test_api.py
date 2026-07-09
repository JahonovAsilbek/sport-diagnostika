"""Comparison endpoint — 2–3 athletes side by side, leader, scoping, count validation (B9)."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import OrganizationFactory, RegionFactory
from apps.measurements.factories import TestSessionFactory
from apps.scoring.factories import EvaluationFactory, IndicatorScoreFactory

pytestmark = pytest.mark.django_db

URL = "/api/v1/comparison/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _evaluate(athlete, total, *, points=(10, 8), daraja="I", color="green"):
    """Give an athlete a latest Evaluation with `total` and some indicator points."""
    evaluation = EvaluationFactory(
        session=TestSessionFactory(athlete=athlete),
        physical_total=total, ranking_score=total, daraja=daraja, color=color,
    )
    for value in points:
        IndicatorScoreFactory(evaluation=evaluation, points=value)
    return evaluation


def _ids(*athletes):
    return {"athletes": ",".join(str(a.id) for a in athletes)}


# --- auth ---------------------------------------------------------------------------

def test_unauthenticated_is_401():
    assert _client().get(URL).status_code == 401


# --- happy paths --------------------------------------------------------------------

def test_two_athletes_side_by_side_with_leader():
    a1, a2 = AthleteFactory(), AthleteFactory()
    _evaluate(a1, 48)
    _evaluate(a2, 42)
    resp = _client(UserFactory(role="super_admin")).get(URL, _ids(a1, a2))
    assert resp.status_code == 200
    data = resp.json()
    assert [row["id"] for row in data["athletes"]] == [a1.id, a2.id]  # request order
    assert data["athletes"][0]["physical_total"] == 48
    assert len(data["athletes"][0]["indicators"]) == 2
    assert data["leader"] == a1.id  # highest physical_total


def test_three_athletes_leader_is_highest_total():
    a1, a2, a3 = AthleteFactory(), AthleteFactory(), AthleteFactory()
    _evaluate(a1, 30)
    _evaluate(a2, 50)
    _evaluate(a3, 40)
    data = _client(UserFactory(role="super_admin")).get(URL, _ids(a1, a2, a3)).json()
    assert len(data["athletes"]) == 3
    assert data["leader"] == a2.id


def test_athlete_without_evaluation_is_no_data():
    a1, a2 = AthleteFactory(), AthleteFactory()
    _evaluate(a1, 44)
    resp = _client(UserFactory(role="super_admin")).get(URL, _ids(a1, a2))
    data = resp.json()
    no_data = data["athletes"][1]
    assert no_data["id"] == a2.id
    assert no_data["physical_total"] is None
    assert no_data["daraja"] is None
    assert no_data["indicators"] == []
    assert data["leader"] == a1.id  # the no-data athlete never leads


def test_leader_is_null_when_nobody_has_an_evaluation():
    a1, a2 = AthleteFactory(), AthleteFactory()
    data = _client(UserFactory(role="super_admin")).get(URL, _ids(a1, a2)).json()
    assert data["leader"] is None


# --- count validation ---------------------------------------------------------------

def test_one_athlete_is_400():
    a1 = AthleteFactory()
    assert _client(UserFactory(role="super_admin")).get(URL, _ids(a1)).status_code == 400


def test_four_athletes_is_400():
    athletes = [AthleteFactory() for _ in range(4)]
    assert _client(UserFactory(role="super_admin")).get(URL, _ids(*athletes)).status_code == 400


def test_non_integer_ids_is_400():
    resp = _client(UserFactory(role="super_admin")).get(URL, {"athletes": "1,abc"})
    assert resp.status_code == 400


# --- scoping ------------------------------------------------------------------------

def test_out_of_scope_athlete_is_403():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    mine = AthleteFactory(coach=coach, organization=org, region=region)
    theirs = AthleteFactory(coach=UserFactory(role="coach"), organization=org, region=region)
    resp = _client(coach).get(URL, _ids(mine, theirs))
    assert resp.status_code == 403


def test_coach_compares_own_athletes():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach = UserFactory(role="coach", organization=org)
    a1 = AthleteFactory(coach=coach, organization=org, region=region)
    a2 = AthleteFactory(coach=coach, organization=org, region=region)
    _evaluate(a1, 40)
    _evaluate(a2, 46)
    resp = _client(coach).get(URL, _ids(a1, a2))
    assert resp.status_code == 200
    assert resp.json()["leader"] == a2.id


def test_nonexistent_athlete_is_403():
    a1 = AthleteFactory()
    resp = _client(UserFactory(role="super_admin")).get(URL, {"athletes": f"{a1.id},999999"})
    assert resp.status_code == 403
