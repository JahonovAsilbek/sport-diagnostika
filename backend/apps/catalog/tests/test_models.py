import pytest
from django.db import IntegrityError, transaction

from apps.catalog.factories import AgeCategoryFactory, RegionFactory
from apps.catalog.models import AgeCategory, District, Region, TestBattery
from apps.common.models import Gender

pytestmark = pytest.mark.django_db


def test_region_code_is_unique():
    Region.objects.create(name="Birinchi", code="DUP")
    with transaction.atomic(), pytest.raises(IntegrityError):
        Region.objects.create(name="Ikkinchi", code="DUP")


def test_age_category_ordinal_is_unique():
    AgeCategory.objects.create(ordinal=3, name="11–12", age_min=11, age_max=12)
    with transaction.atomic(), pytest.raises(IntegrityError):
        AgeCategory.objects.create(ordinal=3, name="boshqa", age_min=11, age_max=12)


def test_district_is_unique_per_region():
    region = RegionFactory()
    District.objects.create(region=region, name="Tuman")
    with transaction.atomic(), pytest.raises(IntegrityError):
        District.objects.create(region=region, name="Tuman")


def test_same_district_name_allowed_in_other_region():
    District.objects.create(region=RegionFactory(), name="Tuman")
    # Different region → the (region, name) pair is still unique.
    District.objects.create(region=RegionFactory(), name="Tuman")
    assert District.objects.filter(name="Tuman").count() == 2


def test_battery_is_unique_per_age_category_and_gender():
    cat = AgeCategoryFactory()
    TestBattery.objects.create(age_category=cat, gender=Gender.MALE)
    with transaction.atomic(), pytest.raises(IntegrityError):
        TestBattery.objects.create(age_category=cat, gender=Gender.MALE)


def test_battery_allows_both_genders_for_one_category():
    cat = AgeCategoryFactory()
    TestBattery.objects.create(age_category=cat, gender=Gender.MALE)
    TestBattery.objects.create(age_category=cat, gender=Gender.FEMALE)
    assert TestBattery.objects.filter(age_category=cat).count() == 2
