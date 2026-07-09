from django.conf import settings
from rest_framework import serializers

from apps.catalog.models import AgeCategory
from apps.common.models import Gender
from apps.measurements.models import ImportBatch, ImportRow


class ImportUploadSerializer(serializers.ModelSerializer):
    """Upload payload: the `.xlsx` file + the template group it targets."""

    class Meta:
        model = ImportBatch
        fields = ("id", "file", "age_category", "gender", "date")

    def validate_file(self, file):
        if not file.name.lower().endswith(".xlsx"):
            raise serializers.ValidationError("Faqat .xlsx fayl qabul qilinadi.")
        if file.size > settings.MAX_IMPORT_FILE_SIZE:
            limit = settings.MAX_IMPORT_FILE_SIZE // (1024 * 1024)
            raise serializers.ValidationError(f"Fayl hajmi {limit} MB dan oshmasligi kerak.")
        return file


class ImportRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRow
        fields = ("row_number", "status", "raw_data", "errors", "athlete", "created_session")


class ImportBatchSerializer(serializers.ModelSerializer):
    rows = ImportRowSerializer(many=True, read_only=True)

    class Meta:
        model = ImportBatch
        fields = (
            "id", "status", "age_category", "gender", "date",
            "row_count", "error_count", "error", "rows", "created_at",
        )


class ImportTemplateQuerySerializer(serializers.Serializer):
    """Query params for `GET /imports/template/` — the group whose battery defines the columns."""

    age_category = serializers.PrimaryKeyRelatedField(queryset=AgeCategory.objects.all())
    gender = serializers.ChoiceField(choices=Gender.choices)
