"""Ranking selectors — order, ties, latest-per-athlete, top-N, region aggregation (BCKND-49)."""
from datetime import date

import pytest

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import AgeCategoryFactory, RegionFactory, SportTypeFactory
from apps.rating.selectors import ranked_athletes, region_rating, top_athletes
from apps.rating.tests.helpers import make_eval, make_partition, partition_filters

pytestmark = pytest.mark.django_db


def _super():
    return UserFactory(role="super_admin")


def test_ranked_orders_by_score_desc():
    partition = make_partition()
    make_eval(partition, 30)
    make_eval(partition, 50)
    make_eval(partition, 42)
    rows = list(ranked_athletes(partition_filters(partition), _super()))
    assert [row.ranking_score for row in rows] == [50, 42, 30]
    assert [row.rank for row in rows] == [1, 2, 3]


def test_ties_share_a_rank():
    partition = make_partition()
    make_eval(partition, 42)
    make_eval(partition, 42)
    make_eval(partition, 30)
    rows = list(ranked_athletes(partition_filters(partition), _super()))
    assert [row.rank for row in rows] == [1, 1, 3]  # RANK(): the two 42s tie, next is 3


def test_only_latest_evaluation_per_athlete_counts():
    partition = make_partition()
    athlete = AthleteFactory()
    make_eval(partition, 20, athlete=athlete, session_date=date(2026, 1, 1))
    make_eval(partition, 48, athlete=athlete, session_date=date(2026, 6, 1))
    make_eval(partition, 40)  # a different athlete for context
    rows = list(ranked_athletes(partition_filters(partition), _super()))
    scores = [row.ranking_score for row in rows]
    assert 20 not in scores  # the older evaluation is excluded
    assert scores == [48, 40]


def test_top_n_limits_results():
    partition = make_partition()
    for score in range(1, 16):
        make_eval(partition, score)
    rows = list(top_athletes(partition_filters(partition), _super(), limit=10))
    assert len(rows) == 10
    assert rows[0].ranking_score == 15  # highest first


def test_different_partitions_rank_independently():
    sport, category = SportTypeFactory(), AgeCategoryFactory()
    region_a, region_b = RegionFactory(), RegionFactory()
    pa = {"region": region_a, "sport_type": sport, "age_category": category, "gender": "male"}
    pb = {"region": region_b, "sport_type": sport, "age_category": category, "gender": "male"}
    make_eval(pa, 30)
    make_eval(pb, 50)
    # No region filter → both partitions present, each ranked from 1 within its own partition.
    rows = ranked_athletes({"sport_type_id": sport.id, "age_category_id": category.id}, _super())
    assert {row.rank for row in rows} == {1}


def test_region_rating_counts_daraja_i_and_avg():
    sport, category = SportTypeFactory(), AgeCategoryFactory()
    region_a, region_b = RegionFactory(), RegionFactory()
    pa = {"region": region_a, "sport_type": sport, "age_category": category, "gender": "male"}
    pb = {"region": region_b, "sport_type": sport, "age_category": category, "gender": "male"}
    make_eval(pa, 50, daraja="I", color="green")
    make_eval(pa, 48, daraja="I", color="green")
    make_eval(pa, 30, daraja="III", color="red")
    make_eval(pb, 50, daraja="I", color="green")
    rows = region_rating({"sport_type_id": sport.id, "age_category_id": category.id}, _super())
    assert rows[0]["region__name"] == region_a.name
    assert rows[0]["daraja_i_count"] == 2
    assert rows[0]["rank"] == 1
    assert rows[1]["daraja_i_count"] == 1
    assert rows[1]["rank"] == 2
