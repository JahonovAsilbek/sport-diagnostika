from rest_framework.routers import SimpleRouter

from apps.recommendations.api import RecommendationRuleViewSet, RecommendationViewSet

router = SimpleRouter()
router.register("recommendation-rules", RecommendationRuleViewSet, basename="recommendation-rule")
router.register("recommendations", RecommendationViewSet, basename="recommendation")

urlpatterns = router.urls
