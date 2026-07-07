from decimal import Decimal

import factory

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import AgeCategoryFactory, ExerciseFactory
from apps.measurements.models import Measurement, TestSession


class TestSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestSession

    athlete = factory.SubFactory(AthleteFactory)
    entered_by = factory.SubFactory(UserFactory)
    # Snapshot dims mirror the athlete (as open_session would freeze them); age_category
    # is a fresh TOIFA — tests that need the battery wire it to this same category.
    gender = factory.SelfAttribute("athlete.gender")
    region = factory.SelfAttribute("athlete.region")
    organization = factory.SelfAttribute("athlete.organization")
    sport_type = factory.SelfAttribute("athlete.sport_type")
    age_category = factory.SubFactory(AgeCategoryFactory)


class MeasurementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Measurement

    session = factory.SubFactory(TestSessionFactory)
    exercise = factory.SubFactory(ExerciseFactory)
    raw_value = Decimal("10")
