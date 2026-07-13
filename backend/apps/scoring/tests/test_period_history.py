"""Period filter on the evaluation-history read endpoint (BCKND-70) — the period filters the
list to a session_date range."""

from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.scoring.factories import EvaluationFactory

pytestmark = pytest.mark.django_db

EVALS = "/api/v1/evaluations/"


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _eval(athlete, session_date):
    return EvaluationFactory(session__athlete=athlete, session__date=session_date)


def test_history_filtered_by_period():
    athlete = AthleteFactory()
    _eval(athlete, date(2026, 2, 1))  # Q1
    _eval(athlete, date(2026, 5, 1))  # Q2
    _eval(athlete, date(2026, 8, 1))  # Q3
    client = _client(UserFactory(role="super_admin"))

    assert client.get(EVALS, {"athlete": athlete.id}).json()["count"] == 3

    q2 = client.get(
        EVALS,
        {"athlete": athlete.id, "period_type": "quarter", "period_year": 2026, "period_index": 2},
    ).json()
    assert q2["count"] == 1
    assert q2["results"][0]["session_date"] == "2026-05-01"

    half1 = client.get(
        EVALS,
        {"athlete": athlete.id, "period_type": "half", "period_year": 2026, "period_index": 1},
    ).json()
    assert half1["count"] == 2  # Q1 + Q2


def test_invalid_period_is_400():
    resp = _client(UserFactory(role="super_admin")).get(EVALS, {"period_type": "half"})  # no year
    assert resp.status_code == 400
