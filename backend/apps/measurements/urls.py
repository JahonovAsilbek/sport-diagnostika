from rest_framework.routers import SimpleRouter

from apps.measurements.api import TestSessionViewSet

router = SimpleRouter()
router.register("sessions", TestSessionViewSet, basename="session")

urlpatterns = router.urls
