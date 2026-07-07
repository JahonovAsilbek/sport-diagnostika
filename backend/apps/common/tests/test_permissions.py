from types import SimpleNamespace

import pytest

from apps.common.permissions import IsSuperAdmin, IsUserAdmin, role_required


def _request(role, authenticated=True):
    return SimpleNamespace(user=SimpleNamespace(role=role, is_authenticated=authenticated))


@pytest.mark.parametrize(
    "role,allowed",
    [
        ("super_admin", True),
        ("region_admin", True),
        ("coach", False),
        ("lab_operator", False),
        ("ministry", False),
        (None, False),
    ],
)
def test_is_user_admin_matrix(role, allowed):
    assert IsUserAdmin().has_permission(_request(role), None) is allowed


@pytest.mark.parametrize(
    "role,allowed",
    [("super_admin", True), ("region_admin", False), ("ministry", False)],
)
def test_is_super_admin_matrix(role, allowed):
    assert IsSuperAdmin().has_permission(_request(role), None) is allowed


def test_unauthenticated_is_denied():
    perm = role_required("super_admin")
    assert perm().has_permission(_request("super_admin", authenticated=False), None) is False
