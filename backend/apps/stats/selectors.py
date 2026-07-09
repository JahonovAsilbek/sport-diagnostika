"""Dashboard aggregates (BCKND-66, API §12) — DB-side counts, all scoped to the requester."""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.athletes.models import Athlete
from apps.catalog.models import Organization, Region
from apps.common.permissions import MINISTRY, SUPER_ADMIN
from apps.common.scoping import scope_queryset
from apps.measurements.models import TestSession
from apps.scoring.models import Evaluation

RECENT_DAYS = 30
_DARAJA_KEYS = [
    Evaluation.Daraja.FIRST.value,
    Evaluation.Daraja.SECOND.value,
    Evaluation.Daraja.THIRD.value,
    Evaluation.Daraja.NONE.value,
]
_ORG_TYPES = [Organization.Type.OTM.value, Organization.Type.OPSTTM.value]


def _latest_eval_ids():
    """Latest Evaluation per athlete (Postgres DISTINCT ON) — the current-standing set."""
    return (
        Evaluation.objects.order_by("athlete_id", "-session_date", "-id")
        .distinct("athlete_id")
        .values("id")
    )


def overview(user):
    athletes = scope_queryset(
        Athlete.objects.filter(is_active=True),
        user,
        region_field="region_id",
        organization_field="organization_id",
        coach_field="coach",
    )
    evaluations = scope_queryset(
        Evaluation.objects.filter(id__in=_latest_eval_ids()),
        user,
        region_field="region_id",
        organization_field="session__organization_id",
        coach_field="athlete__coach",
    )
    sessions = scope_queryset(
        TestSession.objects.all(),
        user,
        region_field="region_id",
        organization_field="organization_id",
        coach_field="athlete__coach",
    )

    by_org = {key: 0 for key in _ORG_TYPES}
    for row in athletes.values("organization__type").annotate(n=Count("id")):
        if row["organization__type"] in by_org:
            by_org[row["organization__type"]] = row["n"]

    by_daraja = {key: 0 for key in _DARAJA_KEYS}
    for row in evaluations.values("daraja").annotate(n=Count("id")):
        if row["daraja"] in by_daraja:
            by_daraja[row["daraja"]] = row["n"]

    if getattr(user, "role", None) in (SUPER_ADMIN, MINISTRY):
        regions = Region.objects.count()
    else:
        regions = athletes.values("region_id").distinct().count()

    recent = sessions.filter(date__gte=timezone.localdate() - timedelta(days=RECENT_DAYS)).count()

    return {
        "athletes_total": athletes.count(),
        "by_organization_type": by_org,
        "by_daraja": by_daraja,
        "regions": regions,
        "recent_sessions": recent,
    }
