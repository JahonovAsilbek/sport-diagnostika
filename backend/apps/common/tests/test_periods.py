"""Period → session_date range translation (BCKND-70)."""

from datetime import date

import pytest
from rest_framework.exceptions import ValidationError

from apps.common.periods import PeriodParamsSerializer, period_range_from_params, resolve_period


def test_no_type_returns_none():
    assert resolve_period(None, 2026, 1) is None
    assert resolve_period("", None, None) is None


def test_year_range():
    assert resolve_period("year", 2026, None) == (date(2026, 1, 1), date(2026, 12, 31))


def test_half_ranges():
    assert resolve_period("half", 2026, 1) == (date(2026, 1, 1), date(2026, 6, 30))
    assert resolve_period("half", 2026, 2) == (date(2026, 7, 1), date(2026, 12, 31))


@pytest.mark.parametrize(
    "index,expected",
    [
        (1, (date(2026, 1, 1), date(2026, 3, 31))),
        (2, (date(2026, 4, 1), date(2026, 6, 30))),
        (3, (date(2026, 7, 1), date(2026, 9, 30))),
        (4, (date(2026, 10, 1), date(2026, 12, 31))),
    ],
)
def test_quarter_ranges(index, expected):
    assert resolve_period("quarter", 2026, index) == expected


def test_missing_year_raises():
    with pytest.raises(ValidationError):
        resolve_period("quarter", None, 1)


def test_bad_quarter_index_raises():
    with pytest.raises(ValidationError):
        resolve_period("quarter", 2026, 5)


def test_bad_half_index_raises():
    with pytest.raises(ValidationError):
        resolve_period("half", 2026, 3)


def test_params_helper():
    assert period_range_from_params({"period_type": "year", "period_year": 2025}) == (
        date(2025, 1, 1),
        date(2025, 12, 31),
    )
    assert period_range_from_params({}) is None


def test_serializer_range_and_cache_params():
    s = PeriodParamsSerializer(
        data={"period_type": "quarter", "period_year": 2026, "period_index": 2}
    )
    assert s.is_valid()
    assert s.period_range() == (date(2026, 4, 1), date(2026, 6, 30))
    assert s.period_cache_params() == {
        "period_type": "quarter",
        "period_year": 2026,
        "period_index": 2,
    }


def test_serializer_invalid_combo_fails_validation():
    s = PeriodParamsSerializer(data={"period_type": "quarter"})  # no year
    assert not s.is_valid()


def test_serializer_empty_is_valid_no_range():
    s = PeriodParamsSerializer(data={})
    assert s.is_valid()
    assert s.period_range() is None
    assert s.period_cache_params() == {}
