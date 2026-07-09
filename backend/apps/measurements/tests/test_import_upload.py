"""Upload → async validation: valid/error rows, security limits, sanitize, idempotency, scoping."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.catalog.factories import AgeCategoryFactory, OrganizationFactory, RegionFactory
from apps.measurements.import_services import sanitize_cell
from apps.measurements.models import ImportRow
from apps.measurements.tasks import validate_import_batch
from apps.measurements.tests.import_helpers import (
    BATCH_DATE,
    IMPORTS,
    make_athlete,
    make_battery,
    row_for,
    unmatched_row,
    xlsx_upload,
)

pytestmark = pytest.mark.django_db


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _upload(client, cat, upload, capture, gender="male"):
    with capture(execute=True):
        return client.post(
            IMPORTS,
            {"file": upload, "age_category": cat.id, "gender": gender, "date": str(BATCH_DATE)},
            format="multipart",
        )


def test_upload_validates_a_matching_row(django_capture_on_commit_callbacks):
    cat, exercises = make_battery()
    athlete = make_athlete()
    client = _client(UserFactory(role="super_admin"))
    resp = _upload(client, cat, xlsx_upload(exercises, [row_for(athlete, exercises)]),
                   django_capture_on_commit_callbacks)
    assert resp.status_code == 201
    detail = client.get(f"{IMPORTS}{resp.json()['id']}/").json()
    assert detail["status"] == "validated"
    assert (detail["row_count"], detail["error_count"]) == (1, 0)
    assert detail["rows"][0]["status"] == "valid"
    assert detail["rows"][0]["athlete"] == athlete.id


def test_upload_reports_mixed_valid_and_error_rows(django_capture_on_commit_callbacks):
    cat, exercises = make_battery()
    athlete = make_athlete()
    rows = [row_for(athlete, exercises), unmatched_row(exercises)]
    client = _client(UserFactory(role="super_admin"))
    resp = _upload(client, cat, xlsx_upload(exercises, rows), django_capture_on_commit_callbacks)
    detail = client.get(f"{IMPORTS}{resp.json()['id']}/").json()
    assert (detail["row_count"], detail["error_count"]) == (2, 1)
    statuses = {row["status"] for row in detail["rows"]}
    assert statuses == {"valid", "error"}


def test_age_category_mismatch_is_error_row(django_capture_on_commit_callbacks):
    # The athlete matches by name, but their real TOIFA (age 16) differs from the batch's
    # template group (age 14) → the 5 columns aren't this athlete's battery → row error.
    cat, exercises = make_battery(age=14)
    AgeCategoryFactory(age_min=16, age_max=16)  # a category the athlete's age maps to
    athlete = make_athlete(birth_year=2010)  # 16 at BATCH_DATE
    client = _client(UserFactory(role="super_admin"))
    resp = _upload(client, cat, xlsx_upload(exercises, [row_for(athlete, exercises)]),
                   django_capture_on_commit_callbacks)
    row = client.get(f"{IMPORTS}{resp.json()['id']}/").json()["rows"][0]
    assert row["status"] == "error"
    assert any(err["field"] == "age_category" for err in row["errors"])


def test_upload_rejects_non_xlsx():
    cat, _ = make_battery()
    bad = SimpleUploadedFile("results.txt", b"not excel", content_type="text/plain")
    resp = _client(UserFactory(role="super_admin")).post(
        IMPORTS, {"file": bad, "age_category": cat.id, "gender": "male"}, format="multipart"
    )
    assert resp.status_code == 400


def test_upload_rejects_oversize_file(settings):
    settings.MAX_IMPORT_FILE_SIZE = 100  # any real .xlsx exceeds this
    cat, exercises = make_battery()
    upload = xlsx_upload(exercises, [row_for(make_athlete(), exercises)])
    resp = _client(UserFactory(role="super_admin")).post(
        IMPORTS, {"file": upload, "age_category": cat.id, "gender": "male"}, format="multipart"
    )
    assert resp.status_code == 400


@pytest.mark.parametrize("value,expected", [
    ("=cmd()", "'=cmd()"),   # a text cell whose value starts with a formula char
    ("+1+1", "'+1+1"),
    ("-2", "'-2"),
    ("@SUM(A1)", "'@SUM(A1)"),
    ("Aliyev", "Aliyev"),    # ordinary text is untouched
    (14, 14),                # numbers pass through
])
def test_sanitize_cell_neutralizes_formula_injection(value, expected):
    # openpyxl reads cached VALUES (data_only=True), so a genuine formula never yields a
    # formula string; the vector is a plain text cell whose value starts with = + - @, which
    # the user's Excel would execute on re-export. sanitize_cell prefixes it with '.
    assert sanitize_cell(value) == expected


def test_revalidation_does_not_duplicate_rows(django_capture_on_commit_callbacks):
    cat, exercises = make_battery()
    client = _client(UserFactory(role="super_admin"))
    resp = _upload(client, cat, xlsx_upload(exercises, [row_for(make_athlete(), exercises)]),
                   django_capture_on_commit_callbacks)
    batch_id = resp.json()["id"]
    validate_import_batch(batch_id)  # re-run directly (eager)
    assert ImportRow.objects.filter(batch_id=batch_id).count() == 1


def test_batch_visible_only_to_uploader(django_capture_on_commit_callbacks):
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    coach_a = UserFactory(role="coach", organization=org)
    coach_b = UserFactory(role="coach", organization=org)
    cat, exercises = make_battery()
    athlete = make_athlete(coach=coach_a, organization=org, region=region)
    resp = _upload(_client(coach_a), cat, xlsx_upload(exercises, [row_for(athlete, exercises)]),
                   django_capture_on_commit_callbacks)
    batch_id = resp.json()["id"]
    assert _client(coach_b).get(IMPORTS).json()["count"] == 0
    assert _client(coach_b).get(f"{IMPORTS}{batch_id}/").status_code == 404
