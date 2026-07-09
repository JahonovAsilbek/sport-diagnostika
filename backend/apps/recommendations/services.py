import logging
import operator

from django.db import transaction

from apps.recommendations.models import Recommendation, RecommendationRule

logger = logging.getLogger(__name__)

_OPS = {"lte": operator.le, "lt": operator.lt, "gte": operator.ge, "gt": operator.gt}


def _rule_fires(rule, total, points_by_exercise):
    """Whether `rule` matches — pure and unit-testable (SCORING.md §8).

    A total rule (`exercise` null) compares `physical_total`; an exercise rule compares that
    exercise's points. An exercise absent from this athlete's battery never fires (treating a
    missing exercise as 0 points would wrongly trip a `≤` rule)."""
    if rule.exercise_id is None:
        value = total
    elif rule.exercise_id not in points_by_exercise:
        return False
    else:
        value = points_by_exercise[rule.exercise_id]
    return _OPS[rule.comparator](value, rule.threshold)


@transaction.atomic
def generate_recommendations(evaluation):
    """(Re)generate the `Recommendation`s for an evaluation from the active rules. Idempotent —
    clears the evaluation's existing recs first, so re-finalize/recompute refresh cleanly."""
    Recommendation.objects.filter(evaluation=evaluation).delete()
    points_by_exercise = dict(evaluation.indicators.values_list("exercise_id", "points"))
    fired = [
        Recommendation(evaluation=evaluation, rule=rule, text=rule.template_text)
        for rule in RecommendationRule.objects.filter(is_active=True)
        if _rule_fires(rule, evaluation.physical_total, points_by_exercise)
    ]
    Recommendation.objects.bulk_create(fired)
    return fired


def generate_recommendations_for(evaluation_pk):
    """`on_commit` entry point (best-effort). Recommendations are advisory and regenerable, so a
    rule bug must never surface as a 500 on an already-committed finalize — log and move on."""
    from apps.scoring.models import Evaluation

    try:
        evaluation = Evaluation.objects.filter(pk=evaluation_pk).first()
        if evaluation is not None:
            generate_recommendations(evaluation)
    except Exception:
        logger.exception("recommendation generation failed for evaluation %s", evaluation_pk)
