import pytest
from django.core.management import call_command

from apps.catalog.models import (
    BatteryItem,
    DarajaThreshold,
    Norm,
    NormBand,
    TestBattery,
)


def _seed_all():
    call_command("seed_catalog")
    call_command("seed_exercises")
    call_command("seed_physical")


@pytest.mark.django_db
def test_seed_physical_loads_expected_counts_and_is_idempotent():
    _seed_all()
    assert Norm.objects.count() == 120  # 24 tables x 5 exercises
    assert NormBand.objects.count() == 360  # x 3 bands
    assert TestBattery.objects.count() == 12  # 6 TOIFA x 2 genders
    assert BatteryItem.objects.count() == 60  # x 5 exercises
    assert DarajaThreshold.objects.count() == 3

    # Re-running changes nothing.
    call_command("seed_physical")
    assert Norm.objects.count() == 120
    assert NormBand.objects.count() == 360
    assert BatteryItem.objects.count() == 60


@pytest.mark.django_db
def test_seed_physical_norms_reproduce_scoring_example():
    """SCORING.md §9: a 14-year-old boy's 100 m of 14.4 s scores 8 points."""
    _seed_all()
    from datetime import date
    from decimal import Decimal

    from apps.catalog.models import Exercise
    from apps.catalog.selectors import get_norm
    from apps.common.models import Gender

    exercise = Exercise.objects.get(name__icontains="100 m")
    norm = get_norm(exercise, Gender.MALE, 14, date(2026, 6, 1))
    band = norm.bands.filter(
        lower_bound__lte=Decimal("14.4"), upper_bound__gt=Decimal("14.4")
    ).first()
    assert band.points == 8


@pytest.mark.django_db
def test_check_physical_norms_passes_after_seed():
    _seed_all()
    call_command("check_physical_norms")  # exits 0 (raises CommandError on any gap)
