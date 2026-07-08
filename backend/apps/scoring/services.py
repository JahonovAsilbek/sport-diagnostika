from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.athletes.selectors import age_at
from apps.catalog.selectors import get_norm
from apps.scoring.domain.battery import battery_for
from apps.scoring.domain.daraja import daraja_for
from apps.scoring.domain.points import resolve_points
from apps.scoring.models import Evaluation, IndicatorScore


@transaction.atomic
def evaluate_session(session):
    """Score a session and write its `Evaluation` snapshot (SCORING.md §3–§5).

    For each battery exercise: look up the versioned `Norm` (pinned to `session.date`) and
    resolve the raw value to points. A missing norm makes the indicator ``unscored`` and
    blocks finalize (`ValidationError`, §7) — never silently scored 0. Σ points →
    `physical_total` → `(daraja, color)`.

    Idempotent: any prior Evaluation for the session is replaced, so re-finalize and the
    recompute task (BCKND-47) both refresh cleanly. Wrapped in one transaction — the caller
    (`finalize`) shares it so a failure here rolls the session status back to draft.
    """
    exercises = battery_for(session.age_category, session.gender)
    if exercises is None:
        raise ValidationError("Bu guruh uchun test batareyasi aniqlanmagan.")

    age = age_at(session.athlete.birth_year, session.date)
    measurements = {m.exercise_id: m for m in session.measurements.all()}

    unscored, scored = [], []
    for exercise in exercises:
        measurement = measurements.get(exercise.id)
        if measurement is None:
            raise ValidationError({"missing": [exercise.id]})
        norm = get_norm(exercise, session.gender, age, session.date)
        if norm is None:
            unscored.append(exercise.id)
            continue
        points = resolve_points(norm, measurement.raw_value)
        scored.append((exercise, measurement.raw_value, points))
    if unscored:
        raise ValidationError(
            {"unscored": unscored, "detail": "Ba'zi mashqlar uchun me'yor topilmadi."}
        )

    total = sum(points for _, _, points in scored)
    daraja, color = daraja_for(total)

    Evaluation.objects.filter(session=session).delete()
    evaluation = Evaluation.objects.create(
        session=session,
        athlete=session.athlete,
        age_category=session.age_category,
        gender=session.gender,
        region=session.region,
        sport_type=session.sport_type,
        session_date=session.date,
        physical_total=total,
        daraja=daraja,
        color=color,
        ranking_score=total,
        computed_at=timezone.now(),
    )
    IndicatorScore.objects.bulk_create([
        IndicatorScore(
            evaluation=evaluation, exercise=exercise, raw_value=raw_value, points=points
        )
        for exercise, raw_value, points in scored
    ])
    # Hooks land with their blocks: recommendation generation (B10), rating-cache
    # invalidation for this partition (B8). Left as no-ops here.
    return evaluation
