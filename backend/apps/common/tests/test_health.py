import pytest
from django.conf import settings


def test_settings_load():
    assert settings.SECRET_KEY
    assert "apps.common" in settings.INSTALLED_APPS
    assert "apps.accounts" in settings.INSTALLED_APPS


@pytest.mark.django_db
def test_health_ok(client):
    resp = client.get("/api/v1/health/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["cache"] == "ok"
