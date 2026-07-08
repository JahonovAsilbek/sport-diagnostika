from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsSuperAdmin
from apps.scoring.serializers import RecomputeFilterSerializer
from apps.scoring.tasks import recompute_evaluations


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
