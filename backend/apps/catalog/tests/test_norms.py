from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    DarajaThresholdFactory,
    ExerciseFactory,
    NormFactory,
    TestBatteryFactory,
)
from apps.catalog.models import DarajaThreshold
from apps.catalog.selectors import get_norm
from apps.common.models import Gender

pytestmark = pytest.mark.django_db

PAST = date(2020, 1, 1)


# --- get_norm ----------------------------------------------------------------------

def test_get_norm_exact_age_match():
    ex = ExerciseFactory()
    norm = NormFactory(exercise=ex, gender=Gender.MALE, age_min=14, age_max=14, valid_from=PAST)
    assert get_norm(ex, Gender.MALE, 14, date(2026, 6, 1)) == norm
    # No single-year norm for a neighbouring age → None.
    assert get_norm(ex, Gender.MALE, 15, date(2026, 6, 1)) is None
    # Wrong gender → None.
    assert get_norm(ex, Gender.FEMALE, 14, date(2026, 6, 1)) is None


def test_get_norm_adult_bucket_resolves_for_18_and_29():
    ex = ExerciseFactory()
    norm = NormFactory(exercise=ex, gender=Gender.FEMALE, age_min=18, age_max=29, valid_from=PAST)
    assert get_norm(ex, Gender.FEMALE, 18, date(2026, 6, 1)) == norm
    assert get_norm(ex, Gender.FEMALE, 29, date(2026, 6, 1)) == norm
    # Just outside the 18–29 bucket on either side.
    assert get_norm(ex, Gender.FEMALE, 17, date(2026, 6, 1)) is None
    assert get_norm(ex, Gender.FEMALE, 30, date(2026, 6, 1)) is None


def test_get_norm_version_selected_by_session_date():
    ex = ExerciseFactory()
    old = NormFactory(exercise=ex, age_min=14, age_max=14, valid_from=date(2025, 1, 1))
    new = NormFactory(exercise=ex, age_min=14, age_max=14, valid_from=date(2026, 1, 1))
    # Session before the new edition pins the older norm (reproducible history).
    assert get_norm(ex, Gender.MALE, 14, date(2025, 6, 1)) == old
    # Session on/after the new edition → the newest applicable version.
    assert get_norm(ex, Gender.MALE, 14, date(2026, 6, 1)) == new
    # Before any edition → None.
    assert get_norm(ex, Gender.MALE, 14, date(2024, 6, 1)) is None


def test_get_norm_ignores_inactive():
    ex = ExerciseFactory()
    NormFactory(exercise=ex, age_min=14, age_max=14, is_active=False, valid_from=PAST)
    assert get_norm(ex, Gender.MALE, 14, date(2026, 6, 1)) is None


# --- DarajaThreshold ---------------------------------------------------------------

def test_daraja_thresholds_ordered_by_total_desc():
    DarajaThresholdFactory(level="III", total_min=30, total_max=36)
    DarajaThresholdFactory(level="I", total_min=48, total_max=50)
    DarajaThresholdFactory(level="II", total_min=38, total_max=46)
    assert list(DarajaThreshold.objects.values_list("level", flat=True)) == ["I", "II", "III"]


def test_daraja_level_is_unique():
    DarajaThreshold.objects.create(level="I", total_min=48, total_max=50)
    with transaction.atomic(), pytest.raises(IntegrityError):
        DarajaThreshold.objects.create(level="I", total_min=40, total_max=45)


# --- check_physical_norms ----------------------------------------------------------
# NOTE: the seed_physical idempotency test is pending BCKND-32 (command not built yet).

def _battery_with(exercises, age_min=14, age_max=14, gender=Gender.MALE):
    cat = AgeCategoryFactory(age_min=age_min, age_max=age_max)
    battery = TestBatteryFactory(age_category=cat, gender=gender)
    for order, ex in enumerate(exercises, start=1):
        BatteryItemFactory(battery=battery, exercise=ex, order=order)
    return battery


def test_check_physical_norms_passes_when_all_norms_present():
    ex1, ex2 = ExerciseFactory(), ExerciseFactory()
    _battery_with([ex1, ex2])
    for ex in (ex1, ex2):
        NormFactory(exercise=ex, gender=Gender.MALE, age_min=14, age_max=14, valid_from=PAST)
    # Full coverage → command returns without raising (exit 0).
    call_command("check_physical_norms")


def test_check_physical_norms_fails_when_a_norm_is_missing():
    ex1, ex2 = ExerciseFactory(), ExerciseFactory()
    _battery_with([ex1, ex2])
    # Only ex1 has a norm; ex2 is a coverage gap.
    NormFactory(exercise=ex1, gender=Gender.MALE, age_min=14, age_max=14, valid_from=PAST)
    with pytest.raises(CommandError):
        call_command("check_physical_norms")


def test_check_physical_norms_requires_each_single_year():
    ex = ExerciseFactory()
    _battery_with([ex], age_min=13, age_max=15)
    # Norms for 13 and 14 but not 15 → still a gap (per-single-year coverage).
    NormFactory(exercise=ex, gender=Gender.MALE, age_min=13, age_max=13, valid_from=PAST)
    NormFactory(exercise=ex, gender=Gender.MALE, age_min=14, age_max=14, valid_from=PAST)
    with pytest.raises(CommandError):
        call_command("check_physical_norms")
