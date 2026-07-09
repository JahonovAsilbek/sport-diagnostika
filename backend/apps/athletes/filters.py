from datetime import date

import django_filters as filters

from apps.athletes.models import Athlete
from apps.catalog.models import AgeCategory


class AthleteFilterSet(filters.FilterSet):
    """Athlete list filters. `age_category` (a computed dimension) is translated to a
    `birth_year` range in SQL so the DB does the work — never a per-row Python compute
    at scale (TASK BCKND-36)."""

    age_category = filters.ModelChoiceFilter(
        queryset=AgeCategory.objects.all(),
        method="filter_age_category",
        label="TOIFA (yosh toifasi)",
    )

    class Meta:
        model = Athlete
        fields = [
            "region",
            "district",
            "organization",
            "sport_type",
            "gender",
            "coach",
            "is_active",
        ]

    def filter_age_category(self, queryset, name, value):
        today = date.today()
        return queryset.filter(
            birth_year__gte=today.year - value.age_max,
            birth_year__lte=today.year - value.age_min,
        )
