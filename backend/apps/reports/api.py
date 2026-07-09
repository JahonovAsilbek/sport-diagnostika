from django.db import transaction
from django.http import FileResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import MINISTRY, SUPER_ADMIN
from apps.reports.models import Report
from apps.reports.serializers import ReportRequestSerializer, ReportSerializer
from apps.reports.tasks import generate_report


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Hisobot hali tayyor emas."


class ReportViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Async report requests. Any authenticated user may request one (reports are read-
    generating; the matrix gives Reports to every role); `params` are scoped to the requester.
    A report is visible only to whoever requested it (super_admin/ministry see all)."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Report.objects.order_by("-created_at", "-id")
        user = self.request.user
        if getattr(user, "role", None) in (SUPER_ADMIN, MINISTRY):
            return queryset
        return queryset.filter(requested_by=user)

    def get_serializer_class(self):
        return ReportRequestSerializer if self.action == "create" else ReportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            report = serializer.save(requested_by=request.user)
            transaction.on_commit(lambda: generate_report.delay(report.id))
        return Response(ReportSerializer(report).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """The generated file once `done` — otherwise 409."""
        report = self.get_object()
        if report.status != Report.Status.DONE:
            raise Conflict()
        return FileResponse(
            report.file.open("rb"), as_attachment=True,
            filename=report.file.name.rsplit("/", 1)[-1],
        )
