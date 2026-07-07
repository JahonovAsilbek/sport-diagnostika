from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super admin"
    REGION_ADMIN = "region_admin", "Viloyat admin"
    COACH = "coach", "Murabbiy"
    LAB_OPERATOR = "lab_operator", "Laboratoriya operatori"
    MINISTRY = "ministry", "Vazirlik vakili"


class User(AbstractUser):
    """Custom user model.

    The region/organization scope FKs are added in B3 (they reference catalog models).
    It exists this early so a swappable user model is in place before the first migrate.
    Inherits ``__str__`` (the username) from ``AbstractBaseUser``.
    """

    phone = models.CharField(max_length=32, blank=True)
    # Least-privilege default so a mis-created user can't land as an admin.
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.LAB_OPERATOR)
