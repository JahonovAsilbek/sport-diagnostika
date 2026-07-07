from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model.

    Minimal for now — the ``role`` field and the region/organization scope FKs are
    added in B2 and the catalog phase. It exists this early so a swappable user model
    is in place before the first migrate (swapping ``AUTH_USER_MODEL`` afterwards is
    painful). Inherits ``__str__`` (the username) from ``AbstractBaseUser``.
    """

    phone = models.CharField(max_length=32, blank=True)
