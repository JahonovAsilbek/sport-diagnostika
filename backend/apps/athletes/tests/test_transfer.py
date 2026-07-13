"""Athlete assignment/transfer history — the one-open ledger invariant, the transfer service,
and the transfer/history endpoints (BCKND-68)."""

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AssignmentHistoryFactory, AthleteFactory
from apps.athletes.models import AthleteAssignmentHistory as History
from apps.athletes.services import open_initial_assignment, transfer_athlete
from apps.catalog.factories import OrganizationFactory, RegionFactory, SportTypeFactory
from apps.measurements.factories import TestSessionFactory

pytestmark = pytest.mark.django_db

ATHLETES = "/api/v1/athletes/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _payload(region, org, sport, **overrides):
    payload = {
        "last_name": "T",
        "first_name": "A",
        "birth_year": 2010,
        "gender": "male",
        "region": region.id,
        "organization": org.id,
        "sport_type": sport.id,
    }
    payload.update(overrides)
    return payload


def _open(athlete):
    return athlete.assignment_history.filter(valid_to__isnull=True)


# --- service -----------------------------------------------------------------------


def test_open_initial_assignment_mirrors_athlete():
    athlete = AthleteFactory()
    record = open_initial_assignment(athlete)
    assert record.valid_to is None
    assert record.region_id == athlete.region_id
    assert record.organization_id == athlete.organization_id
    assert _open(athlete).count() == 1


def test_transfer_closes_old_opens_new_and_syncs():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    old_org = athlete.organization
    new_org = OrganizationFactory(region=athlete.region)

    record = transfer_athlete(
        athlete,
        region=athlete.region,
        district=athlete.district,
        organization=new_org,
        sport_type=athlete.sport_type,
        coach=athlete.coach,
        changed_by=None,
        reason="Koʻchirish",
    )

    athlete.refresh_from_db()
    assert athlete.organization_id == new_org.id
    assert record.valid_to is None and record.organization_id == new_org.id
    # Exactly one open record; the old one is closed on the old org.
    assert _open(athlete).count() == 1
    closed = athlete.assignment_history.filter(valid_to__isnull=False).get()
    assert closed.organization_id == old_org.id and closed.valid_to is not None
    assert athlete.assignment_history.count() == 2


def test_transfer_noop_when_unchanged_writes_nothing():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    before = athlete.assignment_history.count()
    record = transfer_athlete(
        athlete,
        region=athlete.region,
        district=athlete.district,
        organization=athlete.organization,
        sport_type=athlete.sport_type,
        coach=athlete.coach,
        changed_by=None,
        reason="same",
    )
    assert record.valid_to is None
    assert athlete.assignment_history.count() == before  # nothing added


def test_second_open_record_violates_constraint():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AssignmentHistoryFactory(athlete=athlete)  # a second open record


# --- API: create + PATCH guard -----------------------------------------------------


def test_create_opens_one_initial_record():
    region = RegionFactory()
    org = OrganizationFactory(region=region)
    sport = SportTypeFactory()
    resp = _client(UserFactory(role="super_admin")).post(
        ATHLETES, _payload(region, org, sport), format="json"
    )
    assert resp.status_code == 201
    records = History.objects.filter(athlete_id=resp.json()["id"], valid_to__isnull=True)
    assert records.count() == 1
    assert records.get().organization_id == org.id


def test_patch_assignment_field_rejected():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    other_region = RegionFactory()
    resp = _client(UserFactory(role="super_admin")).patch(
        f"{ATHLETES}{athlete.id}/", {"region": other_region.id}, format="json"
    )
    assert resp.status_code == 400
    athlete.refresh_from_db()
    assert athlete.region_id != other_region.id  # unchanged


def test_patch_non_assignment_field_adds_no_history():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    resp = _client(UserFactory(role="super_admin")).patch(
        f"{ATHLETES}{athlete.id}/", {"razryad": "KMS"}, format="json"
    )
    assert resp.status_code == 200
    assert athlete.assignment_history.count() == 1


# --- API: transfer -----------------------------------------------------------------


def test_transfer_endpoint_moves_athlete():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    new_org = OrganizationFactory(region=athlete.region)
    resp = _client(UserFactory(role="super_admin")).post(
        f"{ATHLETES}{athlete.id}/transfer/",
        {"organization": new_org.id, "reason": "Koʻchdi"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["organization"] == new_org.id
    athlete.refresh_from_db()
    assert athlete.organization_id == new_org.id
    assert athlete.assignment_history.count() == 2
    assert _open(athlete).get().reason == "Koʻchdi"


def test_transfer_requires_reason():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    new_org = OrganizationFactory(region=athlete.region)
    resp = _client(UserFactory(role="super_admin")).post(
        f"{ATHLETES}{athlete.id}/transfer/", {"organization": new_org.id}, format="json"
    )
    assert resp.status_code == 400


def test_transfer_region_admin_out_of_scope_is_403():
    region_a, region_b = RegionFactory(), RegionFactory()
    athlete = AthleteFactory(region=region_a, organization=OrganizationFactory(region=region_a))
    open_initial_assignment(athlete)
    admin = UserFactory(role="region_admin", region=region_a)
    org_b = OrganizationFactory(region=region_b)
    resp = _client(admin).post(
        f"{ATHLETES}{athlete.id}/transfer/",
        {"region": region_b.id, "organization": org_b.id, "reason": "x"},
        format="json",
    )
    assert resp.status_code == 403
    athlete.refresh_from_db()
    assert athlete.region_id == region_a.id  # unchanged


# --- API: history ------------------------------------------------------------------


def test_history_newest_first():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    new_org = OrganizationFactory(region=athlete.region)
    transfer_athlete(
        athlete,
        region=athlete.region,
        district=athlete.district,
        organization=new_org,
        sport_type=athlete.sport_type,
        coach=athlete.coach,
        changed_by=None,
        reason="x",
    )
    resp = _client(UserFactory(role="super_admin")).get(f"{ATHLETES}{athlete.id}/history/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["valid_to"] is None  # the open (current) record leads
    assert data[1]["valid_to"] is not None


def test_history_out_of_scope_is_404():
    coach = UserFactory(role="coach", organization=OrganizationFactory())
    other = AthleteFactory()
    open_initial_assignment(other)
    assert _client(coach).get(f"{ATHLETES}{other.id}/history/").status_code == 404


# --- history-safety: past sessions keep their snapshot -----------------------------


def test_session_snapshot_unaffected_by_transfer():
    athlete = AthleteFactory()
    open_initial_assignment(athlete)
    session = TestSessionFactory(athlete=athlete)  # region snapshot = current region
    original_region = session.region_id
    new_region = RegionFactory()
    new_org = OrganizationFactory(region=new_region)

    transfer_athlete(
        athlete,
        region=new_region,
        district=None,
        organization=new_org,
        sport_type=athlete.sport_type,
        coach=athlete.coach,
        changed_by=None,
        reason="move",
    )

    session.refresh_from_db()
    assert session.region_id == original_region  # snapshot frozen
    athlete.refresh_from_db()
    assert athlete.region_id == new_region.id
