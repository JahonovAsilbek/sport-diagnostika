import pytest

from apps.accounts.factories import UserFactory

LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"
ME = "/api/v1/auth/me/"


def _login(client, username="ali", password="password123"):
    return client.post(
        LOGIN, {"username": username, "password": password}, content_type="application/json"
    ).json()


@pytest.mark.django_db
def test_login_returns_tokens_and_profile(client):
    UserFactory(username="ali", role="region_admin", first_name="Ali", last_name="V")
    resp = client.post(
        LOGIN, {"username": "ali", "password": "password123"}, content_type="application/json"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access" in data and "refresh" in data
    assert data["user"]["role"] == "region_admin"
    assert data["user"]["full_name"] == "Ali V"
    assert "password" not in data["user"]


@pytest.mark.django_db
def test_refresh_mints_new_access(client):
    UserFactory(username="ali")
    refresh = _login(client)["refresh"]
    resp = client.post(REFRESH, {"refresh": refresh}, content_type="application/json")
    assert resp.status_code == 200
    assert "access" in resp.json()


@pytest.mark.django_db
def test_logout_blacklists_refresh(client):
    UserFactory(username="ali")
    tokens = _login(client)
    resp = client.post(
        LOGOUT,
        {"refresh": tokens["refresh"]},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    assert resp.status_code == 204
    # The blacklisted refresh can no longer mint an access token.
    resp = client.post(REFRESH, {"refresh": tokens["refresh"]}, content_type="application/json")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_logout_without_refresh_is_400(client):
    UserFactory(username="ali")
    access = _login(client)["access"]
    resp = client.post(
        LOGOUT, {}, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {access}"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_me_returns_profile(client):
    UserFactory(username="ali")
    access = _login(client)["access"]
    resp = client.get(ME, HTTP_AUTHORIZATION=f"Bearer {access}")
    assert resp.status_code == 200
    assert resp.json()["username"] == "ali"


@pytest.mark.django_db
def test_me_unauthenticated_is_401(client):
    resp = client.get(ME)
    assert resp.status_code == 401
