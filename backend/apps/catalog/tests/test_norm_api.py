from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.catalog.factories import (
    DarajaThresholdFactory,
    ExerciseFactory,
    NormBandFactory,
    NormFactory,
)
from apps.catalog.models import Norm
from apps.common.models import Gender

pytestmark = pytest.mark.django_db

NORMS = "/api/v1/catalog/norms/"
DARAJA = "/api/v1/catalog/daraja-thresholds/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _band(points, lower, upper):
    return {"points": points, "lower_bound": lower, "upper_bound": upper}


def _norm_payload(exercise, bands, **overrides):
    payload = {
        "exercise": exercise.id,
        "age_min": 14,
        "age_max": 14,
        "gender": "male",
        "valid_from": "2026-01-01",
        "is_active": True,
        "bands": bands,
    }
    payload.update(overrides)
    return payload


# --- write: super_admin only -------------------------------------------------------


def test_super_admin_creates_norm_with_nested_bands():
    ex = ExerciseFactory()
    bands = [_band(10, "14.0", "14.3"), _band(8, "14.3", "14.6"), _band(6, "14.6", "14.9")]
    resp = _client(UserFactory(role="super_admin")).post(
        NORMS, _norm_payload(ex, bands), format="json"
    )
    assert resp.status_code == 201, resp.content
    norm = Norm.objects.get()
    assert norm.bands.count() == 3
    body = resp.json()
    # exercise is nested on read (API.md §4).
    assert body["exercise"]["id"] == ex.id
    assert len(body["bands"]) == 3


def test_create_norm_with_overlapping_bands_is_400_and_rolls_back():
    ex = ExerciseFactory()
    bands = [_band(10, "14.0", "14.5"), _band(8, "14.3", "14.9")]  # overlap
    resp = _client(UserFactory(role="super_admin")).post(
        NORMS, _norm_payload(ex, bands), format="json"
    )
    assert resp.status_code == 400
    # Atomic: the norm and its bands must not persist.
    assert not Norm.objects.exists()


def test_super_admin_update_replaces_band_set():
    norm = NormFactory()
    NormBandFactory(norm=norm, points=10, lower_bound=Decimal("0"), upper_bound=Decimal("5"))
    bands = [_band(10, "0", "10"), _band(8, "10", "20")]
    resp = _client(UserFactory(role="super_admin")).put(
        f"{NORMS}{norm.id}/",
        _norm_payload(
            norm.exercise,
            bands,
            age_min=norm.age_min,
            age_max=norm.age_max,
            gender=norm.gender,
            valid_from=str(norm.valid_from),
        ),
        format="json",
    )
    assert resp.status_code == 200, resp.content
    norm.refresh_from_db()
    assert set(norm.bands.values_list("points", flat=True)) == {10, 8}


def test_coach_cannot_write_norm_is_403():
    ex = ExerciseFactory()
    resp = _client(UserFactory(role="coach")).post(
        NORMS, _norm_payload(ex, [_band(10, "14.0", "14.3")]), format="json"
    )
    assert resp.status_code == 403
    assert not Norm.objects.exists()


# --- read + filters ----------------------------------------------------------------


def test_coach_can_read_norm_detail_with_nested_bands():
    norm = NormFactory()
    NormBandFactory(norm=norm, points=10, lower_bound=Decimal("0"), upper_bound=Decimal("10"))
    NormBandFactory(norm=norm, points=8, lower_bound=Decimal("10"), upper_bound=Decimal("20"))
    resp = _client(UserFactory(role="coach")).get(f"{NORMS}{norm.id}/")
    assert resp.status_code == 200
    assert {b["points"] for b in resp.json()["bands"]} == {10, 8}


def test_norms_filtered_by_exercise_and_gender():
    ex1, ex2 = ExerciseFactory(), ExerciseFactory()
    NormFactory(exercise=ex1, gender=Gender.MALE, age_min=14, age_max=14)
    NormFactory(exercise=ex1, gender=Gender.FEMALE, age_min=14, age_max=14)
    NormFactory(exercise=ex2, gender=Gender.MALE, age_min=14, age_max=14)
    resp = _client(UserFactory(role="coach")).get(NORMS, {"exercise": ex1.id, "gender": "male"})
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["exercise"]["id"] == ex1.id


# --- daraja thresholds: read-only --------------------------------------------------


def test_daraja_thresholds_read_only():
    DarajaThresholdFactory(level="I", total_min=48, total_max=50)
    assert _client(UserFactory(role="coach")).get(DARAJA).status_code == 200
    # Read-only viewset: even a super_admin (who clears the permission) gets no write route.
    resp = _client(UserFactory(role="super_admin")).post(
        DARAJA, {"level": "II", "total_min": 38, "total_max": 46}, format="json"
    )
    assert resp.status_code == 405
