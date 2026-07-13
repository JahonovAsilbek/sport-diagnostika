from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.models import Role
from apps.athletes.models import Athlete, AthleteAssignmentHistory
from apps.athletes.selectors import age_at, match_age_category
from apps.catalog.models import AgeCategory, District, Organization, Region, SportType
from apps.catalog.serializers import AgeCategorySerializer

User = get_user_model()


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


class AssignmentHistorySerializer(serializers.ModelSerializer):
    """One assignment period (BCKND-68): FK ids + read-only display names. Newest first."""

    region_name = serializers.CharField(source="region.name", read_only=True)
    district_name = serializers.CharField(source="district.name", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    sport_type_name = serializers.CharField(source="sport_type.name", read_only=True)
    coach_name = serializers.CharField(source="coach.username", read_only=True)
    changed_by_name = serializers.CharField(source="changed_by.username", read_only=True)

    class Meta:
        model = AthleteAssignmentHistory
        fields = (
            "id",
            "region",
            "region_name",
            "district",
            "district_name",
            "organization",
            "organization_name",
            "sport_type",
            "sport_type_name",
            "coach",
            "coach_name",
            "changed_by",
            "changed_by_name",
            "valid_from",
            "valid_to",
            "reason",
            "created_at",
        )


class AthleteTransferSerializer(serializers.Serializer):
    """Input for `POST /athletes/{id}/transfer/`. Any subset of placement fields may be given
    (unspecified ones keep their current value, merged in the view); `reason` is required. The
    district-belongs-region check runs in the view against the merged target."""

    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), required=False)
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), required=False, allow_null=True
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), required=False
    )
    sport_type = serializers.PrimaryKeyRelatedField(
        queryset=SportType.objects.all(), required=False
    )
    coach = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    reason = serializers.CharField()

    ASSIGNMENT_FIELDS = ("region", "district", "organization", "sport_type", "coach")

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("Sabab kiritilishi shart.")
        return value

    def validate(self, attrs):
        if not any(field in attrs for field in self.ASSIGNMENT_FIELDS):
            raise serializers.ValidationError("Kamida bitta tayinlash maydoni berilishi kerak.")
        coach = attrs.get("coach")
        if coach is not None and getattr(coach, "role", None) != Role.COACH:
            raise serializers.ValidationError({"coach": "Tanlangan foydalanuvchi murabbiy emas."})
        return attrs
