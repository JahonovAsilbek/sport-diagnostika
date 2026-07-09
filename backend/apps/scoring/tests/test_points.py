"""`resolve_points` — band containment + direction-agnostic clamp (BCKND-44, SCORING §3)."""

from decimal import Decimal

import pytest

from apps.catalog.factories import NormBandFactory, NormFactory
from apps.scoring.domain.points import resolve_points

pytestmark = pytest.mark.django_db

# lower_is_better (100 m): smaller = better, so the 10-band holds the smallest numbers.
LOWER = [(10, "14.0", "14.3"), (8, "14.3", "14.6"), (6, "14.6", "14.9")]
# higher_is_better (turnik): more = better, so the 10-band holds the largest numbers.
HIGHER = [(6, "8", "11"), (8, "11", "15"), (10, "15", "25")]


def _norm(bands):
    norm = NormFactory()
    for points, lower, upper in bands:
        NormBandFactory(
            norm=norm,
            points=points,
            lower_bound=Decimal(lower),
            upper_bound=Decimal(upper),
        )
    return norm


def test_in_range_returns_that_bands_points():
    assert resolve_points(_norm(LOWER), Decimal("14.4")) == 8


def test_lower_boundary_is_inclusive():
    assert resolve_points(_norm(LOWER), Decimal("14.3")) == 8  # start of [14.3, 14.6)


def test_upper_boundary_is_exclusive():
    # 14.6 is excluded from [14.3, 14.6) and belongs to the next band [14.6, 14.9) → 6.
    assert resolve_points(_norm(LOWER), Decimal("14.6")) == 6


def test_lower_is_better_below_range_clamps_to_top():
    assert resolve_points(_norm(LOWER), Decimal("13.9")) == 10  # faster than best → 10


def test_lower_is_better_above_range_clamps_to_zero():
    assert resolve_points(_norm(LOWER), Decimal("15.0")) == 0  # slower than worst → 0


def test_higher_is_better_above_range_clamps_to_top():
    assert resolve_points(_norm(HIGHER), Decimal("30")) == 10  # more than best → 10


def test_higher_is_better_below_range_clamps_to_zero():
    assert resolve_points(_norm(HIGHER), Decimal("5")) == 0  # fewer than worst → 0


def test_unsorted_band_input_still_resolves():
    # NormBand's default ordering is -points; the resolver must re-sort by lower_bound.
    norm = _norm([(6, "14.6", "14.9"), (10, "14.0", "14.3"), (8, "14.3", "14.6")])
    assert resolve_points(norm, Decimal("14.1")) == 10


def test_single_band_clamps_to_it_on_both_sides():
    norm = _norm([(10, "0", "10")])
    assert resolve_points(norm, Decimal("15")) == 10
    assert resolve_points(norm, Decimal("-1")) == 10


def test_no_bands_returns_zero():
    assert resolve_points(NormFactory(), Decimal("5")) == 0
