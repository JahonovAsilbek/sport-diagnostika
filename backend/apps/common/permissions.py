from rest_framework.permissions import SAFE_METHODS, BasePermission

# Role values mirror apps.accounts.models.Role. Kept as plain strings here so `common`
# stays dependency-free (it must not import the accounts app) — see BCKND-4.
SUPER_ADMIN = "super_admin"
REGION_ADMIN = "region_admin"
COACH = "coach"
LAB_OPERATOR = "lab_operator"
MINISTRY = "ministry"

# Roles that may write scoped data entities (athletes, sessions, …). ministry is
# read-only oversight; the actual row-level scope is enforced separately (scoping.py).
DATA_ENTRY_ROLES = frozenset({SUPER_ADMIN, REGION_ADMIN, COACH, LAB_OPERATOR})


def role_required(*roles):
    """Permission factory: an authenticated user whose ``role`` is one of ``roles``.

    Pure (no DB) so it is cheap per request; a missing/blank role is denied.
    """

    class RoleRequired(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            return bool(
                user and user.is_authenticated and getattr(user, "role", None) in roles
            )

    return RoleRequired


# Convenience classes keyed off the role values (API.md §2 capability matrix).
IsSuperAdmin = role_required(SUPER_ADMIN)
IsRegionAdmin = role_required(REGION_ADMIN)
IsCoach = role_required(COACH)
IsLabOperator = role_required(LAB_OPERATOR)
IsMinistry = role_required(MINISTRY)

# Users are administered by super_admin, and by region_admin within their region (B3).
IsUserAdmin = role_required(SUPER_ADMIN, REGION_ADMIN)


class DataEntryOrReadOnly(BasePermission):
    """Read for any authenticated user (the queryset is scope-filtered elsewhere); write
    for the data-entry roles only (API.md capability matrix). Shared by the scoped data
    ViewSets (athletes, measurements, …) so the read/write split lives in one place."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(user, "role", None) in DATA_ENTRY_ROLES

    def has_object_permission(self, request, view, obj):
        # The scoped get_queryset already 404s an out-of-scope pk before this runs;
        # re-affirm the read/write capability split for defense-in-depth.
        return self.has_permission(request, view)
