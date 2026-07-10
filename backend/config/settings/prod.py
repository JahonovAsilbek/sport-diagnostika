"""Production settings — hardened, behind a TLS-terminating reverse proxy (nginx)."""

from .base import *  # noqa: F403
from .base import env

# Never True in production.
DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# TLS is terminated at nginx; trust the forwarded-proto header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Behind Nginx, X-Forwarded-For carries the real client IP for the audit log.
AUDIT_TRUST_X_FORWARDED_FOR = True

# HTTPS-only hardening, gated behind one flag (default on). The pre-TLS D3 profile runs
# HTTP-only and sets SECURE_SSL_REDIRECT=False, so the internal healthcheck and admin
# login work over http; D5 provides certs and leaves these at their True defaults. With
# the redirect on but no https listener, the 301 loops (and the redirect-following
# healthcheck fails); Secure cookies also break admin over plain http.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=SECURE_SSL_REDIRECT)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=SECURE_SSL_REDIRECT)
SECURE_HSTS_SECONDS = (60 * 60 * 24 * 365) if SECURE_SSL_REDIRECT else 0  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_SSL_REDIRECT
SECURE_HSTS_PRELOAD = SECURE_SSL_REDIRECT
X_FRAME_OPTIONS = "DENY"

# Admin POST (and any future same-origin session flow) over the public host. Include the
# scheme, e.g. https://sport-diagnostika.uz. Empty in dev / the D3 HTTP profile.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# The internal container healthcheck hits gunicorn directly over http (no proxy → no
# X-Forwarded-Proto), so with SECURE_SSL_REDIRECT on it would be 301'd to https://127.0.0.1
# (nothing listening) and the redirect-following probe would fail. Exempt just that path.
# SecurityMiddleware strips the leading slash and uses re.search, so anchor with ^…$.
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/$"]

# Structured JSON logs in prod (LOG_LEVEL comes from the env via base, default INFO).
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405

# --- Error tracking (Sentry, DVPS-19) — inert without a DSN; covers web + worker + beat ----
# prod.py is imported once per process (web via gunicorn post-fork; worker/beat via
# config_from_object → the settings import), so this initializes Sentry exactly once each.
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration(monitor_beat_tasks=True)],
        environment=env("SENTRY_ENVIRONMENT", default="production"),
        release=env("SENTRY_RELEASE", default="") or None,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,  # no cookies / client IP / user id
        max_request_body_size="never",  # CRITICAL: never capture request bodies (passwords)
    )
