from apps.common.permissions import (
    COACH,
    LAB_OPERATOR,
    MINISTRY,
    REGION_ADMIN,
    SUPER_ADMIN,
)


def scope_queryset(queryset, user, *, region_field=None, organization_field=None, coach_field=None):
    """Filter a queryset to the user's scope — enforced server-side, never trusting
    client filters (API.md §2).

    Field paths are passed by the caller so this stays model-agnostic. The
    ``User.region``/``User.organization`` fields are added in B3; until a scoped user
    actually has one assigned, that user resolves to an empty scope (deny by default).
    """
    if not (user and user.is_authenticated):
        return queryset.none()

    role = getattr(user, "role", None)
    if role in (SUPER_ADMIN, MINISTRY):
        return queryset
    if role == REGION_ADMIN and region_field:
        region_id = getattr(user, "region_id", None)
        return queryset.filter(**{region_field: region_id}) if region_id else queryset.none()
    if role == LAB_OPERATOR and organization_field:
        org_id = getattr(user, "organization_id", None)
        return queryset.filter(**{organization_field: org_id}) if org_id else queryset.none()
    if role == COACH and coach_field:
        return queryset.filter(**{coach_field: user})
    return queryset.none()


class ScopedQuerysetMixin:
    """ViewSet mixin: filters ``get_queryset()`` to the request user's scope.

    Set the field paths on the viewset, e.g.::

        scope_region_field = "region_id"
        scope_organization_field = "organization_id"
        scope_coach_field = "coach"

    A role with no applicable field path resolves to an empty scope. Object-level access
    falls out for free: ``get_object()`` uses this queryset, so an out-of-scope pk 404s.
    """

    scope_region_field = None
    scope_organization_field = None
    scope_coach_field = None

    def get_queryset(self):
        return scope_queryset(
            super().get_queryset(),
            self.request.user,
            region_field=self.scope_region_field,
            organization_field=self.scope_organization_field,
            coach_field=self.scope_coach_field,
        )
