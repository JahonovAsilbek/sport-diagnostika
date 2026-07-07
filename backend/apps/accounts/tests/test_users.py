import pytest

from apps.accounts.factories import UserFactory


@pytest.mark.django_db
def test_superuser_created():
    user = UserFactory(is_staff=True, is_superuser=True)
    assert user.pk is not None
    assert user.is_superuser
    assert user.is_staff
    assert user.check_password("password123")
