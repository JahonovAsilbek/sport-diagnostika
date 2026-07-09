from rest_framework import serializers

from apps.recommendations.models import Recommendation, RecommendationRule


class RecommendationSerializer(serializers.ModelSerializer):
    """A generated recommendation, with the exercise it relates to (null for a total rule or a
    since-deleted rule)."""

    exercise = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = ("id", "text", "exercise", "created_at")

    def get_exercise(self, obj):
        rule = obj.rule
        return rule.exercise.name if rule and rule.exercise else None


class RecommendationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationRule
        fields = ("id", "exercise", "comparator", "threshold", "template_text", "is_active")

    def validate(self, attrs):
        exercise = attrs.get("exercise", getattr(self.instance, "exercise", None))
        threshold = attrs.get("threshold", getattr(self.instance, "threshold", None))
        limit = 10 if exercise else 50  # exercise points are 0–10; physical_total is 0–50
        if threshold is not None and threshold > limit:
            metric = "mashq ballari (0–10)" if exercise else "umumiy ball (0–50)"
            raise serializers.ValidationError(
                {"threshold": f"Chegara {metric} oralig'idan oshib ketmasligi kerak."}
            )
        return attrs
