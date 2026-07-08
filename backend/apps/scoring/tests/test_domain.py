"""`battery_for` + `daraja_for` — the pure domain resolvers (BCKND-45)."""
import pytest

from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    ExerciseFactory,
    TestBatteryFactory,
)
from apps.scoring.domain.battery import battery_for
from apps.scoring.domain.daraja import daraja_for
from apps.scoring.tests.scenarios import seed_thresholds

pytestmark = pytest.mark.django_db


# --- battery_for -------------------------------------------------------------------

def test_battery_for_returns_exercises_in_order():
    cat = AgeCategoryFactory(age_min=14, age_max=14)
    battery = TestBatteryFactory(age_category=cat, gender="male")
    exercises = [ExerciseFactory() for _ in range(5)]
    for order, exercise in enumerate(exercises, start=1):
        BatteryItemFactory(battery=battery, exercise=exercise, order=order)
    assert battery_for(cat, "male") == exercises


def test_battery_for_differs_by_gender():
    # #5 is gender-specific: boys turnik, girls skameyka (SCORING §2 / §9).
    cat = AgeCategoryFactory(age_min=14, age_max=14)
    boys, girls = (
        TestBatteryFactory(age_category=cat, gender="male"),
        TestBatteryFactory(age_category=cat, gender="female"),
    )
    turnik, skameyka = ExerciseFactory(), ExerciseFactory()
    BatteryItemFactory(battery=boys, exercise=turnik, order=1)
    BatteryItemFactory(battery=girls, exercise=skameyka, order=1)
    assert battery_for(cat, "male") == [turnik]
    assert battery_for(cat, "female") == [skameyka]


def test_battery_for_none_when_undefined():
    cat = AgeCategoryFactory(age_min=7, age_max=8)
    assert battery_for(cat, "male") is None


def test_battery_for_ignores_inactive_battery():
    cat = AgeCategoryFactory(age_min=14, age_max=14)
    TestBatteryFactory(age_category=cat, gender="male", is_active=False)
    assert battery_for(cat, "male") is None


# --- daraja_for --------------------------------------------------------------------

def test_daraja_for_maps_every_level():
    seed_thresholds()
    assert daraja_for(50) == ("I", "green")
    assert daraja_for(48) == ("I", "green")
    assert daraja_for(46) == ("II", "yellow")
    assert daraja_for(42) == ("II", "yellow")
    assert daraja_for(38) == ("II", "yellow")
    assert daraja_for(36) == ("III", "red")
    assert daraja_for(30) == ("III", "red")


def test_daraja_for_below_all_thresholds_is_none():
    seed_thresholds()
    assert daraja_for(28) == ("none", "red")
    assert daraja_for(0) == ("none", "red")
