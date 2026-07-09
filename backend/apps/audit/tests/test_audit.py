"""Audit — diff capture, sensitive-field exclusion, actor+IP via the middleware, super_admin API."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.athletes.factories import AthleteFactory
from apps.audit.context import reset, set_actor
from apps.audit.models import AuditLog
from apps.catalog.factories import OrganizationFactory, RegionFactory, SportTypeFactory

pytestmark = pytest.mark.django_db

AUDIT = "/api/v1/audit/"
ATHLETES = "/api/v1/athletes/"


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


# --- diff capture (ORM under a bound actor) ----------------------------------------


def test_create_logs_a_snapshot():
    actor = UserFactory(role="super_admin")
    token = set_actor(user=actor, ip="1.1.1.1")
    try:
        athlete = AthleteFactory(last_name="Aliyev")
    finally:
        reset(token)
    log = AuditLog.objects.get(entity_type="athlete", action="created", entity_id=str(athlete.id))
    assert log.user_id == actor.id
    assert log.ip == "1.1.1.1"
    assert log.changes["last_name"] == "Aliyev"


def test_update_logs_only_changed_fields():
    athlete = AthleteFactory(razryad="")
    token = set_actor(user=UserFactory(role="super_admin"))
    try:
        athlete.razryad = "KMS"
        athlete.save()
    finally:
        reset(token)
    log = AuditLog.objects.filter(entity_type="athlete", action="updated").latest("created_at")
    assert log.changes["razryad"] == ["", "KMS"]
    assert "last_name" not in log.changes  # unchanged fields aren't logged


def test_user_password_and_last_login_never_logged_but_role_is():
    token = set_actor(user=UserFactory(role="super_admin"))
    try:
        user = UserFactory(role="coach")
        user.set_password("s3cret-value")
        user.is_staff = True
        user.save()
    finally:
        reset(token)
    for log in AuditLog.objects.filter(entity_type="user"):
        assert "password" not in log.changes
        assert "last_login" not in log.changes
    update = AuditLog.objects.filter(entity_type="user", action="updated").latest("created_at")
    assert "is_staff" in update.changes  # privilege changes ARE captured


def test_auditlog_is_not_self_audited():
    token = set_actor(user=UserFactory(role="super_admin"))
    try:
        AthleteFactory()
    finally:
        reset(token)
    assert AuditLog.objects.filter(entity_type="auditlog").count() == 0


def test_off_request_write_has_no_actor():
    AthleteFactory(last_name="Anon")  # no bound actor (like a Celery task)
    log = AuditLog.objects.filter(entity_type="athlete", action="created").latest("created_at")
    assert log.user_id is None


# --- actor + IP via the real middleware (the JWT lazy-user path) --------------------


def test_api_mutation_records_actor_and_forwarded_ip(settings):
    settings.AUDIT_TRUST_X_FORWARDED_FOR = True
    actor = UserFactory(role="super_admin")
    region = RegionFactory()
    payload = {
        "last_name": "Test",
        "first_name": "A",
        "birth_year": 2012,
        "gender": "male",
        "region": region.id,
        "organization": OrganizationFactory(region=region).id,
        "sport_type": SportTypeFactory().id,
    }
    resp = _client(actor).post(
        ATHLETES, payload, format="json", HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.1"
    )
    assert resp.status_code == 201, resp.json()
    log = AuditLog.objects.get(entity_type="athlete", entity_id=str(resp.json()["id"]))
    assert log.action == "created"
    assert log.user_id == actor.id  # resolved lazily after DRF auth (crux)
    assert log.ip == "203.0.113.7"


# --- read API ----------------------------------------------------------------------


def test_audit_endpoint_is_super_admin_only():
    for role in ("coach", "region_admin", "lab_operator", "ministry"):
        assert _client(UserFactory(role=role)).get(AUDIT).status_code == 403
    assert _client(UserFactory(role="super_admin")).get(AUDIT).status_code == 200


def test_audit_endpoint_filters_by_entity_type():
    token = set_actor(user=UserFactory(role="super_admin"))
    try:
        AthleteFactory()
    finally:
        reset(token)
    resp = _client(UserFactory(role="super_admin")).get(AUDIT, {"entity_type": "athlete"})
    assert resp.status_code == 200
    assert all(row["entity_type"] == "athlete" for row in resp.json()["results"])
