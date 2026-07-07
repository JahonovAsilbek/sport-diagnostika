from rest_framework.routers import SimpleRouter

from apps.athletes.api import AthleteViewSet

router = SimpleRouter()
router.register("athletes", AthleteViewSet, basename="athlete")

urlpatterns = router.urls
