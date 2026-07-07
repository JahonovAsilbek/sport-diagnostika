from rest_framework import serializers

from apps.catalog.models import Exercise
from apps.measurements.models import Measurement, TestSession
from apps.measurements.services import open_session, resnapshot_date


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ("exercise", "raw_value")


class TestSessionSerializer(serializers.ModelSerializer):
    """`athlete`/`date`/`height_cm`/`weight_kg` are writable; the snapshot dims and status
    are read-only (frozen at open / changed only via `finalize`). `athlete` is fixed after
    open — a PATCH that names a different athlete is ignored (the snapshots stay coherent)."""

    measurements = MeasurementSerializer(many=True, read_only=True)

    class Meta:
        model = TestSession
        fields = (
            "id", "athlete", "date", "entered_by", "source", "status",
            "age_category", "gender", "region", "organization", "sport_type",
            "height_cm", "weight_kg", "measurements", "created_at",
        )
        read_only_fields = (
            "entered_by", "source", "status", "age_category", "gender",
            "region", "organization", "sport_type", "created_at",
        )

    def create(self, validated_data):
        return open_session(
            athlete=validated_data["athlete"],
            entered_by=self.context["request"].user,
            date=validated_data.get("date"),
            height_cm=validated_data.get("height_cm"),
            weight_kg=validated_data.get("weight_kg"),
        )

    def update(self, instance, validated_data):
        # Only the mutable draft fields; athlete is fixed at open (snapshots depend on it).
        new_date = validated_data.get("date", instance.date)
        if new_date != instance.date:
            resnapshot_date(instance, new_date)
        for field in ("height_cm", "weight_kg"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class MeasurementItemSerializer(serializers.Serializer):
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    # CharField accepts both a number (14.4) and an "m:ss" string; parsed per value_type.
    raw_value = serializers.CharField()


class MeasurementBulkSerializer(serializers.Serializer):
    """Bulk raw entry: `{"measurements": [{"exercise": id, "raw_value": ...}]}`."""

    measurements = MeasurementItemSerializer(many=True, allow_empty=False)
