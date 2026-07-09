from rest_framework.routers import SimpleRouter

from apps.recommendations.api import RecommendationRuleViewSet

router = SimpleRouter()
router.register("recommendation-rules", RecommendationRuleViewSet, basename="recommendation-rule")

urlpatterns = router.urls
