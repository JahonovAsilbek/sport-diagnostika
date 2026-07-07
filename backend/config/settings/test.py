"""Test settings — Postgres test DB, in-memory cache (no Redis), fast hashing."""
from .dev import *  # noqa: F403

# Tests must not hit Redis — use a local in-memory cache.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Speed up password hashing in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Plain static storage in tests (no collectstatic manifest needed).
STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
