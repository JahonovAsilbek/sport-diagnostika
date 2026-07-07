from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Lightweight liveness probe for nginx / uptime monitoring (DVPS-D3/D7).

    Public and cheap — only `SELECT 1` and a cache round-trip. Returns 503 (and names
    the failing component) if the DB or cache is unreachable.
    """
    db_ok = _check_db()
    cache_ok = _check_cache()
    healthy = db_ok and cache_ok
    data = {
        "status": "ok" if healthy else "unhealthy",
        "db": "ok" if db_ok else "down",
        "cache": "ok" if cache_ok else "down",
        "time": timezone.now().isoformat(),
    }
    return Response(data, status=200 if healthy else 503)


def _check_db():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return False
    return True


def _check_cache():
    try:
        cache.set("healthcheck", "1", 5)
        return cache.get("healthcheck") == "1"
    except Exception:
        return False
