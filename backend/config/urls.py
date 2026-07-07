"""Root URL configuration.

Only the admin is wired here; `api/v1/`, the OpenAPI schema and docs are added in
BCKND-7, and the health endpoint in BCKND-8.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
