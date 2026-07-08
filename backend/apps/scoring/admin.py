from django.contrib import admin

from apps.scoring.models import Evaluation, IndicatorScore


class IndicatorScoreInline(admin.TabularInline):
    model = IndicatorScore
    extra = 0
    can_delete = False
    readonly_fields = ("exercise", "raw_value", "points")


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """Evaluations are computed snapshots — view-only in the admin (no manual edits)."""

    list_display = (
        "athlete", "session_date", "physical_total", "daraja", "color", "computed_at",
    )
    list_filter = ("daraja", "gender", "region", "sport_type")
    search_fields = ("athlete__last_name", "athlete__first_name")
    readonly_fields = (
        "session", "athlete", "age_category", "gender", "region", "sport_type",
        "session_date", "physical_total", "daraja", "color", "ranking_score", "computed_at",
    )
    inlines = [IndicatorScoreInline]

    def has_add_permission(self, request):
        return False
