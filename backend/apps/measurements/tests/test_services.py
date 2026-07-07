import datetime
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    ExerciseFactory,
    TestBatteryFactory,
)
from apps.catalog.models import Exercise
from apps.measurements.factories import TestSessionFactory
from apps.measurements.models import TestSession
from apps.measurements.services import (
    finalize_session,
    open_session,
    parse_raw_value,
    save_measurements,
)

pytestmark = pytest.mark.django_db

VT = Exercise.ValueType


def _battery_session():
    """A session whose (age_category, gender) has an active 5-exercise battery."""
    session = TestSessionFactory()
    battery = TestBatteryFactory(age_category=session.age_category, gender=session.gender)
    exercises = [
        ExerciseFactory(value_type=VT.SECONDS),
        ExerciseFactory(value_type=VT.MINSEC),
        ExerciseFactory(value_type=VT.COUNT),
        ExerciseFactory(value_type=VT.CM_SIGNED),
        ExerciseFactory(value_type=VT.COUNT),
    ]
    for order, exercise in enumerate(exercises, start=1):
        BatteryItemFactory(battery=battery, exercise=exercise, order=order)
    return session, exercises


def _full_items(exercises):
    return [
        {"exercise": exercises[0], "raw_value": "14.4"},
        {"exercise": exercises[1], "raw_value": "1:22"},
        {"exercise": exercises[2], "raw_value": "9"},
        {"exercise": exercises[3], "raw_value": "-3"},
        {"exercise": exercises[4], "raw_value": "12"},
    ]


# --- parse_raw_value ---------------------------------------------------------


def test_parse_minsec_colon_form():
    assert parse_raw_value(VT.MINSEC, "1:22") == Decimal("82.00")


def test_parse_minsec_numeric_seconds():
    assert parse_raw_value(VT.MINSEC, "82") == Decimal("82.00")


def test_parse_minsec_non_positive_raises():
    with pytest.raises(ValidationError):
        parse_raw_value(VT.MINSEC, "0:00")


def test_parse_minsec_malformed_raises():
    with pytest.raises(ValidationError):
        parse_raw_value(VT.MINSEC, "abc")


def test_parse_seconds():
    assert parse_raw_value(VT.SECONDS, "14.4") == Decimal("14.40")


def test_parse_seconds_non_positive_raises():
    with pytest.raises(ValidationError):
        parse_raw_value(VT.SECONDS, "0")


def test_parse_count_integer():
    assert parse_raw_value(VT.COUNT, "9") == Decimal("9.00")


def test_parse_count_non_integer_raises():
    with pytest.raises(ValidationError):
        parse_raw_value(VT.COUNT, "9.5")


def test_parse_count_negative_raises():
    with pytest.raises(ValidationError):
        parse_raw_value(VT.COUNT, "-1")


def test_parse_cm_signed_positive():
    assert parse_raw_value(VT.CM_SIGNED, "9") == Decimal("9.00")


def test_parse_cm_signed_negative_is_valid():
    assert parse_raw_value(VT.CM_SIGNED, "-3") == Decimal("-3.00")


def test_parse_garbage_raises():
    with pytest.raises(ValidationError):
        parse_raw_value(VT.SECONDS, "abc")


# --- open_session ------------------------------------------------------------


def test_open_session_snapshots_athlete_dims():
    category = AgeCategoryFactory(age_min=14, age_max=14)
    on_date = datetime.date(2026, 6, 1)
    athlete = AthleteFactory(birth_year=on_date.year - 14)
    operator = UserFactory()

    session = open_session(athlete=athlete, entered_by=operator, date=on_date)

    assert session.is_draft is True
    assert session.status == TestSession.Status.DRAFT
    assert session.age_category == category
    assert session.gender == athlete.gender
    assert session.region == athlete.region
    assert session.organization == athlete.organization
    assert session.sport_type == athlete.sport_type
    assert session.entered_by == operator
    assert session.date == on_date


def test_open_session_defaults_date_to_today():
    category = AgeCategoryFactory(age_min=14, age_max=14)
    athlete = AthleteFactory(birth_year=timezone.localdate().year - 14)

    session = open_session(athlete=athlete, entered_by=UserFactory())

    assert session.date == timezone.localdate()
    assert session.age_category == category


def test_open_session_age_out_of_range_raises():
    AgeCategoryFactory(age_min=10, age_max=12)
    on_date = datetime.date(2026, 6, 1)
    athlete = AthleteFactory(birth_year=on_date.year - 5)

    with pytest.raises(ValidationError) as exc:
        open_session(athlete=athlete, entered_by=UserFactory(), date=on_date)
    assert "athlete" in exc.value.detail


# --- save_measurements -------------------------------------------------------


def test_save_measurements_stores_parsed_values():
    session, exercises = _battery_session()

    save_measurements(session, _full_items(exercises))

    assert session.measurements.count() == 5
    assert session.measurements.get(exercise=exercises[1]).raw_value == Decimal("82.00")
    assert session.measurements.get(exercise=exercises[3]).raw_value == Decimal("-3.00")


def test_save_measurements_rejects_exercise_outside_battery():
    session, _ = _battery_session()
    outsider = ExerciseFactory(value_type=VT.COUNT)

    with pytest.raises(ValidationError) as exc:
        save_measurements(session, [{"exercise": outsider, "raw_value": "3"}])
    assert "measurements" in exc.value.detail


def test_save_measurements_requires_battery():
    session = TestSessionFactory()
    exercise = ExerciseFactory(value_type=VT.COUNT)

    with pytest.raises(ValidationError):
        save_measurements(session, [{"exercise": exercise, "raw_value": "9"}])


def test_save_measurements_is_idempotent_per_exercise():
    session, exercises = _battery_session()
    exercise = exercises[2]

    save_measurements(session, [{"exercise": exercise, "raw_value": "9"}])
    save_measurements(session, [{"exercise": exercise, "raw_value": "12"}])

    assert session.measurements.filter(exercise=exercise).count() == 1
    assert session.measurements.get(exercise=exercise).raw_value == Decimal("12.00")


# --- finalize_session --------------------------------------------------------


def test_finalize_session_completes_battery():
    session, exercises = _battery_session()
    save_measurements(session, _full_items(exercises))

    result = finalize_session(session)

    assert result.status == TestSession.Status.FINALIZED
    session.refresh_from_db()
    assert session.status == TestSession.Status.FINALIZED


def test_finalize_session_incomplete_raises_with_missing():
    session, exercises = _battery_session()
    save_measurements(session, [{"exercise": exercises[0], "raw_value": "14.4"}])

    with pytest.raises(ValidationError) as exc:
        finalize_session(session)
    assert "missing" in exc.value.detail


def test_finalize_session_already_finalized_raises():
    session, _ = _battery_session()
    session.status = TestSession.Status.FINALIZED
    session.save(update_fields=["status"])

    with pytest.raises(ValidationError):
        finalize_session(session)
