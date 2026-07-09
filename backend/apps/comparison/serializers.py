from rest_framework import serializers


class ComparisonIndicatorSerializer(serializers.Serializer):
    """One exercise's result for an athlete — the exercise NAME (batteries differ by
    age×gender, so the name is what lets the reader match rows across athletes)."""

    exercise = serializers.CharField(source="exercise.name")
    raw_value = serializers.DecimalField(max_digits=8, decimal_places=2)
    points = serializers.IntegerField()


class ComparisonAthleteSerializer(serializers.Serializer):
    """One athlete's side. Scalars are read from a plain dict; `indicators` from the latest
    Evaluation's `IndicatorScore`s (empty for a no-data athlete)."""

    id = serializers.IntegerField()
    full_name = serializers.CharField()
    physical_total = serializers.IntegerField(allow_null=True)
    ranking_score = serializers.IntegerField(allow_null=True)
    daraja = serializers.CharField(allow_null=True)
    color = serializers.CharField(allow_null=True)
    indicators = ComparisonIndicatorSerializer(many=True)
