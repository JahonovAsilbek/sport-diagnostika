"""Rule matching (pure) + `generate_recommendations` (DB) — BCKND-56/57."""
from types import SimpleNamespace

import pytest

from apps.catalog.factories import ExerciseFactory
from apps.recommendations.factories import RecommendationRuleFactory
from apps.recommendations.models import Recommendation
from apps.recommendations.services import _rule_fires, generate_recommendations
from apps.scoring.factories import EvaluationFactory, IndicatorScoreFactory


def _rule(comparator, threshold, exercise_id=None):
    return SimpleNamespace(exercise_id=exercise_id, comparator=comparator, threshold=threshold)


# --- _rule_fires (pure, no DB) ------------------------------------------------------

def test_total_rule_below_threshold_fires():
    assert _rule_fires(_rule("lt", 30), 28, {}) is True


def test_total_rule_at_threshold_does_not_fire_for_strict_lt():
    assert _rule_fires(_rule("lt", 30), 30, {}) is False


def test_exercise_rule_at_threshold_fires_for_lte():
    # SCORING §8: "turnikda tortilish points ≤ 6" — the boundary value fires.
    assert _rule_fires(_rule("lte", 6, exercise_id=7), 42, {7: 6}) is True


def test_exercise_rule_above_threshold_does_not_fire():
    assert _rule_fires(_rule("lte", 6, exercise_id=7), 42, {7: 8}) is False


def test_exercise_absent_from_battery_never_fires():
    assert _rule_fires(_rule("lte", 6, exercise_id=7), 42, {9: 4}) is False


def test_gte_and_gt_comparators():
    assert _rule_fires(_rule("gte", 48, exercise_id=1), 0, {1: 48}) is True
    assert _rule_fires(_rule("gt", 48, exercise_id=1), 0, {1: 48}) is False


# --- generate_recommendations (DB) --------------------------------------------------

@pytest.mark.django_db
def test_total_rule_fires_and_snapshots_text():
    RecommendationRuleFactory(comparator="lt", threshold=30, template_text="Ko'proq mashq.")
    evaluation = EvaluationFactory(physical_total=25, ranking_score=25)
    fired = generate_recommendations(evaluation)
    assert len(fired) == 1
    assert evaluation.recommendations.get().text == "Ko'proq mashq."


@pytest.mark.django_db
def test_total_rule_not_met_creates_nothing():
    RecommendationRuleFactory(comparator="lt", threshold=30)
    evaluation = EvaluationFactory(physical_total=40, ranking_score=40)
    assert generate_recommendations(evaluation) == []
    assert evaluation.recommendations.count() == 0


@pytest.mark.django_db
def test_exercise_rule_fires_on_matching_indicator():
    exercise = ExerciseFactory()
    RecommendationRuleFactory(
        exercise=exercise, comparator="lte", threshold=6, template_text="Kuch."
    )
    evaluation = EvaluationFactory(physical_total=42, ranking_score=42)
    IndicatorScoreFactory(evaluation=evaluation, exercise=exercise, points=6)
    fired = generate_recommendations(evaluation)
    assert len(fired) == 1
    assert fired[0].text == "Kuch."


@pytest.mark.django_db
def test_inactive_rule_is_ignored():
    RecommendationRuleFactory(comparator="lt", threshold=30, is_active=False)
    evaluation = EvaluationFactory(physical_total=10, ranking_score=10)
    assert generate_recommendations(evaluation) == []


@pytest.mark.django_db
def test_regeneration_is_idempotent():
    RecommendationRuleFactory(comparator="lt", threshold=30)
    evaluation = EvaluationFactory(physical_total=20, ranking_score=20)
    generate_recommendations(evaluation)
    generate_recommendations(evaluation)  # re-run clears + recreates
    assert Recommendation.objects.filter(evaluation=evaluation).count() == 1
