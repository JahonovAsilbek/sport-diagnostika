import datetime

import pytest

from apps.athletes.selectors import (
    AgeOutOfRange,
    age_at,
    age_category_for,
    match_age_category,
)
from apps.catalog.factories import AgeCategoryFactory
from apps.catalog.models import AgeCategory

pytestmark = pytest.mark.django_db

ON_DATE = datetime.date(2026, 7, 7)


def _make_categories():
    AgeCategoryFactory(ordinal=1, name="7–8", age_min=7, age_max=8)
    AgeCategoryFactory(ordinal=4, name="13–15", age_min=13, age_max=15)
    AgeCategoryFactory(ordinal=6, name="18–29", age_min=18, age_max=29)
    return list(AgeCategory.objects.order_by("ordinal"))


def test_age_at():
    assert age_at(2019, ON_DATE) == 7
    assert age_at(2008, ON_DATE) == 18
    assert age_at(1997, ON_DATE) == 29


def test_match_age_category_in_range():
    categories = _make_categories()
    category = match_age_category(categories, 14)
    assert category.age_min == 13
    assert category.age_max == 15


def test_match_age_category_out_of_range_returns_none():
    categories = _make_categories()
    assert match_age_category(categories, 6) is None
    assert match_age_category(categories, 30) is None


def test_age_category_for_boundaries():
    _make_categories()
    assert age_category_for(2019, ON_DATE).ordinal == 1  # age 7
    assert age_category_for(2018, ON_DATE).ordinal == 1  # age 8
    assert age_category_for(2008, ON_DATE).ordinal == 6  # age 18
    assert age_category_for(1997, ON_DATE).ordinal == 6  # age 29


def test_age_category_for_out_of_range_raises():
    _make_categories()
    with pytest.raises(AgeOutOfRange) as exc:
        age_category_for(2020, ON_DATE)  # age 6
    assert exc.value.age == 6

    with pytest.raises(AgeOutOfRange) as exc:
        age_category_for(1996, ON_DATE)  # age 30
    assert exc.value.age == 30
