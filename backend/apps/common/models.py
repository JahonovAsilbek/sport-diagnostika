from django.db import models


class Gender(models.TextChoices):
    """Shared across Athlete, TestBattery and Norm — one source of the gender values."""

    MALE = "male", "Erkak"
    FEMALE = "female", "Ayol"


class TimeStampedModel(models.Model):
    """Abstract base adding creation/update timestamps; most domain models inherit it."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
