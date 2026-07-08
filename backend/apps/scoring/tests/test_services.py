"""`evaluate_session` — the orchestration + the SCORING.md §9 worked example (BCKND-46/48)."""
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    ExerciseFactory,
    NormBandFactory,
    NormFactory,
)
from apps.measurements.factories import MeasurementFactory, TestSessionFactory
from apps.scoring.models import Evaluation, IndicatorScore
from apps.scoring.services import evaluate_session
from apps.scoring.tests.scenarios import (
    SESSION_DATE,
    make_session,
    section9_session,
    seed_thresholds,
    wire_exercise,
)

pytestmark = pytest.mark.django_db


def test_section9_14yo_boy_totals_42_second_daraja():
    """The exact SCORING.md §9 example: 8+8+10+8+8 = 42 → II daraja 🟡."""
    evaluation = evaluate_session(section9_session())
    assert evaluation.physical_total == 42
    assert evaluation.ranking_score == 42
    assert evaluation.daraja == "II"
    assert evaluation.color == "yellow"
    assert evaluation.indicators.count() == 5
    assert sorted(i.points for i in evaluation.indicators.all()) == [8, 8, 8, 8, 10]


def test_evaluation_snapshots_the_session_dims():
    session = section9_session()
    evaluation = evaluate_session(session)
    assert evaluation.session_id == session.id
    assert evaluation.athlete_id == session.athlete_id
    assert evaluation.age_category_id == session.age_category_id
    assert evaluation.region_id == session.region_id
    assert evaluation.sport_type_id == session.sport_type_id
    assert evaluation.session_date == session.date
    assert evaluation.gender == session.gender


def test_value_worse_than_worst_band_scores_zero():
    seed_thresholds()
    session, battery = make_session()
    wire_exercise(
        session, battery, 1,
        [(10, "14.0", "14.3"), (8, "14.3", "14.6"), (6, "14.6", "14.9")], "20",
    )  # 20 s — slower than the worst band → 0
    evaluation = evaluate_session(session)
    assert evaluation.physical_total == 0
    assert evaluation.daraja == "none"
    assert evaluation.color == "red"


def test_missing_norm_marks_unscored_and_writes_nothing():
    seed_thresholds()
    session, battery = make_session()
    exercise = ExerciseFactory()
    BatteryItemFactory(battery=battery, exercise=exercise, order=1)
    MeasurementFactory(session=session, exercise=exercise, raw_value=Decimal("10"))
    with pytest.raises(ValidationError) as err:
        evaluate_session(session)
    assert "unscored" in err.value.detail
    assert Evaluation.objects.count() == 0
    assert IndicatorScore.objects.count() == 0


def test_missing_measurement_raises():
    session, battery = make_session()
    exercise = ExerciseFactory()
    BatteryItemFactory(battery=battery, exercise=exercise, order=1)
    NormFactory(exercise=exercise, gender="male", age_min=14, age_max=14)
    with pytest.raises(ValidationError):
        evaluate_session(session)  # no Measurement for the battery exercise


def test_undefined_battery_raises():
    cat = AgeCategoryFactory(age_min=14, age_max=14)
    athlete = AthleteFactory(birth_year=2012)
    session = TestSessionFactory(
        athlete=athlete, age_category=cat, gender="male",
        region=athlete.region, organization=athlete.organization,
        sport_type=athlete.sport_type, date=SESSION_DATE,
    )
    with pytest.raises(ValidationError):
        evaluate_session(session)


def test_reevaluate_is_idempotent_and_replaces():
    session = section9_session()
    first = evaluate_session(session)
    second = evaluate_session(session)
    assert Evaluation.objects.filter(session=session).count() == 1
    assert IndicatorScore.objects.filter(evaluation__session=session).count() == 5
    assert second.physical_total == 42
    assert first.id != second.id  # prior Evaluation deleted + recreated


def test_adult_scored_via_18_29_norm_bucket():
    seed_thresholds()
    session, battery = make_session(birth_year=2006, age_min=18, age_max=29)  # age 20
    exercise = ExerciseFactory()
    BatteryItemFactory(battery=battery, exercise=exercise, order=1)
    norm = NormFactory(exercise=exercise, gender="male", age_min=18, age_max=29)
    NormBandFactory(norm=norm, points=10, lower_bound=Decimal("0"), upper_bound=Decimal("100"))
    MeasurementFactory(session=session, exercise=exercise, raw_value=Decimal("50"))
    assert evaluate_session(session).physical_total == 10


def test_female_session_uses_female_battery():
    seed_thresholds()
    session, battery = make_session(gender="female")
    wire_exercise(session, battery, 1, [(10, "0", "100")], "50")
    evaluation = evaluate_session(session)
    assert evaluation.gender == "female"
    assert evaluation.physical_total == 10
