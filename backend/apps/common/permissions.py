from rest_framework.permissions import BasePermission

# Role values mirror apps.accounts.models.Role. Kept as plain strings here so `common`
# stays dependency-free (it must not import the accounts app) — see BCKND-4.
SUPER_ADMIN = "super_admin"
REGION_ADMIN = "region_admin"
COACH = "coach"
LAB_OPERATOR = "lab_operator"
MINISTRY = "ministry"


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
