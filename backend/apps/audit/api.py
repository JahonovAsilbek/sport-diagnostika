from rest_framework import viewsets

from apps.audit.filters import AuditLogFilterSet
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.common.pagination import DefaultPagination
from apps.common.permissions import IsSuperAdmin


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /audit/` — the change log, super_admin only (API §13). Filter by user, entity_type,
    and a created_at date range."""

    queryset = AuditLog.objects.select_related("user")
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = DefaultPagination
    filterset_class = AuditLogFilterSet
