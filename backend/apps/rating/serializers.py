from rest_framework import serializers

from apps.catalog.models import AgeCategory, Region, SportType
from apps.common.models import Gender
from apps.common.periods import PeriodParamsSerializer


class RatingFilterSerializer(PeriodParamsSerializer):
    """Validates the rating query params (all optional). `region`/`sport_type`/`age_category`
    are PKs; `age_category` filters the Evaluation snapshot FK directly (no birth_year range —
    that translation is only for the computed athlete list). `limit` applies to `/top/`. The
    optional `period_*` fields (inherited) scope ranking to the latest evaluation in a period."""

    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), required=False)
    sport_type = serializers.PrimaryKeyRelatedField(
        queryset=SportType.objects.all(), required=False
    )
    age_category = serializers.PrimaryKeyRelatedField(
        queryset=AgeCategory.objects.all(), required=False
    )
    gender = serializers.ChoiceField(choices=Gender.choices, required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, required=False, default=10)

    def selector_filters(self):
        """The whitelisted `Evaluation` filter kwargs (ids/strings) for the ranking selectors."""
        data = self.validated_data
        filters = {}
        if "region" in data:
            filters["region_id"] = data["region"].id
        if "sport_type" in data:
            filters["sport_type_id"] = data["sport_type"].id
        if "age_category" in data:
            filters["age_category_id"] = data["age_category"].id
        if "gender" in data:
            filters["gender"] = data["gender"]
        return filters

    def filters_header(self):
        """Human-readable echo of the applied filters (names) for the `/top/` envelope."""
        data = self.validated_data
        header = {}
        if "region" in data:
            header["region"] = data["region"].name
        if "sport_type" in data:
            header["sport_type"] = data["sport_type"].name
        if "age_category" in data:
            header["age_category"] = data["age_category"].name
        if "gender" in data:
            header["gender"] = data["gender"]
        return header


class AthleteRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()


class RatingRowSerializer(serializers.Serializer):
    """One ranked athlete row (serializes a rank-annotated `Evaluation`)."""

    rank = serializers.IntegerField()
    athlete = AthleteRefSerializer()
    ranking_score = serializers.IntegerField()
    daraja = serializers.CharField()
    color = serializers.CharField()


class RegionRatingRowSerializer(serializers.Serializer):
    """One region row (serializes a dict from `region_rating`)."""

    rank = serializers.IntegerField()
    region = serializers.CharField(source="region__name")
    daraja_i_count = serializers.IntegerField()
    avg_score = serializers.SerializerMethodField()

    def get_avg_score(self, obj):
        value = obj.get("avg_score")
        return round(float(value), 1) if value is not None else None
