from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stats.cache import scope_token
from apps.stats.selectors import overview

_TTL = 60


class StatsOverviewView(APIView):
    """`GET /stats/overview/` — role-scoped dashboard numbers (API §12). Cached briefly per
    scope token so one scope's counts never leak to another user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        key = f"stats:overview:{scope_token(request.user)}"
        try:
            data = cache.get_or_set(key, lambda: overview(request.user), _TTL)
        except Exception:
            data = overview(request.user)  # best-effort: a cache outage must not break the read
        return Response(data)
