from datetime import date

import factory

from apps.athletes.models import Athlete, AthleteAssignmentHistory
from apps.catalog.factories import OrganizationFactory, RegionFactory, SportTypeFactory
from apps.common.models import Gender


class AthleteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Athlete

    last_name = factory.Faker("last_name")
    first_name = factory.Faker("first_name")
    birth_year = 2010
    gender = Gender.MALE
    region = factory.SubFactory(RegionFactory)
    # Keep the organization in the athlete's region by default (a realistic, consistent
    # row); tests that need a mismatch pass region/organization explicitly.
    organization = factory.SubFactory(OrganizationFactory, region=factory.SelfAttribute("..region"))
    sport_type = factory.SubFactory(SportTypeFactory)
    is_active = True


class AssignmentHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AthleteAssignmentHistory

    athlete = factory.SubFactory(AthleteFactory)
    # Mirror the athlete's current placement by default (an open, current record).
    region = factory.SelfAttribute("athlete.region")
    district = factory.SelfAttribute("athlete.district")
    organization = factory.SelfAttribute("athlete.organization")
    sport_type = factory.SelfAttribute("athlete.sport_type")
    coach = factory.SelfAttribute("athlete.coach")
    valid_from = factory.LazyFunction(date.today)
    valid_to = None
