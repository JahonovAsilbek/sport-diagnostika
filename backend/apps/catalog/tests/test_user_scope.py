"""User region/organization per-role validation (BCKND-20), exercised via the users API.

Lives with the catalog tests because the scope FKs point at catalog models and use the
catalog factories.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.catalog.factories import OrganizationFactory, RegionFactory

pytestmark = pytest.mark.django_db

USERS = "/api/v1/users/"
PASSWORD = "StrongPw!2345"


def _admin_client():
    client = APIClient()
    client.force_authenticate(user=UserFactory(role="super_admin"))
    return client


def test_region_admin_without_region_is_400():
    resp = _admin_client().post(
        USERS,
        {"username": "ra1", "password": PASSWORD, "role": "region_admin"},
        format="json",
    )
    assert resp.status_code == 400
    assert "region" in resp.json()


def test_region_admin_with_region_is_created():
    region = RegionFactory()
    resp = _admin_client().post(
        USERS,
        {"username": "ra2", "password": PASSWORD, "role": "region_admin", "region": region.id},
        format="json",
    )
    assert resp.status_code == 201


def test_coach_without_organization_is_400():
    resp = _admin_client().post(
        USERS,
        {"username": "c1", "password": PASSWORD, "role": "coach"},
        format="json",
    )
    assert resp.status_code == 400
    assert "organization" in resp.json()


def test_coach_with_organization_is_created():
    org = OrganizationFactory()
    resp = _admin_client().post(
        USERS,
        {"username": "c2", "password": PASSWORD, "role": "coach", "organization": org.id},
        format="json",
    )
    assert resp.status_code == 201
