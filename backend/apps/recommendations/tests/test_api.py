"""Recommendation generation via the Evaluation signal + the rule CRUD / athlete endpoints."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import ExerciseFactory
from apps.measurements.factories import TestSessionFactory
from apps.recommendations.factories import RecommendationFactory, RecommendationRuleFactory
from apps.scoring.factories import EvaluationFactory

pytestmark = pytest.mark.django_db

RULES = "/api/v1/recommendation-rules/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _recs_url(athlete_id):
    return f"/api/v1/athletes/{athlete_id}/recommendations/"


# --- generation via the Evaluation post_save → on_commit signal ---------------------

def test_new_evaluation_generates_recommendations(django_capture_on_commit_callbacks):
    RecommendationRuleFactory(comparator="lt", threshold=30, template_text="Ko'proq mashq.")
    with django_capture_on_commit_callbacks(execute=True):
        evaluation = EvaluationFactory(physical_total=25, ranking_score=25)
    assert evaluation.recommendations.count() == 1
    assert evaluation.recommendations.get().text == "Ko'proq mashq."


def test_no_matching_rule_generates_nothing(django_capture_on_commit_callbacks):
    RecommendationRuleFactory(comparator="lt", threshold=30)
    with django_capture_on_commit_callbacks(execute=True):
        evaluation = EvaluationFactory(physical_total=45, ranking_score=45)
    assert evaluation.recommendations.count() == 0


# --- athlete recommendations sub-route ----------------------------------------------

def test_athlete_recommendations_lists_latest_eval_recs():
    athlete = AthleteFactory()
    evaluation = EvaluationFactory(session=TestSessionFactory(athlete=athlete))
    RecommendationFactory(evaluation=evaluation, text="Kuch mashqlari hajmini oshiring.")
    resp = _client(UserFactory(role="super_admin")).get(_recs_url(athlete.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["text"] == "Kuch mashqlari hajmini oshiring."


def test_athlete_without_evaluation_returns_empty_list():
    athlete = AthleteFactory()
    resp = _client(UserFactory(role="super_admin")).get(_recs_url(athlete.id))
    assert resp.status_code == 200
    assert resp.json() == []


# --- rule CRUD, gated to super_admin ------------------------------------------------

def test_super_admin_full_rule_crud():
    client = _client(UserFactory(role="super_admin"))
    created = client.post(
        RULES, {"comparator": "lt", "threshold": 30, "template_text": "x"}, format="json"
    )
    assert created.status_code == 201
    rule_id = created.json()["id"]
    assert client.get(RULES).status_code == 200
    assert client.patch(f"{RULES}{rule_id}/", {"threshold": 25}, format="json").status_code == 200
    assert client.delete(f"{RULES}{rule_id}/").status_code == 204


def test_rule_read_and_write_forbidden_for_non_super_admin():
    RecommendationRuleFactory()
    body = {"comparator": "lt", "threshold": 30, "template_text": "x"}
    for role in ("coach", "region_admin", "lab_operator", "ministry"):
        client = _client(UserFactory(role=role))
        assert client.get(RULES).status_code == 403
        assert client.post(RULES, body, format="json").status_code == 403


def test_unauthenticated_rule_access_is_401():
    assert _client().get(RULES).status_code == 401


# --- threshold validation -----------------------------------------------------------

def test_exercise_rule_threshold_over_10_is_400():
    exercise = ExerciseFactory()
    resp = _client(UserFactory(role="super_admin")).post(
        RULES,
        {"exercise": exercise.id, "comparator": "lte", "threshold": 15, "template_text": "x"},
        format="json",
    )
    assert resp.status_code == 400


def test_total_rule_threshold_over_50_is_400():
    resp = _client(UserFactory(role="super_admin")).post(
        RULES, {"comparator": "lt", "threshold": 60, "template_text": "x"}, format="json"
    )
    assert resp.status_code == 400
