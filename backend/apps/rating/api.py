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
        serializer = _validated_filters(self.request)
        return ranked_athletes(
            serializer.selector_filters(), self.request.user, serializer.period_range()
        )


class TopRatingView(APIView):
    """`GET /rating/top/` — the "Top Athletes" list (limit N, default 10) for the partition,
    cached per scope + filters + limit."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = _validated_filters(request)
        filters = serializer.selector_filters()
        limit = serializer.validated_data.get("limit", 10)
        date_range = serializer.period_range()

        def build():
            rows = top_athletes(filters, request.user, limit=limit, date_range=date_range)
            # Plain list (not DRF's ReturnList) so the value is picklable for the cache.
            return {
                "filters": serializer.filters_header(),
                "results": list(RatingRowSerializer(rows, many=True).data),
            }

        # The period must be part of the cache key or Q1/Q2 results collide.
        cache_filters = {**filters, "limit": limit, **serializer.period_cache_params()}
        return Response(cached_response("top", request.user, cache_filters, build))


class RegionsRatingView(APIView):
    """`GET /rating/regions/` — per-region daraja-I counts + average score, cached."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = _validated_filters(request)
        filters = serializer.selector_filters()
        date_range = serializer.period_range()

        def build():
            rows = region_rating(filters, request.user, date_range)
            return {"results": list(RegionRatingRowSerializer(rows, many=True).data)}

        cache_filters = {**filters, **serializer.period_cache_params()}
        return Response(cached_response("regions", request.user, cache_filters, build))
