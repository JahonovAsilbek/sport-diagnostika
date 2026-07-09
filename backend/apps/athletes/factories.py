import factory

from apps.athletes.models import Athlete
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
