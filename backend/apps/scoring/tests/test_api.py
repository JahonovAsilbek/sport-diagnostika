"""Scoring HTTP surface — the recompute endpoint auth/behavior and the populated athlete
evaluation sub-routes (BCKND-46/47/48). Postgres test DB; Celery runs eagerly in tests."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.measurements.models import TestSession
from apps.scoring.factories import EvaluationFactory
from apps.scoring.models import Evaluation
from apps.scoring.services import evaluate_session
from apps.scoring.tests.scenarios import section9_session

pytestmark = pytest.mark.django_db

RECOMPUTE = "/api/v1/evaluations/recompute/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _athlete_url(athlete_id, suffix):
    return f"/api/v1/athletes/{athlete_id}/{suffix}/"


# --- recompute auth ----------------------------------------------------------------


def test_recompute_unauthenticated_is_401():
    assert _client().post(RECOMPUTE).status_code == 401


def test_recompute_non_admin_is_403():
    for role in ("coach", "region_admin", "lab_operator", "ministry"):
        assert _client(UserFactory(role=role)).post(RECOMPUTE).status_code == 403


def test_recompute_super_admin_gets_202_with_task_id():
    resp = _client(UserFactory(role="super_admin")).post(RECOMPUTE, {}, format="json")
    assert resp.status_code == 202
    assert "task_id" in resp.json()


def test_recompute_ignores_unknown_filter_field():
    # The allowlist serializer drops unknown keys, so raw input can't reach .filter().
    resp = _client(UserFactory(role="super_admin")).post(
        RECOMPUTE, {"status": "draft"}, format="json"
    )
    assert resp.status_code == 202


# --- recompute behavior (eager) ----------------------------------------------------


def test_recompute_refreshes_a_stale_evaluation():
    session = section9_session()
    session.status = TestSession.Status.FINALIZED
    session.save()
    evaluate_session(session)  # the real score (42)
    Evaluation.objects.filter(session=session).update(
        physical_total=0, ranking_score=0, daraja="none", color="red"
    )
    resp = _client(UserFactory(role="super_admin")).post(RECOMPUTE, {}, format="json")
    assert resp.status_code == 202
    session.refresh_from_db()
    assert session.evaluation.physical_total == 42  # recomputed inline (eager)


# --- athlete sub-routes ------------------------------------------------------------


def test_athlete_evaluations_lists_snapshots():
    evaluation = EvaluationFactory()
    resp = _client(UserFactory(role="super_admin")).get(
        _athlete_url(evaluation.athlete_id, "evaluations")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["evaluation_id"] == evaluation.id
    assert data[0]["physical_total"] == 42


def test_athlete_latest_evaluation_returns_snapshot():
    evaluation = EvaluationFactory()
    resp = _client(UserFactory(role="super_admin")).get(
        _athlete_url(evaluation.athlete_id, "latest-evaluation")
    )
    assert resp.status_code == 200
    assert resp.json()["evaluation_id"] == evaluation.id


def test_athlete_latest_evaluation_is_204_when_none():
    athlete = AthleteFactory()
    resp = _client(UserFactory(role="super_admin")).get(
        _athlete_url(athlete.id, "latest-evaluation")
    )
    assert resp.status_code == 204
