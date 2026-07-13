from rest_framework import serializers

from apps.common.periods import period_range_from_params
from apps.reports.datasets import assert_params_in_scope
from apps.reports.models import Report


class ReportRequestSerializer(serializers.ModelSerializer):
    """`POST /reports/` payload. `params` is scoped to the requester in `validate` — an
    out-of-scope request raises `PermissionDenied` (403)."""

    class Meta:
        model = Report
        fields = ("id", "type", "format", "params", "status", "created_at")
        read_only_fields = ("status", "created_at")

    def validate(self, attrs):
        params = attrs.get("params") or {}
        # Reject a bad period at request time (400) rather than in the async worker (BCKND-70).
        period_range_from_params(params)
        assert_params_in_scope(attrs["type"], params, self.context["request"].user)
        return attrs


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            "id",
            "type",
            "format",
            "params",
            "status",
            "error",
            "created_at",
            "completed_at",
        )
