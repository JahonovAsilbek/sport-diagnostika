"""Period → session_date range translation (BCKND-70).

An optional (period_type, year, index) selects a calendar range for filtering evaluations by
`session_date`. Shared by rating, comparison, evaluation-history and reports; absent → no range
(callers fall back to the latest evaluation overall). No period entity — it's derived here.
"""

from datetime import date

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

PERIOD_TYPES = ("quarter", "half", "year")

# Last calendar day of each period-ending month (only these months end a quarter/half/year).
_MONTH_END = {3: 31, 6: 30, 9: 30, 12: 31}


def resolve_period(period_type, year, index):
    """Translate a period selection into an inclusive (start_date, end_date), or None when no
    `period_type` is given. Raises DRF ``ValidationError`` on an invalid combination."""
    if not period_type:
        return None
    if year is None:
        raise ValidationError({"period_year": "Davr uchun yil majburiy."})
    if period_type == "year":
        return date(year, 1, 1), date(year, 12, 31)
    if period_type == "half":
        if index not in (1, 2):
            raise ValidationError({"period_index": "Yarim yil 1 yoki 2 boʻlishi kerak."})
        if index == 1:
            return date(year, 1, 1), date(year, 6, 30)
        return date(year, 7, 1), date(year, 12, 31)
    if period_type == "quarter":
        if index not in (1, 2, 3, 4):
            raise ValidationError({"period_index": "Chorak 1 dan 4 gacha boʻlishi kerak."})
        start_month = (index - 1) * 3 + 1
        end_month = start_month + 2
        return date(year, start_month, 1), date(year, end_month, _MONTH_END[end_month])
    raise ValidationError({"period_type": "Notoʻgʻri davr turi."})


def period_range_from_params(params):
    """The (start, end) range for a report's `params` dict, or None — same validation as the
    query-param path (raises ``ValidationError`` on a bad combo → reports fail at request time)."""
    return resolve_period(
        params.get("period_type"),
        params.get("period_year"),
        params.get("period_index"),
    )


class PeriodParamsSerializer(serializers.Serializer):
    """The optional period query params — reusable standalone (comparison, evaluation-history) or
    as a base class (the rating filter serializer)."""

    period_type = serializers.ChoiceField(choices=PERIOD_TYPES, required=False)
    period_year = serializers.IntegerField(required=False, min_value=2000, max_value=2100)
    period_index = serializers.IntegerField(required=False, min_value=1, max_value=4)

    def validate(self, attrs):
        # Surface an invalid period combo (e.g. quarter with no year) at is_valid() time.
        resolve_period(
            attrs.get("period_type"), attrs.get("period_year"), attrs.get("period_index")
        )
        return attrs

    def period_range(self):
        data = self.validated_data
        return resolve_period(
            data.get("period_type"), data.get("period_year"), data.get("period_index")
        )

    def period_cache_params(self):
        """Only the period keys that are present — folded into the rating cache key so a period's
        results never collide with another's."""
        keys = ("period_type", "period_year", "period_index")
        return {k: self.validated_data[k] for k in keys if k in self.validated_data}
