"""Rating response cache (BCKND-51). Redis in dev/prod, locmem in tests.

Invalidation is a global **generation counter**: any Evaluation write bumps it, and every
rating cache key embeds the current generation, so a bumped generation makes all prior
responses unreachable — rankings never go stale (the TTL is only a backstop). Coarser than
per-partition invalidation, but a correct superset of it. All cache access is best-effort:
a Redis outage must never break a write (the counter bump) or a read (falls back to compute).
"""
from django.core.cache import cache

from apps.common.permissions import COACH, LAB_OPERATOR, MINISTRY, REGION_ADMIN, SUPER_ADMIN

_GEN_KEY = "rating:gen"
_TTL = 300


def generation():
    return cache.get(_GEN_KEY, 0)


def bump_generation():
    """Advance the generation, invalidating every cached rating response. Best-effort."""
    try:
        cache.incr(_GEN_KEY)
    except ValueError:
        cache.set(_GEN_KEY, 1, None)  # first bump — the counter itself never expires
    except Exception:
        pass  # a cache outage must not break the Evaluation write that triggered this


def scope_token(user):
    """A per-user cache discriminator so one scope's ranking never leaks to another user —
    two region_admins with identical filters must not share a cache key."""
    role = getattr(user, "role", None)
    if role in (SUPER_ADMIN, MINISTRY):
        return "all"
    if role == REGION_ADMIN:
        return f"r{getattr(user, 'region_id', None)}"
    if role == LAB_OPERATOR:
        return f"o{getattr(user, 'organization_id', None)}"
    if role == COACH:
        return f"c{user.id}"
    return f"u{user.id}"


def _key(endpoint, token, filters):
    parts = ",".join(f"{name}={filters[name]}" for name in sorted(filters))
    return f"rating:{endpoint}:{token}:{parts}:{generation()}"


def cached_response(endpoint, user, filters, build):
    """Return the cached response for (endpoint, scope, filters, generation) or `build()` it
    and store it. Any cache error degrades gracefully to computing without the cache."""
    try:
        key = _key(endpoint, scope_token(user), filters)
        hit = cache.get(key)
        if hit is not None:
            return hit
    except Exception:
        return build()
    value = build()
    try:
        cache.set(key, value, _TTL)
    except Exception:
        pass
    return value
