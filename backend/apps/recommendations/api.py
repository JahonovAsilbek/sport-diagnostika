from rest_framework import viewsets

from apps.common.permissions import IsSuperAdmin
from apps.recommendations.models import RecommendationRule
from apps.recommendations.serializers import RecommendationRuleSerializer


class RecommendationRuleViewSet(viewsets.ModelViewSet):
    """Admin-managed recommendation rules — super_admin only (internal config; coaches consume
    the generated recommendation *text* via `/athletes/{id}/recommendations/`, not the rules)."""

    queryset = RecommendationRule.objects.select_related("exercise").all()
    serializer_class = RecommendationRuleSerializer
    permission_classes = [IsSuperAdmin]
