from rest_framework.permissions import BasePermission


def role_required(*roles):
    """Permission factory: an authenticated user whose ``role`` is one of ``roles``.

    ``role`` is added to the User in B2; until then this is only a string comparison
    via ``getattr``, so importing this early creates no import cycle.
    """

    class RoleRequired(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            return bool(
                user and user.is_authenticated and getattr(user, "role", None) in roles
            )

    return RoleRequired


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, "role", None) == "super_admin"
        )
