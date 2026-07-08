"""Shared scoring fixtures (helpers, not a test module — the `_`-free name is fine because
it holds no `test_` functions). Builds scorable sessions incl. the exact SCORING.md §9
worked example so several test modules reproduce it identically."""
from datetime import date
from decimal import Decimal

from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    DarajaThresholdFactory,
    ExerciseFactory,
    NormBandFactory,
    NormFactory,
    TestBatteryFactory,
)
from apps.measurements.factories import MeasurementFactory, TestSessionFactory

SESSION_DATE = date(2026, 6, 1)  # an athlete born 2012 is exactly 14 here


def seed_thresholds():
    """The locked physical daraja cut-offs (SCORING.md §5)."""
    DarajaThresholdFactory(level="I", total_min=48, total_max=50)
    DarajaThresholdFactory(level="II", total_min=38, total_max=46)
    DarajaThresholdFactory(level="III", total_min=30, total_max=36)


def make_session(gender="male", birth_year=2012, age_min=14, age_max=14):
    """A draft session whose snapshot dims mirror a fresh athlete, plus its (empty) battery."""
    cat = AgeCategoryFactory(age_min=age_min, age_max=age_max)
    athlete = AthleteFactory(birth_year=birth_year, gender=gender)
    session = TestSessionFactory(
        athlete=athlete,
        age_category=cat,
        gender=gender,
        region=athlete.region,
        organization=athlete.organization,
        sport_type=athlete.sport_type,
        date=SESSION_DATE,
    )
    battery = TestBatteryFactory(age_category=cat, gender=gender)
    return session, battery


def wire_exercise(session, battery, order, bands, raw):
    """Add one battery exercise + its norm/bands (for the athlete's age×gender) + the raw
    measurement. `bands` is a list of `(points, lower, upper)`. Returns the Exercise.

    The measurement's `raw_value` is stored directly (already parsed), so scoring reads it as
    is — the exercise `value_type` is irrelevant to `evaluate_session`."""
    age = SESSION_DATE.year - session.athlete.birth_year
    exercise = ExerciseFactory()
    BatteryItemFactory(battery=battery, exercise=exercise, order=order)
    norm = NormFactory(exercise=exercise, gender=session.gender, age_min=age, age_max=age)
    for points, lower, upper in bands:
        NormBandFactory(
            norm=norm, points=points,
            lower_bound=Decimal(lower), upper_bound=Decimal(upper),
        )
    MeasurementFactory(session=session, exercise=exercise, raw_value=Decimal(raw))
    return exercise


# SCORING.md §9 — 14-yosh oʻgʻil bola: (bands, raw) per battery exercise.
# 100m 14.4→8 · 400m 82s→8 · uzunlik 178→10 · egilish +9→8 · turnik 13→8  ⇒  total 42.
SECTION9 = [
    ([("10", "14.0", "14.3"), ("8", "14.3", "14.6"), ("6", "14.6", "14.9")], "14.4"),
    ([("10", "78", "82"), ("8", "82", "86"), ("6", "86", "90")], "82"),
    ([("6", "160", "170"), ("8", "170", "178"), ("10", "178", "190")], "178"),
    ([("6", "0", "5"), ("8", "5", "12"), ("10", "12", "20")], "9"),
    ([("6", "8", "11"), ("8", "11", "15"), ("10", "15", "25")], "13"),
]


def section9_session():
    """The full SCORING.md §9 boy scenario — five wired exercises → total 42 → II daraja."""
    seed_thresholds()
    session, battery = make_session()
    for order, (bands, raw) in enumerate(SECTION9, start=1):
        wire_exercise(session, battery, order, [(int(p), lo, hi) for p, lo, hi in bands], raw)
    return session
