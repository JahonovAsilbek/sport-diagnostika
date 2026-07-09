from rest_framework.routers import SimpleRouter

from apps.reports.api import ReportViewSet

router = SimpleRouter()
router.register("reports", ReportViewSet, basename="report")

urlpatterns = router.urls
