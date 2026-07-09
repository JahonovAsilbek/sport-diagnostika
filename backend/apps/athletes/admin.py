from django.contrib import admin

from apps.athletes.models import Athlete


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "birth_year",
        "gender",
        "region",
        "organization",
        "sport_type",
        "coach",
        "is_active",
    )
    list_filter = ("gender", "is_active", "region", "sport_type", "organization")
    search_fields = ("last_name", "first_name", "middle_name")
    list_select_related = ("region", "organization", "sport_type", "coach")
    # Users can be numerous — a raw-id widget avoids a huge dropdown; the FK's
    # limit_choices_to already restricts the picker to role=coach users.
    raw_id_fields = ("coach",)
