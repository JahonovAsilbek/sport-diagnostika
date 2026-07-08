from django.urls import path

from apps.scoring.api import RecomputeView

urlpatterns = [
    path("evaluations/recompute/", RecomputeView.as_view(), name="evaluations-recompute"),
]
