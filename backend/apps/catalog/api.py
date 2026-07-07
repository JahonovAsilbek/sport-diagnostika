from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.catalog.models import (
    AgeCategory,
    DarajaThreshold,
    District,
    Exercise,
    Norm,
    Organization,
    Region,
    SportType,
    TestBattery,
)
from apps.catalog.serializers import (
    AgeCategorySerializer,
    DarajaThresholdSerializer,
    DistrictSerializer,
    ExerciseSerializer,
    NormSerializer,
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


class NormViewSet(CatalogViewSet):
    """Norms with nested bands — read for any authenticated user, write for super_admin.

    Not region-scoped: the physical standard is universal by age × gender (API.md §4).
    """

    queryset = Norm.objects.select_related("exercise").prefetch_related("bands")
    serializer_class = NormSerializer
    filterset_fields = ["exercise", "age_min", "age_max", "gender"]


class DarajaThresholdViewSet(viewsets.ReadOnlyModelViewSet):
    """Daraja cut-offs (I/II/III → total range). Read-only over the API; edited in admin."""

    permission_classes = [ReadOnlyOrSuperAdmin]
    queryset = DarajaThreshold.objects.all()
    serializer_class = DarajaThresholdSerializer
