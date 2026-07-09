"""Root URL configuration.

App routes are added under `api/v1/` as blocks land (auth in B2, catalog in B3, …).
The health endpoint is added in BCKND-8.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.views import health

# API v1 routes — filled in as backend blocks deliver their endpoints.
api_v1 = [
    path("health/", health, name="health"),
    path("", include("apps.accounts.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("", include("apps.athletes.urls")),
    path("", include("apps.measurements.urls")),
    path("", include("apps.scoring.urls")),
    path("rating/", include("apps.rating.urls")),
    path("", include("apps.comparison.urls")),
    path("", include("apps.recommendations.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "api"))),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
