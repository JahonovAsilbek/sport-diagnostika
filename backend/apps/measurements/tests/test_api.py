"""Test-session API — auth, create/snapshot, battery, measurements, finalize, and the
draft-only editability rules (B6). Postgres test DB; run with --reuse-db."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    DarajaThresholdFactory,
    ExerciseFactory,
    NormBandFactory,
    NormFactory,
    TestBatteryFactory,
)
from apps.catalog.models import Exercise
from apps.measurements.factories import TestSessionFactory
from apps.measurements.models import Measurement, TestSession
from apps.scoring.models import Evaluation

pytestmark = pytest.mark.django_db

SESSIONS = "/api/v1/sessions/"
SESSION_DATE = "2026-06-01"  # an athlete born 2012 is age 14 on this date
RAW_VALUES = ["14.4", "1:22", "9", "-3", "13"]


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _covered_athlete(**kwargs):
    """An athlete aged 14 at SESSION_DATE plus a TOIFA category that covers age 14, so
    `open_session` can resolve an `age_category` on create."""
    AgeCategoryFactory(age_min=14, age_max=14)
    return AthleteFactory(birth_year=2012, **kwargs)


def _battery_complete_session(**session_kwargs):
    """A draft session wired to the ordered 5-exercise battery for its (age_category,
    gender). Returns (session, exercises) in battery order."""
    session = TestSessionFactory(**session_kwargs)
    battery = TestBatteryFactory(age_category=session.age_category, gender=session.gender)
    value_types = [
        Exercise.ValueType.SECONDS, Exercise.ValueType.MINSEC, Exercise.ValueType.COUNT,
        Exercise.ValueType.CM_SIGNED, Exercise.ValueType.COUNT,
    ]
    exercises = [ExerciseFactory(value_type=vt) for vt in value_types]
    for order, exercise in enumerate(exercises, start=1):
        BatteryItemFactory(battery=battery, exercise=exercise, order=order)
    return session, exercises


def _measurements_body(exercises):
    return {"measurements": [
        {"exercise": ex.id, "raw_value": v}
        for ex, v in zip(exercises, RAW_VALUES, strict=True)
    ]}


def _seed_norms(session, exercises):
    """Seed a norm (one 8-point band spanning every RAW_VALUE) per battery exercise for the
    session's age×gender, plus the three daraja thresholds — so finalize scores 5×8 = 40 →
    II daraja instead of blocking on an unscored indicator (B7 wires scoring into finalize)."""
    age = session.date.year - session.athlete.birth_year
    for exercise in exercises:
        norm = NormFactory(
            exercise=exercise, gender=session.gender, age_min=age, age_max=age
        )
        NormBandFactory(
            norm=norm, points=8, lower_bound=Decimal("-100"), upper_bound=Decimal("1000")
        )
    DarajaThresholdFactory(level="I", total_min=48, total_max=50)
    DarajaThresholdFactory(level="II", total_min=38, total_max=46)
    DarajaThresholdFactory(level="III", total_min=30, total_max=36)


# --- auth --------------------------------------------------------------------------

def test_unauthenticated_list_is_401():
    assert _client().get(SESSIONS).status_code == 401


def test_unauthenticated_create_is_401():
    athlete = _covered_athlete()
    body = {"athlete": athlete.id, "date": SESSION_DATE}
    assert _client().post(SESSIONS, body, format="json").status_code == 401


# --- create / snapshot -------------------------------------------------------------

def test_super_admin_create_snapshots_dims():
    cat = AgeCategoryFactory(age_min=14, age_max=14)
    athlete = AthleteFactory(birth_year=2012)
    user = UserFactory(role="super_admin")
    body = {"athlete": athlete.id, "date": SESSION_DATE, "height_cm": 178, "weight_kg": 70}
    resp = _client(user).post(SESSIONS, body, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["age_category"] == cat.id
    assert data["gender"] == athlete.gender
    assert data["region"] == athlete.region_id
    assert data["organization"] == athlete.organization_id
    assert data["sport_type"] == athlete.sport_type_id
    assert data["entered_by"] == user.id


def test_create_without_covering_age_category_is_400():
    AgeCategoryFactory(age_min=10, age_max=12)  # does not cover age 14
    athlete = AthleteFactory(birth_year=2012)
    body = {"athlete": athlete.id, "date": SESSION_DATE}
    resp = _client(UserFactory(role="super_admin")).post(SESSIONS, body, format="json")
    assert resp.status_code == 400


def test_ministry_create_is_403():
    athlete = _covered_athlete()
    body = {"athlete": athlete.id, "date": SESSION_DATE}
    resp = _client(UserFactory(role="ministry")).post(SESSIONS, body, format="json")
    assert resp.status_code == 403


# --- battery action ----------------------------------------------------------------

def test_battery_action_returns_five_ordered_items():
    session, exercises = _battery_complete_session()
    resp = _client(UserFactory(role="super_admin")).get(f"{SESSIONS}{session.id}/battery/")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 5
    assert [item["order"] for item in items] == [1, 2, 3, 4, 5]
    assert [item["exercise"]["id"] for item in items] == [ex.id for ex in exercises]


def test_battery_action_without_battery_is_400():
    session = TestSessionFactory()
    resp = _client(UserFactory(role="super_admin")).get(f"{SESSIONS}{session.id}/battery/")
    assert resp.status_code == 400


# --- measurements action -----------------------------------------------------------

def test_measurements_action_stores_the_battery():
    session, exercises = _battery_complete_session()
    resp = _client(UserFactory(role="super_admin")).post(
        f"{SESSIONS}{session.id}/measurements/", _measurements_body(exercises), format="json"
    )
    assert resp.status_code == 200
    assert session.measurements.count() == 5
    minsec = Measurement.objects.get(session=session, exercise=exercises[1])
    assert minsec.raw_value == Decimal("82.00")  # "1:22" → 82 seconds


def test_measurements_action_rejects_exercise_outside_battery():
    session, _ = _battery_complete_session()
    stray = ExerciseFactory(value_type=Exercise.ValueType.COUNT)
    body = {"measurements": [{"exercise": stray.id, "raw_value": "5"}]}
    resp = _client(UserFactory(role="super_admin")).post(
        f"{SESSIONS}{session.id}/measurements/", body, format="json"
    )
    assert resp.status_code == 400


# --- finalize action ---------------------------------------------------------------

def test_finalize_complete_battery_scores_and_finalizes():
    session, exercises = _battery_complete_session()
    _seed_norms(session, exercises)
    client = _client(UserFactory(role="super_admin"))
    assert client.post(
        f"{SESSIONS}{session.id}/measurements/", _measurements_body(exercises), format="json"
    ).status_code == 200
    resp = client.post(f"{SESSIONS}{session.id}/finalize/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "computed"
    assert body["evaluation_id"]
    assert body["physical_total"] == 40  # 5 × 8 points
    assert body["daraja"] == "II"
    assert len(body["indicators"]) == 5
    session.refresh_from_db()
    assert session.status == TestSession.Status.FINALIZED


def test_finalize_with_missing_measurement_is_400():
    session, exercises = _battery_complete_session()
    client = _client(UserFactory(role="super_admin"))
    partial = {"measurements": [
        {"exercise": ex.id, "raw_value": v}
        for ex, v in zip(exercises[:4], RAW_VALUES[:4], strict=True)
    ]}
    assert client.post(
        f"{SESSIONS}{session.id}/measurements/", partial, format="json"
    ).status_code == 200
    resp = client.post(f"{SESSIONS}{session.id}/finalize/")
    assert resp.status_code == 400
    assert "missing" in resp.json()


def test_finalize_with_missing_norm_is_400_and_rolls_back_to_draft():
    # Complete battery + measurements but NO seeded norms → every indicator is unscored.
    # finalize + scoring share one transaction, so the 400 must leave the session in draft.
    session, exercises = _battery_complete_session()
    client = _client(UserFactory(role="super_admin"))
    assert client.post(
        f"{SESSIONS}{session.id}/measurements/", _measurements_body(exercises), format="json"
    ).status_code == 200
    resp = client.post(f"{SESSIONS}{session.id}/finalize/")
    assert resp.status_code == 400
    assert "unscored" in resp.json()
    session.refresh_from_db()
    assert session.status == TestSession.Status.DRAFT  # rolled back
    assert not Evaluation.objects.filter(session=session).exists()


# --- draft-only editability --------------------------------------------------------

def test_patch_finalized_session_is_400():
    session = TestSessionFactory(status=TestSession.Status.FINALIZED)
    resp = _client(UserFactory(role="super_admin")).patch(
        f"{SESSIONS}{session.id}/", {"height_cm": 180}, format="json"
    )
    assert resp.status_code == 400


def test_measurements_on_finalized_session_is_400():
    session = TestSessionFactory(status=TestSession.Status.FINALIZED)
    body = {"measurements": [{"exercise": ExerciseFactory().id, "raw_value": "5"}]}
    resp = _client(UserFactory(role="super_admin")).post(
        f"{SESSIONS}{session.id}/measurements/", body, format="json"
    )
    assert resp.status_code == 400


def test_finalize_already_finalized_session_is_400():
    session = TestSessionFactory(status=TestSession.Status.FINALIZED)
    resp = _client(UserFactory(role="super_admin")).post(f"{SESSIONS}{session.id}/finalize/")
    assert resp.status_code == 400


def test_patch_draft_height_persists():
    session = TestSessionFactory()
    resp = _client(UserFactory(role="super_admin")).patch(
        f"{SESSIONS}{session.id}/", {"height_cm": 180}, format="json"
    )
    assert resp.status_code == 200
    session.refresh_from_db()
    assert session.height_cm == Decimal("180")
