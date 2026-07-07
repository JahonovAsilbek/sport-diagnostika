from datetime import date
from decimal import Decimal

import factory

from apps.catalog.models import (
    AgeCategory,
    BatteryItem,
    DarajaThreshold,
    District,
    Exercise,
    Norm,
    NormBand,
    Organization,
    Region,
    SportType,
    TestBattery,
)
from apps.common.models import Gender


class RegionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Region
        django_get_or_create = ("code",)

    name = factory.Sequence(lambda n: f"Region {n}")
    code = factory.Sequence(lambda n: f"R{n}")


class DistrictFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = District

    region = factory.SubFactory(RegionFactory)
    name = factory.Sequence(lambda n: f"District {n}")


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Org {n}")
    type = Organization.Type.OTM
    region = factory.SubFactory(RegionFactory)


class SportTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SportType
        django_get_or_create = ("code",)

    name = factory.Sequence(lambda n: f"Sport {n}")
    code = factory.Sequence(lambda n: f"S{n}")


class AgeCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AgeCategory
        django_get_or_create = ("ordinal",)

    ordinal = factory.Sequence(lambda n: n + 1)
    name = factory.LazyAttribute(lambda o: f"cat {o.ordinal}")
    age_min = 10
    age_max = 12


class ExerciseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Exercise

    name = factory.Sequence(lambda n: f"Exercise {n}")
    unit = "s"
    value_type = Exercise.ValueType.SECONDS
    direction = Exercise.Direction.LOWER
    order = factory.Sequence(lambda n: n)


class TestBatteryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestBattery

    age_category = factory.SubFactory(AgeCategoryFactory)
    gender = Gender.MALE


class BatteryItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BatteryItem

    battery = factory.SubFactory(TestBatteryFactory)
    exercise = factory.SubFactory(ExerciseFactory)
    order = factory.Sequence(lambda n: n + 1)


class NormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Norm

    exercise = factory.SubFactory(ExerciseFactory)
    age_min = 14
    age_max = 14
    gender = Gender.MALE
    valid_from = date(2026, 1, 1)
    is_active = True


class NormBandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NormBand

    norm = factory.SubFactory(NormFactory)
    points = 10
    lower_bound = Decimal("0")
    upper_bound = Decimal("10")


class DarajaThresholdFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DarajaThreshold
        django_get_or_create = ("level",)

    level = DarajaThreshold.Level.FIRST
    total_min = 48
    total_max = 50
