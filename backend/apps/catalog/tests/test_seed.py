import pytest
from django.core.management import call_command

from apps.catalog.models import AgeCategory, District, Exercise, Region, SportType

pytestmark = pytest.mark.django_db


def test_seed_catalog_is_idempotent():
    call_command("seed_catalog")
    counts = (
        Region.objects.count(),
        District.objects.count(),
        AgeCategory.objects.count(),
        SportType.objects.count(),
    )
    call_command("seed_catalog")
    assert (
        Region.objects.count(),
        District.objects.count(),
        AgeCategory.objects.count(),
        SportType.objects.count(),
    ) == counts


def test_seed_catalog_expected_counts():
    call_command("seed_catalog")
    assert Region.objects.count() == 14
    assert AgeCategory.objects.count() == 6
    assert SportType.objects.count() >= 30
    assert District.objects.exists()


def test_seed_exercises_is_idempotent():
    call_command("seed_exercises")
    assert Exercise.objects.count() == 9
    call_command("seed_exercises")
    assert Exercise.objects.count() == 9


def test_seed_exercises_directions_and_types():
    call_command("seed_exercises")
    runs = Exercise.objects.filter(name__endswith="yugurish")
    assert runs.count() == 3
    assert all(e.direction == "lower_is_better" for e in runs)
    assert Exercise.objects.get(name__endswith="400 m ga pastki startdan yugurish").value_type == (
        "minsec"
    )
    flex = Exercise.objects.get(name__startswith="Gimnastika")
    assert flex.value_type == "cm_signed"
    assert flex.direction == "higher"
