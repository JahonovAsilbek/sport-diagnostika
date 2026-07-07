import pytest

from apps.catalog.factories import BatteryItemFactory, ExerciseFactory, TestBatteryFactory
from apps.catalog.models import Exercise
from apps.measurements.factories import MeasurementFactory, TestSessionFactory
from apps.measurements.selectors import (
    battery_exercise_ids,
    missing_exercises,
    resolve_battery,
)

pytestmark = pytest.mark.django_db


def _battery_session():
    """A session whose (age_category, gender) has an active 5-exercise battery."""
    session = TestSessionFactory()
    battery = TestBatteryFactory(age_category=session.age_category, gender=session.gender)
    exercises = [
        ExerciseFactory(value_type=Exercise.ValueType.SECONDS),
        ExerciseFactory(value_type=Exercise.ValueType.MINSEC),
        ExerciseFactory(value_type=Exercise.ValueType.COUNT),
        ExerciseFactory(value_type=Exercise.ValueType.CM_SIGNED),
        ExerciseFactory(value_type=Exercise.ValueType.COUNT),
    ]
    for order, exercise in enumerate(exercises, start=1):
        BatteryItemFactory(battery=battery, exercise=exercise, order=order)
    return session, battery, exercises


def test_resolve_battery_returns_matching_battery():
    session, battery, _ = _battery_session()
    assert resolve_battery(session) == battery


def test_resolve_battery_none_when_undefined():
    session = TestSessionFactory()
    assert resolve_battery(session) is None


def test_battery_exercise_ids_in_order():
    session, _, exercises = _battery_session()
    assert battery_exercise_ids(session) == [ex.id for ex in exercises]


def test_battery_exercise_ids_none_without_battery():
    session = TestSessionFactory()
    assert battery_exercise_ids(session) is None


def test_missing_exercises_none_without_battery():
    session = TestSessionFactory()
    assert missing_exercises(session) is None


def test_missing_exercises_full_list_when_empty():
    session, _, exercises = _battery_session()
    assert missing_exercises(session) == [ex.id for ex in exercises]


def test_missing_exercises_empty_when_complete():
    session, _, exercises = _battery_session()
    for exercise in exercises:
        MeasurementFactory(session=session, exercise=exercise)
    assert missing_exercises(session) == []


def test_missing_exercises_subset_when_partial():
    session, _, exercises = _battery_session()
    MeasurementFactory(session=session, exercise=exercises[0])
    MeasurementFactory(session=session, exercise=exercises[2])
    assert missing_exercises(session) == [exercises[1].id, exercises[3].id, exercises[4].id]
