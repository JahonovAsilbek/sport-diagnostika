"""Login rate limiting + brute-force lockout (BCKND-69). The `_isolate_cache` autouse fixture
(root conftest) gives each test a clean throttle/lockout state."""

import pytest

from apps.accounts.factories import UserFactory

pytestmark = pytest.mark.django_db

LOGIN = "/api/v1/auth/login/"
GENERIC = "Login yoki parol noto'g'ri."


def _attempt(client, username, password):
    return client.post(
        LOGIN, {"username": username, "password": password}, content_type="application/json"
    )


def test_wrong_password_is_401_generic(client):
    UserFactory(username="ali")
    resp = _attempt(client, "ali", "wrong")
    assert resp.status_code == 401
    assert resp.json()["detail"] == GENERIC


def test_unknown_user_same_generic_message(client):
    # No enumeration: an unknown username returns the identical error as a wrong password.
    resp = _attempt(client, "ghost", "wrong")
    assert resp.status_code == 401
    assert resp.json()["detail"] == GENERIC


def test_lockout_after_threshold_blocks_even_correct_password(client):
    UserFactory(username="ali")
    for _ in range(5):  # threshold = 5
        assert _attempt(client, "ali", "wrong").status_code == 401
    # Locked now — even the correct password is refused with 429.
    assert _attempt(client, "ali", "password123").status_code == 429


def test_success_resets_failure_counter(client):
    UserFactory(username="ali")
    for _ in range(4):  # below threshold
        assert _attempt(client, "ali", "wrong").status_code == 401
    assert _attempt(client, "ali", "password123").status_code == 200  # clears the counter
    # After the reset, counting starts from zero — a single failure does not lock.
    assert _attempt(client, "ali", "wrong").status_code == 401


def test_login_rate_throttled_after_limit(client):
    # The scoped login throttle caps the endpoint by IP (10/min) regardless of credentials;
    # distinct usernames keep the per-(username, IP) lockout from tripping first.
    for i in range(10):
        _attempt(client, f"u{i}", "x")
    assert _attempt(client, "u10", "x").status_code == 429
