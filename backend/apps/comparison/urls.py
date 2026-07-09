from django.urls import path

from apps.comparison.api import ComparisonView

urlpatterns = [
    path("comparison/", ComparisonView.as_view(), name="comparison"),
]
