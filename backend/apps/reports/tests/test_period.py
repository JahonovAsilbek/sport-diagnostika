"""Period filter on reports (BCKND-70) — accepted in params, validated at request time, and
honored by the dataset builders."""

from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.reports.datasets import _athlete_dataset
from apps.scoring.factories import EvaluationFactory

pytestmark = pytest.mark.django_db

REPORTS = "/api/v1/reports/"


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_report_accepts_period_params():
    athlete = AthleteFactory()
    EvaluationFactory(session__athlete=athlete, session__date=date(2026, 5, 1))
    resp = _client(UserFactory(role="super_admin")).post(
        REPORTS,
        {
            "type": "athlete",
            "format": "excel",
            "params": {
                "athlete": athlete.id,
                "period_type": "quarter",
                "period_year": 2026,
                "period_index": 2,
            },
        },
        format="json",
    )
    assert resp.status_code == 202


def test_report_invalid_period_is_400():
    athlete = AthleteFactory()
    resp = _client(UserFactory(role="super_admin")).post(
        REPORTS,
        {
            "type": "athlete",
            "format": "excel",
            "params": {"athlete": athlete.id, "period_type": "quarter"},  # no year
        },
        format="json",
    )
    assert resp.status_code == 400


def test_athlete_dataset_honors_period():
    athlete = AthleteFactory()
    EvaluationFactory(session__athlete=athlete, session__date=date(2026, 2, 1), physical_total=30)
    EvaluationFactory(session__athlete=athlete, session__date=date(2026, 5, 1), physical_total=50)
    user = UserFactory(role="super_admin")

    q1 = _athlete_dataset(
        {"athlete": athlete.id, "period_type": "quarter", "period_year": 2026, "period_index": 1},
        user,
    )
    assert "30" in q1.subtitle  # "Umumiy ball: 30 — ..."
    q2 = _athlete_dataset(
        {"athlete": athlete.id, "period_type": "quarter", "period_year": 2026, "period_index": 2},
        user,
    )
    assert "50" in q2.subtitle
