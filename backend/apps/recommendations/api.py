from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsSuperAdmin
from apps.common.scoping import ScopedQuerysetMixin
from apps.recommendations.models import Recommendation, RecommendationRule
from apps.recommendations.serializers import (
    RecommendationRuleSerializer,
    RecommendationSerializer,
)


class RecommendationRuleViewSet(viewsets.ModelViewSet):
    """Admin-managed recommendation rules — super_admin only (internal config; coaches consume
    the generated recommendation *text* via `/recommendations/`, not the rules)."""

    queryset = RecommendationRule.objects.select_related("exercise").all()
    serializer_class = RecommendationRuleSerializer
    permission_classes = [IsSuperAdmin]


class RecommendationFilterSet(filters.FilterSet):
    # Filter by athlete across all of their evaluations (the card/F9 use this).
    athlete = filters.NumberFilter(field_name="evaluation__athlete")

    class Meta:
        model = Recommendation
        fields = ["evaluation", "athlete"]


class RecommendationViewSet(ScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """`GET /recommendations/` — read-only, scoped generated recommendations. Filter by
    ``athlete`` or ``evaluation`` (F9 recommendations view + the athlete card). Scope resolves
    through the parent Evaluation."""

    queryset = Recommendation.objects.select_related("evaluation", "rule", "rule__exercise")
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = RecommendationFilterSet
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    scope_region_field = "evaluation__region_id"
    scope_organization_field = "evaluation__session__organization_id"
    scope_coach_field = "evaluation__athlete__coach"
