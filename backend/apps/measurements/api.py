from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.athletes.models import Athlete
from apps.catalog.serializers import TestBatterySerializer
from apps.common.permissions import DataEntryOrReadOnly
from apps.common.scoping import ScopedQuerysetMixin, scope_queryset
from apps.measurements.models import TestSession
from apps.measurements.selectors import resolve_battery
from apps.measurements.serializers import MeasurementBulkSerializer, TestSessionSerializer
from apps.measurements.services import finalize_session, save_measurements
from apps.scoring.serializers import EvaluationSerializer
from apps.scoring.services import evaluate_session


class TestSessionViewSet(ScopedQuerysetMixin, viewsets.ModelViewSet):
    """Physical-battery test sessions. Scoped like athletes (the session carries the
    athlete's snapshot dims and is reachable via `athlete.coach`). Only `draft` sessions
    are mutable; `finalize` validates the full 5-exercise battery and transitions to
    `finalized` (the scoring/Evaluation is wired in B7/BCKND-46)."""

    queryset = TestSession.objects.select_related(
        "athlete", "entered_by", "age_category", "region", "organization", "sport_type"
    ).prefetch_related("measurements__exercise")
    serializer_class = TestSessionSerializer
    permission_classes = [DataEntryOrReadOnly]
    filterset_fields = ["athlete", "status"]
    ordering_fields = ["date", "created_at"]

    scope_region_field = "region_id"
    scope_organization_field = "organization_id"
    scope_coach_field = "athlete__coach"

    def perform_create(self, serializer):
        self._assert_athlete_in_scope(serializer.validated_data["athlete"])
        serializer.save()

    def perform_update(self, serializer):
        self._require_draft(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._require_draft(instance)
        instance.delete()

    def _require_draft(self, session):
        if not session.is_draft:
            raise ValidationError("Yakunlangan sessiya tahrirlanmaydi.")

    def _assert_athlete_in_scope(self, athlete):
        """A scoped creator may only open a session for an athlete in their own scope."""
        allowed = scope_queryset(
            Athlete.objects.all(),
            self.request.user,
            region_field="region_id",
            organization_field="organization_id",
            coach_field="coach",
        )
        if not allowed.filter(pk=athlete.pk).exists():
            raise PermissionDenied("Bu sportchi ko'lamingizdan tashqarida.")

    @action(detail=True, methods=["get"])
    def battery(self, request, pk=None):
        """The ordered 5 exercises for the session's group — drives the entry form."""
        battery = resolve_battery(self.get_object())
        if battery is None:
            raise ValidationError("Bu guruh uchun test batareyasi aniqlanmagan.")
        return Response(TestBatterySerializer(battery).data)

    @action(detail=True, methods=["post"])
    def measurements(self, request, pk=None):
        """Bulk raw entry for the battery exercises (draft only)."""
        session = self.get_object()
        self._require_draft(session)
        serializer = MeasurementBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        save_measurements(session, serializer.validated_data["measurements"])
        session.refresh_from_db()
        return Response(self.get_serializer(session).data)

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        """Validate the complete battery, transition draft→finalized, then score it.

        The validation + status flip + `Evaluation` share one transaction (BCKND-46): a
        scoring failure — e.g. a missing norm makes an indicator unscored → 400 — rolls the
        status back to draft so the session can be re-finalized once the norm exists.
        """
        session = self.get_object()
        with transaction.atomic():
            finalize_session(session)
            evaluation = evaluate_session(session)
        return Response({**EvaluationSerializer(evaluation).data, "status": "computed"})
