from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.athletes.filters import AthleteFilterSet
from apps.athletes.models import Athlete
from apps.athletes.serializers import (
    AssignmentHistorySerializer,
    AthleteSerializer,
    AthleteTransferSerializer,
)
from apps.athletes.services import ASSIGNMENT_FIELDS, open_initial_assignment, transfer_athlete
from apps.catalog.models import AgeCategory
from apps.common.permissions import COACH, LAB_OPERATOR, REGION_ADMIN, DataEntryOrReadOnly
from apps.common.scoping import ScopedQuerysetMixin
from apps.recommendations.selectors import recommendations_for_athlete
from apps.recommendations.serializers import RecommendationSerializer
from apps.scoring.selectors import athlete_evaluations, latest_evaluation
from apps.scoring.serializers import EvaluationSerializer


class AthleteViewSet(ScopedQuerysetMixin, viewsets.ModelViewSet):
    """Athlete registry — the canonical region-scoped entity (BCKND-37).

    super_admin/ministry see all; region_admin by region; lab_operator by organization;
    coach by `coach=self`. A scoped creator can only place an athlete inside their scope.
    """

    queryset = Athlete.objects.select_related(
        "region", "district", "organization", "sport_type", "coach"
    )
    serializer_class = AthleteSerializer
    permission_classes = [DataEntryOrReadOnly]
    filterset_class = AthleteFilterSet
    search_fields = ["last_name", "first_name", "middle_name"]
    ordering_fields = ["last_name", "birth_year", "created_at"]

    scope_region_field = "region_id"
    scope_organization_field = "organization_id"
    scope_coach_field = "coach"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["age_categories"] = list(AgeCategory.objects.order_by("ordinal"))
        return context

    def perform_create(self, serializer):
        athlete = serializer.save(**self._guard_scope(serializer.validated_data))
        # Open the athlete's first (current) assignment record (BCKND-68).
        open_initial_assignment(athlete, changed_by=self.request.user)

    def perform_update(self, serializer):
        # Placement changes go only through the transfer action (an atomic, recorded move) — a
        # plain PATCH/PUT that tries to change one is rejected (BCKND-68).
        data = serializer.validated_data
        instance = serializer.instance
        if any(
            field in data and data[field] != getattr(instance, field)
            for field in ASSIGNMENT_FIELDS
        ):
            raise ValidationError(
                {
                    "detail": "Tayinlash (viloyat/tuman/tashkilot/sport/murabbiy) faqat "
                    "transfer orqali oʻzgartiriladi."
                }
            )
        serializer.save(**self._guard_scope(data))

    def perform_destroy(self, instance):
        # Soft delete (like users): athletes accrue sessions/evaluations, so preserve the
        # row and its history — clients filter on is_active.
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    def _guard_scope(self, data):
        """A scoped creator may only place/keep an athlete inside their own scope. Returns
        the fields to force on save (coach → self). Mirrors accounts `_guard_region_admin`."""
        user = self.request.user
        role = getattr(user, "role", None)
        region = data.get("region")
        organization = data.get("organization")

        if role in (COACH, LAB_OPERATOR):
            if organization is not None and organization.pk != user.organization_id:
                raise PermissionDenied("Faqat o'z tashkilotingizga sportchi qo'sha olasiz.")
            return {"coach": user} if role == COACH else {}

        if role == REGION_ADMIN:
            if region is not None and region.pk != user.region_id:
                raise PermissionDenied("region_admin faqat o'z viloyatidagi sportchini boshqaradi.")
            if organization is not None and organization.region_id != user.region_id:
                raise PermissionDenied("Tashkilot region_admin viloyatida bo'lishi kerak.")
        return {}

    # Sub-routes reserved so the URL space is stable for the SPA (F4). sessions → B6 (kept a
    # stub — sessions are listed via /sessions/?athlete=). Each calls get_object() so the
    # sub-route is scope-checked too (out-of-scope pk → 404).
    @action(detail=True, methods=["get"])
    def sessions(self, request, pk=None):
        self.get_object()
        return Response([])

    @action(detail=True, methods=["get"])
    def evaluations(self, request, pk=None):
        """The athlete's Evaluation snapshots, newest first (un-paginated history)."""
        athlete = self.get_object()
        evaluations = athlete_evaluations(athlete)
        return Response(EvaluationSerializer(evaluations, many=True).data)

    @action(detail=True, methods=["get"], url_path="latest-evaluation")
    def latest_evaluation(self, request, pk=None):
        """The athlete's most recent Evaluation, or 204 if none yet."""
        athlete = self.get_object()
        evaluation = latest_evaluation(athlete)
        if evaluation is None:
            return Response(status=204)
        return Response(EvaluationSerializer(evaluation).data)

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        """Recommendations from the athlete's latest Evaluation (un-paginated list)."""
        athlete = self.get_object()
        recommendations = recommendations_for_athlete(athlete)
        return Response(RecommendationSerializer(recommendations, many=True).data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """The athlete's assignment/transfer history, newest first (BCKND-68)."""
        athlete = self.get_object()
        records = athlete.assignment_history.select_related(
            "region", "district", "organization", "sport_type", "coach", "changed_by"
        )
        return Response(AssignmentHistorySerializer(records, many=True).data)

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        """Move the athlete to a new placement — atomic, records changed_by + reason (BCKND-68).
        Unspecified fields keep their current value; the target is scoped like a create."""
        athlete = self.get_object()
        serializer = AthleteTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target = {field: data.get(field, getattr(athlete, field)) for field in ASSIGNMENT_FIELDS}
        if target["district"] is not None and target["district"].region_id != target["region"].id:
            raise ValidationError(
                {"district": "Tuman tanlangan viloyatga tegishli bo'lishi kerak."}
            )
        # Scope the target placement (region_admin/coach/lab_operator can't move out of scope).
        target.update(self._guard_scope(target))

        transfer_athlete(athlete, changed_by=request.user, reason=data["reason"], **target)
        athlete.refresh_from_db()
        return Response(AthleteSerializer(athlete, context=self.get_serializer_context()).data)
