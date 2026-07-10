from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.scoring.api import EvaluationViewSet, RecomputeView

router = SimpleRouter()
router.register("evaluations", EvaluationViewSet, basename="evaluation")

urlpatterns = [
    # The explicit action must precede the router's `evaluations/{pk}/` so "recompute"
    # isn't captured as a pk.
    path("evaluations/recompute/", RecomputeView.as_view(), name="evaluations-recompute"),
    *router.urls,
]
