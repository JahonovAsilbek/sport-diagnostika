from rest_framework import serializers

from apps.catalog.models import AgeCategory, Region, SportType
from apps.common.models import Gender
from apps.scoring.models import Evaluation, IndicatorScore


class IndicatorScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorScore
        fields = ("exercise", "raw_value", "points")


class EvaluationSerializer(serializers.ModelSerializer):
    """The stored scoring snapshot. `evaluation_id` mirrors the pk so the finalize response
    reads `{evaluation_id, physical_total, daraja, color, indicators}` (API.md §6)."""

    evaluation_id = serializers.IntegerField(source="id", read_only=True)
    indicators = IndicatorScoreSerializer(many=True, read_only=True)

    class Meta:
        model = Evaluation
        fields = (
            "evaluation_id",
            "session",
            "athlete",
            "session_date",
            "age_category",
            "gender",
            "region",
            "sport_type",
            "physical_total",
            "ranking_score",
            "daraja",
            "color",
            "computed_at",
            "indicators",
        )


class RecomputeFilterSerializer(serializers.Serializer):
    """Allowlist for `POST /evaluations/recompute/` — only these dims may narrow the slice,
    so raw request data never reaches `TestSession.objects.filter(**kwargs)` directly."""

    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), required=False)
    sport_type = serializers.PrimaryKeyRelatedField(
        queryset=SportType.objects.all(), required=False
    )
    age_category = serializers.PrimaryKeyRelatedField(
        queryset=AgeCategory.objects.all(), required=False
    )
    gender = serializers.ChoiceField(choices=Gender.choices, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def filter_kwargs(self):
        """A JSON-serializable `TestSession` filter (ids/strings only) for the Celery task."""
        data = self.validated_data
        kwargs = {}
        if "region" in data:
            kwargs["region_id"] = data["region"].id
        if "sport_type" in data:
            kwargs["sport_type_id"] = data["sport_type"].id
        if "age_category" in data:
            kwargs["age_category_id"] = data["age_category"].id
        if "gender" in data:
            kwargs["gender"] = data["gender"]
        if "date_from" in data:
            kwargs["date__gte"] = data["date_from"].isoformat()
        if "date_to" in data:
            kwargs["date__lte"] = data["date_to"].isoformat()
        return kwargs
