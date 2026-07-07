from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only profile — never exposes the password hash."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "role", "phone", "email", "is_active")
        read_only_fields = fields


class LoginSerializer(TokenObtainPairSerializer):
    """Token pair + the authenticated user's profile (so the SPA skips a /me call)."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
