"""Shared rating fixtures (helpers, not a test module). Builds Evaluations placed in a chosen
`(region, sport_type, age_category, gender)` partition with a given ranking_score, so ranking/
cache tests can compose leaderboards without going through the whole finalize pipeline."""

from datetime import date

from apps.catalog.factories import AgeCategoryFactory, RegionFactory, SportTypeFactory
from apps.measurements.factories import TestSessionFactory
from apps.scoring.factories import EvaluationFactory

DEFAULT_DATE = date(2026, 6, 1)


def make_partition(gender="male"):
    """A fresh `(region, sport_type, age_category, gender)` partition (model instances)."""
    return {
        "region": RegionFactory(),
        "sport_type": SportTypeFactory(),
        "age_category": AgeCategoryFactory(),
        "gender": gender,
    }


def partition_filters(partition):
    """The partition as selector filter kwargs (ids/strings)."""
    return {
        "region_id": partition["region"].id,
        "sport_type_id": partition["sport_type"].id,
        "age_category_id": partition["age_category"].id,
        "gender": partition["gender"],
    }


def partition_query(partition):
    """The partition as API query params (PKs)."""
    return {
        "region": partition["region"].id,
        "sport_type": partition["sport_type"].id,
        "age_category": partition["age_category"].id,
        "gender": partition["gender"],
    }


def make_eval(
    partition, score, *, athlete=None, session_date=DEFAULT_DATE, daraja=None, color=None
):
    """One Evaluation in `partition` with `ranking_score == physical_total == score`. A fresh
    athlete each call unless `athlete` is given (pass the same athlete twice to test
    latest-per-athlete)."""
    kwargs = dict(partition)
    kwargs.update(ranking_score=score, physical_total=score, session_date=session_date)
    if daraja is not None:
        kwargs["daraja"] = daraja
    if color is not None:
        kwargs["color"] = color
    if athlete is not None:
        kwargs["session"] = TestSessionFactory(athlete=athlete, date=session_date)
    return EvaluationFactory(**kwargs)
