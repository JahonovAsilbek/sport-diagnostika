from rest_framework import serializers

from apps.catalog.models import (
    AgeCategory,
    BatteryItem,
    District,
    Exercise,
    Organization,
    Region,
    SportType,
    TestBattery,
)


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "name", "code")


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ("id", "name", "region")


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "type", "region", "district")


class SportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportType
        fields = ("id", "name", "code")


class AgeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeCategory
        fields = ("id", "ordinal", "name", "age_min", "age_max")


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ("id", "name", "unit", "value_type", "direction", "order", "is_active")


class BatteryItemSerializer(serializers.ModelSerializer):
    """One slot of a battery — the ordered exercise the athlete performs."""

    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = BatteryItem
        fields = ("order", "exercise")


class TestBatterySerializer(serializers.ModelSerializer):
    """A battery with its ordered items — this drives the entry form (B6)."""

    items = BatteryItemSerializer(many=True, read_only=True)

    class Meta:
        model = TestBattery
        fields = ("id", "age_category", "gender", "is_active", "items")
