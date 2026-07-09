from rest_framework.routers import SimpleRouter

from apps.measurements.api import TestSessionViewSet
from apps.measurements.import_api import ImportBatchViewSet

router = SimpleRouter()
router.register("sessions", TestSessionViewSet, basename="session")
router.register("imports", ImportBatchViewSet, basename="import")

urlpatterns = router.urls
