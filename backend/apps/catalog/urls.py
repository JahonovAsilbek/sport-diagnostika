from rest_framework.routers import SimpleRouter

from apps.catalog.api import (
    AgeCategoryViewSet,
    DistrictViewSet,
    ExerciseViewSet,
    OrganizationViewSet,
    RegionViewSet,
    SportTypeViewSet,
    TestBatteryViewSet,
)

router = SimpleRouter()
router.register("regions", RegionViewSet, basename="region")
router.register("districts", DistrictViewSet, basename="district")
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("sport-types", SportTypeViewSet, basename="sport-type")
router.register("age-categories", AgeCategoryViewSet, basename="age-category")
router.register("exercises", ExerciseViewSet, basename="exercise")
router.register("batteries", TestBatteryViewSet, basename="battery")

urlpatterns = router.urls
