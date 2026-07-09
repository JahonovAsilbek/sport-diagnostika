"""Per-request actor context for the audit signals. Model signals have no request, so a
middleware binds the request here (in a `ContextVar` — coroutine-safe, reset per request) and
the signal reads the user LAZILY: this API authenticates with JWT via DRF, which resolves
`request.user` in the view (after `AuthenticationMiddleware`), so an eager read would see
AnonymousUser. Off-request (Celery / management commands) the actor is `(None, None)`."""
from contextvars import ContextVar

from django.conf import settings

_ctx = ContextVar("audit_request", default=None)


def bind_request(request, ip):
    """Bind the current request + resolved IP; returns a token to `reset` with in a finally."""
    return _ctx.set({"request": request, "ip": ip})


def set_actor(user=None, ip=None):
    """Bind an actor directly (tests / off-request writers). Returns a token to `reset`."""
    return _ctx.set({"user": user, "ip": ip})


def reset(token):
    _ctx.reset(token)


def current_actor():
    """`(user_or_None, ip_or_None)` for the mutation being logged — user read lazily."""
    ctx = _ctx.get()
    if ctx is None:
        return None, None
    if "user" in ctx:  # set_actor path
        return ctx["user"], ctx.get("ip")
    user = getattr(ctx["request"], "user", None)
    if not getattr(user, "is_authenticated", False):
        user = None
    return user, ctx.get("ip")


def client_ip(request):
    """The client IP — the first `X-Forwarded-For` hop only when we trust the proxy (prod
    behind Nginx), otherwise `REMOTE_ADDR` (XFF is client-spoofable without a known proxy)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if getattr(settings, "AUDIT_TRUST_X_FORWARDED_FOR", False) and forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
