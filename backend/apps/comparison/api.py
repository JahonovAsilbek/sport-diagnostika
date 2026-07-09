from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.athletes.models import Athlete
from apps.common.scoping import scope_queryset
from apps.comparison.selectors import compare_athletes
from apps.comparison.serializers import ComparisonAthleteSerializer


class ComparisonView(APIView):
    """`GET /comparison/?athletes=1,2,3` — 2–3 athletes side by side (physical results).

    Thin: reads the scoring selectors. Every requested athlete must be in the caller's scope
    (a missing or out-of-scope id → 403, without leaking which). Athletes without an
    Evaluation are returned as no-data rows.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = self._parse_ids(request.query_params.get("athletes", ""))
        scoped = scope_queryset(
            Athlete.objects.all(),
            request.user,
            region_field="region_id",
            organization_field="organization_id",
            coach_field="coach",
        )
        by_id = {athlete.id: athlete for athlete in scoped.filter(id__in=ids)}
        if any(athlete_id not in by_id for athlete_id in ids):
            raise PermissionDenied("Ba'zi sportchilar ko'lamingizdan tashqarida.")

        rows, leader = compare_athletes([by_id[athlete_id] for athlete_id in ids])
        return Response(
            {
                "athletes": ComparisonAthleteSerializer(rows, many=True).data,
                "leader": leader,
            }
        )

    def _parse_ids(self, raw):
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        try:
            ids = [int(part) for part in parts]
        except ValueError as exc:
            raise ValidationError(
                "athletes: butun ID'lar vergul bilan ajratilib berilishi kerak."
            ) from exc
        ids = list(dict.fromkeys(ids))  # dedupe, preserve order
        if not 2 <= len(ids) <= 3:
            raise ValidationError("Taqqoslash uchun 2 yoki 3 ta sportchi kerak.")
        return ids
