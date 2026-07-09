import pytest
from django.core.exceptions import ValidationError

from apps.athletes.factories import AthleteFactory
from apps.athletes.models import Athlete
from apps.catalog.factories import (
    DistrictFactory,
    OrganizationFactory,
    RegionFactory,
    SportTypeFactory,
)
from apps.catalog.models import Organization
from apps.common.models import Gender

pytestmark = pytest.mark.django_db


def test_full_name_without_middle_name():
    athlete = AthleteFactory(last_name="Aliyev", first_name="Ali", middle_name="")
    assert athlete.full_name == "Aliyev Ali"


def test_full_name_with_middle_name():
    athlete = AthleteFactory(last_name="Aliyev", first_name="Ali", middle_name="Vali oʻgʻli")
    assert athlete.full_name == "Aliyev Ali Vali oʻgʻli"


def test_block_returns_otm():
    org = OrganizationFactory(type=Organization.Type.OTM)
    athlete = AthleteFactory(region=org.region, organization=org)
    assert athlete.block == "OTM"


def test_block_returns_opsttm():
    org = OrganizationFactory(type=Organization.Type.OPSTTM)
    athlete = AthleteFactory(region=org.region, organization=org)
    assert athlete.block == "OPSTTM"


def test_str_equals_full_name():
    athlete = AthleteFactory(last_name="Aliyev", first_name="Ali", middle_name="Vali")
    assert str(athlete) == athlete.full_name


def test_clean_raises_when_district_region_mismatches():
    region_a, region_b = RegionFactory(), RegionFactory()
    athlete = Athlete(
        last_name="Aliyev",
        first_name="Ali",
        birth_year=2010,
        gender=Gender.MALE,
        region=region_a,
        district=DistrictFactory(region=region_b),
        organization=OrganizationFactory(region=region_a),
        sport_type=SportTypeFactory(),
    )
    with pytest.raises(ValidationError) as exc:
        athlete.clean()
    assert "district" in exc.value.message_dict


def test_clean_ok_when_district_region_matches():
    region = RegionFactory()
    athlete = Athlete(
        last_name="Aliyev",
        first_name="Ali",
        birth_year=2010,
        gender=Gender.MALE,
        region=region,
        district=DistrictFactory(region=region),
        organization=OrganizationFactory(region=region),
        sport_type=SportTypeFactory(),
    )
    athlete.clean()  # does not raise
