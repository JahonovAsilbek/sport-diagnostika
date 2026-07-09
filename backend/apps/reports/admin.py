from django.contrib import admin

from apps.reports.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Reports are produced by the async pipeline — read-only here."""

    list_display = ("id", "requested_by", "type", "format", "status", "created_at", "completed_at")
    list_filter = ("status", "type", "format")
    readonly_fields = (
        "requested_by",
        "type",
        "format",
        "params",
        "status",
        "file",
        "error",
        "completed_at",
    )

    def has_add_permission(self, request):
        return False
