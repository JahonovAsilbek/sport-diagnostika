"""Base settings shared by every environment.

Secrets and environment-specific values are read from the environment via
django-environ. `DATABASES`/`CACHES` (BCKND-3), DRF/JWT/OpenAPI (BCKND-7) and Celery
(BCKND-6) are wired in their own tasks.
"""

from datetime import timedelta
from pathlib import Path

import environ

# backend/ — manage.py lives here; this file is backend/config/settings/base.py.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Load backend/.env for local dev if present; real environment variables win.
environ.Env.read_env(BASE_DIR / ".env")

# Mandatory — no default. In prod the app must refuse to start without it.
SECRET_KEY = env("SECRET_KEY")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
]

LOCAL_APPS = [
    "apps.common",
    "apps.accounts",
    "apps.catalog",
    "apps.athletes",
    "apps.measurements",
    "apps.scoring",
    "apps.rating",
    "apps.comparison",
    "apps.recommendations",
    "apps.reports",
    "apps.audit",
    "apps.stats",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "apps.common.middleware.RequestIDMiddleware",  # outermost — the request id covers everything
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditContextMiddleware",  # binds the request for the audit signals
]

# Trust X-Forwarded-For for the audit IP only behind a known proxy (prod/Nginx). Off by
# default — without a proxy the header is client-spoofable.
AUDIT_TRUST_X_FORWARDED_FOR = False

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Custom user model — set before the first migrate (BCKND-5). The initial migration
# is generated in BCKND-9.
AUTH_USER_MODEL = "accounts.User"

# Database — parsed from DATABASE_URL (psycopg v3). The Postgres service is started
# in DVPS-D1; this is wiring only. The DB is required for `migrate`.
DATABASES = {"default": env.db("DATABASE_URL")}

# Cache — Redis. The connection is lazy (opened on first use), so the project imports
# and `runserver` comes up even when Redis is down.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

# Celery — broker and result backend default to REDIS_URL.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=env("REDIS_URL"))
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=env("REDIS_URL"))
CELERY_TASK_TRACK_STARTED = True
CELERY_TIMEZONE = "Asia/Tashkent"
# Don't let the worker replace the root logger at boot — keep our LOGGING (+ request-id filter)
# governing worker output (DVPS-19).
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Beat liveness heartbeat (DVPS-18). DatabaseScheduler (DVPS-7) syncs this into the DB on start.
# The task is a no-op unless HEALTHCHECK_PING_URL is set (opt-in dead-man switch).
HEALTHCHECK_PING_URL = env("HEALTHCHECK_PING_URL", default="")
CELERY_BEAT_SCHEDULE = {
    "heartbeat": {"task": "apps.common.tasks.heartbeat", "schedule": 300.0},  # every 5 min
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# Static files & media
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Excel import caps (B11). DATA_UPLOAD_MAX_MEMORY_SIZE does NOT cap uploaded files, so the
# import upload serializer/task enforce these explicitly.
MAX_IMPORT_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_IMPORT_ROWS = 2000

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS — allowed origins from env (dev overrides with CORS_ALLOW_ALL_ORIGINS).
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# --- Logging (DVPS-19) --------------------------------------------------------------------
# One console handler on root → stdout (Docker captures + rotates it via the json-file driver).
# The request-id filter is on the HANDLER so every propagated record is stamped; named loggers
# only set levels and propagate, so each line is emitted exactly once. prod.py flips the
# formatter to JSON. Never log SQL/params (django.db.backends at WARNING) — no PII in logs.
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "apps.common.logging.RequestIDFilter"}},
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"},
        "json": {"()": "apps.common.logging.JsonFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "plain",
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"level": LOG_LEVEL},
        "django.request": {"level": "ERROR"},  # 5xx as ERROR; drop 4xx noise
        "django.db.backends": {"level": "WARNING"},  # never log SQL / bound params
        "django.security": {"level": "WARNING"},
        "celery": {"level": LOG_LEVEL},
        "apps": {"level": LOG_LEVEL},
    },
}

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.DefaultPagination",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# JWT — full login/refresh/logout lands in B2; the config lives here.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# OpenAPI schema (drf-spectacular)
SPECTACULAR_SETTINGS = {
    "TITLE": "SPORT-DIAGNOSTIKA API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Schema + Swagger UI are public (no auth) — required in dev.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}
