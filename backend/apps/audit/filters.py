import django_filters as filters

from apps.audit.models import AuditLog


class AuditLogFilterSet(filters.FilterSet):
    date_from = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = ["user", "entity_type"]
