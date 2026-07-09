from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import (
    AgeCategory,
    BatteryItem,
    DarajaThreshold,
    District,
    Exercise,
    Norm,
    NormBand,
    Organization,
    Region,
    SportType,
    TestBattery,
)
from apps.catalog.validators import assert_bands_no_overlap


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


class NormBandSerializer(serializers.ModelSerializer):
    """One `[lower_bound, upper_bound)` raw-value band → points (SCORING.md §3.4)."""

    class Meta:
        model = NormBand
        fields = ("points", "lower_bound", "upper_bound")


class NormSerializer(serializers.ModelSerializer):
    """A norm with its writable nested band set — the norm editor (F9) POST/PUTs this.

    `exercise` is accepted as a primary key on write and nested on read (API.md §4).
    Writing replaces the whole band set atomically and re-runs the overlap check.
    """

    bands = NormBandSerializer(many=True)

    class Meta:
        model = Norm
        fields = (
            "id",
            "exercise",
            "age_min",
            "age_max",
            "gender",
            "valid_from",
            "is_active",
            "bands",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["exercise"] = ExerciseSerializer(instance.exercise).data
        return data

    def _replace_bands(self, norm, bands_data):
        try:
            assert_bands_no_overlap(bands_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"bands": list(exc.messages)}) from exc
        norm.bands.all().delete()
        NormBand.objects.bulk_create(NormBand(norm=norm, **band) for band in bands_data)

    def create(self, validated_data):
        bands_data = validated_data.pop("bands")
        with transaction.atomic():
            norm = Norm.objects.create(**validated_data)
            self._replace_bands(norm, bands_data)
        return norm

    def update(self, instance, validated_data):
        bands_data = validated_data.pop("bands", None)
        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()
            if bands_data is not None:
                self._replace_bands(instance, bands_data)
        return instance


class DarajaThresholdSerializer(serializers.ModelSerializer):
    """Total (0–50) → daraja cut-off (I/II/III). Read-only over the API; the admin edits it."""

    class Meta:
        model = DarajaThreshold
        fields = ("id", "level", "total_min", "total_max")
