import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()


@pytest.mark.django_db
def test_seed_admin_creates_super_admin():
    call_command("seed_admin", "--username", "root", "--password", "RootPw!23456")
    user = User.objects.get(username="root")
    assert user.is_superuser
    assert user.role == "super_admin"
    assert user.check_password("RootPw!23456")


@pytest.mark.django_db
def test_seed_admin_is_idempotent():
    call_command("seed_admin", "--username", "root", "--password", "RootPw!23456")
    call_command("seed_admin", "--username", "root", "--password", "different")
    assert User.objects.filter(username="root").count() == 1


@pytest.mark.django_db
def test_seed_admin_requires_password():
    with pytest.raises(CommandError):
        call_command("seed_admin", "--username", "root")
