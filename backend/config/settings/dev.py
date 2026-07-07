"""Development settings."""
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Dev convenience: the SPA may run on any localhost port.
CORS_ALLOW_ALL_ORIGINS = True
