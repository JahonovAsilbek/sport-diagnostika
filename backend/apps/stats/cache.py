"""Per-user scope token for the stats cache key — the same lesson as B8 rating: without it two
region_admins with different scopes would share a cached result and leak counts across regions.
A tiny local copy avoids a stats→rating coupling for one helper."""
from apps.common.permissions import COACH, LAB_OPERATOR, MINISTRY, REGION_ADMIN, SUPER_ADMIN


def scope_token(user):
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
