from django.db import transaction
from django.http import HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from apps.common.permissions import MINISTRY, SUPER_ADMIN, DataEntryOrReadOnly
from apps.measurements.import_serializers import (
    ImportBatchSerializer,
    ImportTemplateQuerySerializer,
    ImportUploadSerializer,
)
from apps.measurements.import_services import build_template, commit_batch
from apps.measurements.models import ImportBatch
from apps.measurements.tasks import validate_import_batch

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Amal joriy holatda bajarib bo'lmaydi."


class ImportBatchViewSet(
    mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Bulk Excel import (B11). A batch is a personal artifact — visible only to its uploader
    (super_admin/ministry see all). Upload → async validation → commit."""

    permission_classes = [DataEntryOrReadOnly]

    def get_queryset(self):
        queryset = ImportBatch.objects.prefetch_related("rows").order_by("-created_at", "-id")
        user = self.request.user
        if getattr(user, "role", None) in (SUPER_ADMIN, MINISTRY):
            return queryset
        return queryset.filter(uploaded_by=user)

    def get_serializer_class(self):
        return ImportUploadSerializer if self.action == "create" else ImportBatchSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            batch = serializer.save(uploaded_by=request.user)
            # Enqueue only after the file + batch commit, so the worker never races the write.
            transaction.on_commit(lambda: validate_import_batch.delay(batch.id))
        return Response(ImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def template(self, request):
        """Download the `.xlsx` template for a group (columns = its 5 battery exercises)."""
        query = ImportTemplateQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        workbook = build_template(data["age_category"], data["gender"])
        response = HttpResponse(content_type=_XLSX)
        response["Content-Disposition"] = 'attachment; filename="import_template.xlsx"'
        workbook.save(response)
        return response

    @action(detail=True, methods=["post"])
    def commit(self, request, pk=None):
        """Commit the validated rows into sessions/measurements/evaluations (partial commit)."""
        batch = self.get_object()
        if batch.status != ImportBatch.Status.VALIDATED:
            raise Conflict("Faqat 'validated' holatidagi batch commit qilinadi.")
        commit_batch(batch)
        batch.refresh_from_db()
        return Response(ImportBatchSerializer(batch).data)
