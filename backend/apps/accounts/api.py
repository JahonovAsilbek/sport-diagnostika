from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import Role
from apps.accounts.serializers import LoginSerializer, UserSerializer, UserWriteSerializer
from apps.common.permissions import IsUserAdmin
from apps.common.scoping import ScopedQuerysetMixin

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail": "refresh token required"}, status=400)
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            return Response({"detail": "invalid or expired refresh token"}, status=400)
        return Response(status=204)


class MeView(RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserViewSet(ScopedQuerysetMixin, viewsets.ModelViewSet):
    """User administration.

    super_admin manages everyone; region_admin manages users within their own region
    (scoped by BCKND-14 and unable to create super_admins or cross-region users).
    Delete is a soft deactivate (is_active=False) to preserve audit/FK integrity.
    """

    queryset = User.objects.select_related("region", "organization").order_by("id")
    permission_classes = [IsUserAdmin]
    scope_region_field = "region_id"
    search_fields = ["username", "first_name", "last_name", "email"]
    filterset_fields = ["role", "is_active"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return UserWriteSerializer
        return UserSerializer

    def perform_create(self, serializer):
        self._guard_region_admin(serializer.validated_data)
        serializer.save()

    def perform_update(self, serializer):
        self._guard_region_admin(serializer.validated_data)
        serializer.save()

    def _guard_region_admin(self, data):
        actor = self.request.user
        if actor.role != Role.REGION_ADMIN:
            return
        if data.get("role") == Role.SUPER_ADMIN:
            raise PermissionDenied("region_admin super_admin yarata olmaydi.")
        region = data.get("region")
        if region is not None and region.pk != actor.region_id:
            raise PermissionDenied(
                "region_admin faqat o'z viloyatidagi foydalanuvchini boshqaradi."
            )
        organization = data.get("organization")
        if organization is not None and organization.region_id != actor.region_id:
            raise PermissionDenied("Tashkilot region_admin viloyatida bo'lishi kerak.")

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get("password")
        if not new_password:
            return Response({"detail": "password required"}, status=400)
        try:
            validate_password(new_password, user)
        except DjangoValidationError as exc:
            return Response({"password": list(exc.messages)}, status=400)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response(status=204)
