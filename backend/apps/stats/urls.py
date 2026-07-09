from django.urls import path

from apps.stats.api import StatsOverviewView

urlpatterns = [
    path("stats/overview/", StatsOverviewView.as_view(), name="stats-overview"),
]
