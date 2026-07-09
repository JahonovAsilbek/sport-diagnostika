from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.catalog.validators import assert_bands_no_overlap


def _band(lower, upper):
    return {"lower_bound": Decimal(lower), "upper_bound": Decimal(upper)}


# Pure function — no DB needed (BCKND-33).


def test_disjoint_bands_pass():
    assert_bands_no_overlap([_band("0", "10"), _band("10", "20"), _band("20", "30")])


def test_touching_bands_are_disjoint():
    # Half-open [lower, upper): band ending at 10 and one starting at 10 don't overlap.
    assert_bands_no_overlap([_band("10", "20"), _band("0", "10")])


def test_overlapping_bands_raise():
    with pytest.raises(ValidationError):
        assert_bands_no_overlap([_band("0", "11"), _band("10", "20")])


def test_unordered_overlap_is_detected():
    with pytest.raises(ValidationError):
        assert_bands_no_overlap([_band("10", "20"), _band("15", "25"), _band("0", "5")])
