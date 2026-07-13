"""Ranking selectors — Postgres `RANK()` over the latest Evaluation per athlete (BCKND-49).

Ranking is computed, never stored. The partition is `(region, sport_type, age_category,
gender)` — no block (physical is block-independent; `sport_type` stays a partition dim so
"top athletes in a sport" is answerable). Only the latest Evaluation per athlete counts.
"""

from django.db.models import Avg, Count, F, Q, Window
from django.db.models.functions import Rank

from apps.common.scoping import scope_queryset
from apps.scoring.models import Evaluation

_PARTITION = [F("region_id"), F("sport_type_id"), F("age_category_id"), F("gender")]


def _latest_ids(date_range=None):
    """Ids of each athlete's most recent Evaluation (Postgres `DISTINCT ON`). Kept as a
    subquery so the outer window query has no `distinct()` (the two can't share a query).

    `date_range` (start, end) narrows `session_date` **before** the DISTINCT ON, so it selects
    the latest evaluation *within the period* — not the latest-overall then filtered (BCKND-70).
    """
    qs = Evaluation.objects.all()
    if date_range:
        qs = qs.filter(session_date__range=date_range)
    return qs.order_by("athlete_id", "-session_date", "-id").distinct("athlete_id").values("id")


def _scoped_latest(filters, user, date_range=None):
    """The latest-per-athlete set, narrowed by whitelisted filters and the user's scope.

    Scope is applied *before* the window: region is a partition dim so a region_admin's
    ranks stay correct; a coach ranks among their own athletes (permission matrix §2).
    """
    qs = Evaluation.objects.filter(id__in=_latest_ids(date_range))
    for field, value in filters.items():
        qs = qs.filter(**{field: value})
    return scope_queryset(
        qs,
        user,
        region_field="region_id",
        organization_field="session__organization_id",
        coach_field="athlete__coach",
    )


def ranked_athletes(filters, user, date_range=None):
    """Latest-per-athlete Evaluations ranked within the partition by `ranking_score` DESC.
    Ties share a rank (only the score is in the window order); display tiebreak = latest
    session date, then athlete name. `date_range` scopes to the latest within a period."""
    return (
        _scoped_latest(filters, user, date_range)
        .select_related("athlete")
        .annotate(
            rank=Window(
                expression=Rank(),
                partition_by=_PARTITION,
                order_by=F("ranking_score").desc(),
            )
        )
        .order_by("rank", "-session_date", "athlete__last_name", "athlete__first_name")
    )


def top_athletes(filters, user, limit=10, date_range=None):
    """The top `limit` ranked athletes for the (typically fully-specified) partition."""
    return ranked_athletes(filters, user, date_range)[:limit]


def region_rating(filters, user, date_range=None):
    """Per-region aggregation over the latest-per-athlete set: count of daraja-I athletes +
    average `ranking_score`, ranked by daraja-I count then average. Ranked in Python — region
    cardinality is tiny and a SQL window over a GROUP BY is fragile in the ORM."""
    rows = list(
        _scoped_latest(filters, user, date_range)
        .values("region_id", "region__name")
        .annotate(
            daraja_i_count=Count("id", filter=Q(daraja=Evaluation.Daraja.FIRST)),
            avg_score=Avg("ranking_score"),
        )
        .order_by("-daraja_i_count", "-avg_score")
    )
    for position, row in enumerate(rows, start=1):
        row["rank"] = position
    return rows
