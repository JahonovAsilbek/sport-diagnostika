from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import DefaultPagination
from apps.rating.cache import cached_response
from apps.rating.selectors import ranked_athletes, region_rating, top_athletes
from apps.rating.serializers import (
    RatingFilterSerializer,
    RatingRowSerializer,
    RegionRatingRowSerializer,
)


def _validated_filters(request):
    serializer = RatingFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return serializer


class AthletesRatingView(generics.ListAPIView):
    """`GET /rating/athletes/` — the full ranked list (paginated). Rank is computed by the
    window in SQL, so LIMIT/OFFSET pagination keeps page-2 ranks continuous. Uncached (many
    pages, and the query is index-backed)."""

    permission_classes = [IsAuthenticated]
    serializer_class = RatingRowSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        filters = _validated_filters(self.request).selector_filters()
        return ranked_athletes(filters, self.request.user)


class TopRatingView(APIView):
    """`GET /rating/top/` — the "Top Athletes" list (limit N, default 10) for the partition,
    cached per scope + filters + limit."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = _validated_filters(request)
        filters = serializer.selector_filters()
        limit = serializer.validated_data.get("limit", 10)

        def build():
            rows = top_athletes(filters, request.user, limit=limit)
            # Plain list (not DRF's ReturnList) so the value is picklable for the cache.
            return {
                "filters": serializer.filters_header(),
                "results": list(RatingRowSerializer(rows, many=True).data),
            }

        return Response(cached_response("top", request.user, {**filters, "limit": limit}, build))


class RegionsRatingView(APIView):
    """`GET /rating/regions/` — per-region daraja-I counts + average score, cached."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters = _validated_filters(request).selector_filters()

        def build():
            rows = region_rating(filters, request.user)
            return {"results": list(RegionRatingRowSerializer(rows, many=True).data)}

        return Response(cached_response("regions", request.user, filters, build))
