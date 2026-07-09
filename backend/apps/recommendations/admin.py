from django.contrib import admin

from apps.recommendations.models import Recommendation, RecommendationRule


@admin.register(RecommendationRule)
class RecommendationRuleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "exercise", "comparator", "threshold", "is_active")
    list_filter = ("is_active", "comparator", "exercise")
    search_fields = ("template_text",)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """Recommendations are generated on finalize — read-only here."""

    list_display = ("id", "evaluation", "rule", "text", "created_at")
    list_filter = ("rule",)
    readonly_fields = ("evaluation", "rule", "text")

    def has_add_permission(self, request):
        return False
