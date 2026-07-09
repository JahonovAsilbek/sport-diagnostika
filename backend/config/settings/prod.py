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
