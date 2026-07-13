from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import Role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only profile — never exposes the password hash."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    region = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "first_name",
            "last_name",
            "role",
            "phone",
            "email",
            "is_active",
            "region",
            "organization",
        )
        read_only_fields = fields

    def get_region(self, obj):
        return {"id": obj.region_id, "name": obj.region.name} if obj.region_id else None

    def get_organization(self, obj):
        if not obj.organization_id:
            return None
        return {"id": obj.organization_id, "name": obj.organization.name}


class LoginSerializer(TokenObtainPairSerializer):
    """Token pair + the authenticated user's profile (so the SPA skips a /me call)."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class UserWriteSerializer(serializers.ModelSerializer):
    """Create/update users — the password is write-only and always hashed."""

    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_active",
            "region",
            "organization",
        )

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "Yangi foydalanuvchi uchun parol majburiy."}
            )
        role = attrs.get("role") or getattr(self.instance, "role", None)
        region = attrs.get("region", getattr(self.instance, "region", None))
        organization = attrs.get("organization", getattr(self.instance, "organization", None))
        if role == Role.REGION_ADMIN and not region:
            raise serializers.ValidationError({"region": "region_admin uchun viloyat majburiy."})
        if role in (Role.COACH, Role.LAB_OPERATOR) and not organization:
            raise serializers.ValidationError(
                {"organization": "coach/lab_operator uchun tashkilot majburiy."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
