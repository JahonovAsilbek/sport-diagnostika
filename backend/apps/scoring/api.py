from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.periods import PeriodParamsSerializer
from apps.common.permissions import IsSuperAdmin
from apps.common.scoping import ScopedQuerysetMixin
from apps.scoring.models import Evaluation
from apps.scoring.serializers import EvaluationSerializer, RecomputeFilterSerializer
from apps.scoring.tasks import recompute_evaluations


class EvaluationViewSet(ScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """`GET /evaluations/` — read-only, region/org/coach-scoped scoring snapshots (API.md §6).

    Filter by ``athlete``/``session`` (+ the snapshot dims); order by ``session_date`` (newest
    first by default). Drives the F6 result view + history and the athlete card's evaluation
    summary. The snapshot region/sport_type live on the row (no athlete join for those); org and
    coach scope resolve through ``session``/``athlete``.
    """

    queryset = Evaluation.objects.select_related(
        "athlete", "session", "region", "sport_type", "age_category"
    ).prefetch_related("indicators")
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["athlete", "session", "gender", "region", "sport_type", "age_category"]
    ordering_fields = ["session_date", "physical_total"]
    ordering = ["-session_date", "-id"]
    scope_region_field = "region_id"
    scope_organization_field = "session__organization_id"
    scope_coach_field = "athlete__coach"

    def get_queryset(self):
        # Optional period filter (BCKND-70): narrow the history to a session_date range.
        qs = super().get_queryset()
        period = PeriodParamsSerializer(data=self.request.query_params)
        period.is_valid(raise_exception=True)
        date_range = period.period_range()
        if date_range:
            qs = qs.filter(session_date__range=date_range)
        return qs


class RecomputeView(APIView):
    """`POST /evaluations/recompute/` — super_admin triggers a re-score of finalized
    sessions after a norm change (API.md §14). The slice is narrowed only by the allowlisted
    filter; the work runs in the worker (D1), so this returns `202` + the task id."""

    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = RecomputeFilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = recompute_evaluations.delay(serializer.filter_kwargs())
        return Response(
            {"task_id": result.id, "status": "pending"}, status=status.HTTP_202_ACCEPTED
        )
