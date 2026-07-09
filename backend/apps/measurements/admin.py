from django.contrib import admin

from apps.measurements.models import ImportBatch, ImportRow, Measurement, TestSession


class MeasurementInline(admin.TabularInline):
    model = Measurement
    extra = 0
    raw_id_fields = ("exercise",)


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = (
        "athlete", "date", "status", "age_category", "gender",
        "region", "sport_type", "entered_by",
    )
    list_filter = ("status", "source", "gender", "region", "sport_type")
    search_fields = ("athlete__last_name", "athlete__first_name")
    list_select_related = (
        "athlete", "age_category", "region", "organization", "sport_type", "entered_by",
    )
    raw_id_fields = ("athlete", "entered_by")
    inlines = [MeasurementInline]


class ImportRowInline(admin.TabularInline):
    model = ImportRow
    extra = 0
    can_delete = False
    readonly_fields = ("row_number", "status", "raw_data", "errors", "athlete", "created_session")


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    """Import batches are produced by the upload/validate pipeline — read-only here."""

    list_display = ("id", "uploaded_by", "age_category", "gender", "status",
                    "row_count", "error_count", "created_at")
    list_filter = ("status", "gender")
    readonly_fields = ("uploaded_by", "file", "age_category", "gender", "date",
                       "status", "row_count", "error_count")
    inlines = [ImportRowInline]

    def has_add_permission(self, request):
        return False
