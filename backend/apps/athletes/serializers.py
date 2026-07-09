from datetime import date

from rest_framework import serializers

from apps.accounts.models import Role
from apps.athletes.models import Athlete
from apps.athletes.selectors import age_at, match_age_category
from apps.catalog.models import AgeCategory
from apps.catalog.serializers import AgeCategorySerializer


class AthleteSerializer(serializers.ModelSerializer):
    """Read: computed `full_name`, `block` (OTM/OPSTTM classification) and the derived
    `age_category` (TOIFA at today's date; `null` when out of range). FKs are writable
    by primary key; scope enforcement happens in the viewset (BCKND-37)."""

    full_name = serializers.CharField(read_only=True)
    block = serializers.CharField(read_only=True)
    age_category = serializers.SerializerMethodField()

    class Meta:
        model = Athlete
        fields = (
            "id",
            "last_name",
            "first_name",
            "middle_name",
            "full_name",
            "birth_year",
            "gender",
            "region",
            "district",
            "organization",
            "sport_type",
            "coach",
            "razryad",
            "training_experience",
            "main_competitions",
            "block",
            "age_category",
            "is_active",
            "created_at",
        )
        read_only_fields = ("created_at",)

    def get_age_category(self, obj):
        # The viewset preloads the tiny TOIFA table into context to avoid a per-row query.
        categories = self.context.get("age_categories")
        if categories is None:
            categories = list(AgeCategory.objects.order_by("ordinal"))
        category = match_age_category(categories, age_at(obj.birth_year, date.today()))
        return AgeCategorySerializer(category).data if category else None

    def validate(self, attrs):
        coach = attrs.get("coach")
        if coach is not None and getattr(coach, "role", None) != Role.COACH:
            raise serializers.ValidationError({"coach": "Tanlangan foydalanuvchi murabbiy emas."})

        region = attrs.get("region", getattr(self.instance, "region", None))
        district = attrs.get("district", getattr(self.instance, "district", None))
        if district is not None and region is not None and district.region_id != region.id:
            raise serializers.ValidationError(
                {"district": "Tuman tanlangan viloyatga tegishli bo'lishi kerak."}
            )
        return attrs
