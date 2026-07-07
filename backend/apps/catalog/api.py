from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.catalog.models import (
    AgeCategory,
    District,
    Exercise,
    Organization,
    Region,
    SportType,
    TestBattery,
)
from apps.catalog.serializers import (
    AgeCategorySerializer,
    DistrictSerializer,
    ExerciseSerializer,
    OrganizationSerializer,
    RegionSerializer,
    SportTypeSerializer,
    TestBatterySerializer,
)
from apps.common.permissions import SUPER_ADMIN

# Reference lists are NOT region-scoped — everyone sees every region/sport/exercise
# (API.md §4). Only data entities (athletes/measurements) are scoped.
# follow-up: cache list responses in Redis and invalidate on write (read-heavy data).


class ReadOnlyOrSuperAdmin(BasePermission):
    """Read for any authenticated user; write (create/update/delete) for super_admin."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(user, "role", None) == SUPER_ADMIN


class CatalogViewSet(viewsets.ModelViewSet):
    """Base for the catalog reference viewsets — read-any, write-super_admin."""

    permission_classes = [ReadOnlyOrSuperAdmin]


class RegionViewSet(CatalogViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class DistrictViewSet(CatalogViewSet):
    queryset = District.objects.select_related("region")
    serializer_class = DistrictSerializer
    filterset_fields = ["region"]


class OrganizationViewSet(CatalogViewSet):
    queryset = Organization.objects.select_related("region", "district")
    serializer_class = OrganizationSerializer
    filterset_fields = ["type", "region"]


class SportTypeViewSet(CatalogViewSet):
    queryset = SportType.objects.all()
    serializer_class = SportTypeSerializer


class AgeCategoryViewSet(CatalogViewSet):
    queryset = AgeCategory.objects.all()
    serializer_class = AgeCategorySerializer


class ExerciseViewSet(CatalogViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    filterset_fields = ["is_active"]


class TestBatteryViewSet(CatalogViewSet):
    queryset = TestBattery.objects.prefetch_related("items__exercise")
    serializer_class = TestBatterySerializer
    filterset_fields = ["age_category", "gender"]
