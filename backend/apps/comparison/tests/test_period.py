"""Period filter on the comparison endpoint (BCKND-70) — the period can change the leader."""

from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.scoring.factories import EvaluationFactory

pytestmark = pytest.mark.django_db

URL = "/api/v1/comparison/"


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _eval(athlete, total, session_date):
    return EvaluationFactory(
        session__athlete=athlete,
        session__date=session_date,
        physical_total=total,
        ranking_score=total,
    )


def test_period_changes_leader():
    a1, a2 = AthleteFactory(), AthleteFactory()
    # Q1: a1 leads (40 > 30); Q2: a2 leads (50 > 20).
    _eval(a1, 40, date(2026, 2, 1))
    _eval(a2, 30, date(2026, 2, 1))
    _eval(a1, 20, date(2026, 5, 1))
    _eval(a2, 50, date(2026, 5, 1))
    client = _client(UserFactory(role="super_admin"))
    ids = {"athletes": f"{a1.id},{a2.id}"}

    q1 = client.get(
        URL, {**ids, "period_type": "quarter", "period_year": 2026, "period_index": 1}
    ).json()
    assert q1["leader"] == a1.id

    q2 = client.get(
        URL, {**ids, "period_type": "quarter", "period_year": 2026, "period_index": 2}
    ).json()
    assert q2["leader"] == a2.id
