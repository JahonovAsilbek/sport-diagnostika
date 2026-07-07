from django.contrib import admin

from apps.measurements.models import Measurement, TestSession


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
