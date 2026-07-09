"""Commit — create sessions/measurements/evaluations from valid rows; partial commit; re-commit
guard (BCKND-60)."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.measurements.models import TestSession
from apps.measurements.tests.import_helpers import (
    BATCH_DATE,
    IMPORTS,
    make_athlete,
    make_battery,
    row_for,
    seed_norms,
    unmatched_row,
    xlsx_upload,
)
from apps.scoring.models import Evaluation

pytestmark = pytest.mark.django_db


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _upload_validated(client, cat, exercises, rows, capture):
    with capture(execute=True):
        resp = client.post(
            IMPORTS,
            {"file": xlsx_upload(exercises, rows), "age_category": cat.id,
             "gender": "male", "date": str(BATCH_DATE)},
            format="multipart",
        )
    return resp.json()["id"]


def test_commit_creates_session_measurements_evaluation(django_capture_on_commit_callbacks):
    cat, exercises = make_battery()
    seed_norms(exercises)
    athlete = make_athlete()
    client = _client(UserFactory(role="super_admin"))
    batch_id = _upload_validated(client, cat, exercises, [row_for(athlete, exercises)],
                                 django_capture_on_commit_callbacks)
    resp = client.post(f"{IMPORTS}{batch_id}/commit/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "committed"
    session = TestSession.objects.get(athlete=athlete, source=TestSession.Source.EXCEL)
    assert session.status == TestSession.Status.FINALIZED
    assert session.measurements.count() == 5
    assert Evaluation.objects.filter(session=session).exists()


def test_commit_skips_error_rows(django_capture_on_commit_callbacks):
    cat, exercises = make_battery()
    seed_norms(exercises)
    athlete = make_athlete()
    rows = [row_for(athlete, exercises), unmatched_row(exercises)]  # 1 valid, 1 error
    client = _client(UserFactory(role="super_admin"))
    batch_id = _upload_validated(client, cat, exercises, rows, django_capture_on_commit_callbacks)
    client.post(f"{IMPORTS}{batch_id}/commit/")
    assert TestSession.objects.filter(source=TestSession.Source.EXCEL).count() == 1
    assert TestSession.objects.get(source=TestSession.Source.EXCEL).athlete_id == athlete.id


def test_recommit_is_409(django_capture_on_commit_callbacks):
    cat, exercises = make_battery()
    seed_norms(exercises)
    client = _client(UserFactory(role="super_admin"))
    batch_id = _upload_validated(client, cat, exercises, [row_for(make_athlete(), exercises)],
                                 django_capture_on_commit_callbacks)
    assert client.post(f"{IMPORTS}{batch_id}/commit/").status_code == 200
    assert client.post(f"{IMPORTS}{batch_id}/commit/").status_code == 409  # already committed


def test_unmatched_only_batch_commits_nothing(django_capture_on_commit_callbacks):
    cat, exercises = make_battery()
    seed_norms(exercises)
    client = _client(UserFactory(role="super_admin"))
    batch_id = _upload_validated(client, cat, exercises, [unmatched_row(exercises)],
                                 django_capture_on_commit_callbacks)
    resp = client.post(f"{IMPORTS}{batch_id}/commit/")
    assert resp.status_code == 200
    assert TestSession.objects.filter(source=TestSession.Source.EXCEL).count() == 0
