from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.athletes.filters import AthleteFilterSet
from apps.athletes.models import Athlete
from apps.athletes.serializers import AthleteSerializer
from apps.catalog.models import AgeCategory
from apps.common.permissions import COACH, LAB_OPERATOR, REGION_ADMIN, DataEntryOrReadOnly
from apps.common.scoping import ScopedQuerysetMixin
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
        serializer.save(**self._guard_scope(serializer.validated_data))

    def perform_update(self, serializer):
        serializer.save(**self._guard_scope(serializer.validated_data))

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

    # Sub-routes reserved so the URL space is stable for the SPA (F4). Bodies land with
    # their blocks: sessions → B6, recommendations → B10.
    # Each calls get_object() so the sub-route is scope-checked too (out-of-scope pk → 404).
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
        self.get_object()
        return Response([])
