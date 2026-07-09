from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Report(TimeStampedModel):
    """An async report request. The worker builds the dataset (physical results/rankings) and
    renders it to the chosen format, saving the file to MEDIA; the client polls status then
    downloads when `done`."""

    class Type(models.TextChoices):
        ATHLETE = "athlete", "Sportchi"
        REGION = "region", "Viloyat"
        SPORT = "sport", "Sport turi"
        REPUBLIC = "republic", "Respublika"

    class Format(models.TextChoices):
        PDF = "pdf", "PDF"
        WORD = "word", "Word"
        EXCEL = "excel", "Excel"

    class Status(models.TextChoices):
        PENDING = "pending", "Navbatda"
        PROCESSING = "processing", "Ishlanmoqda"
        DONE = "done", "Tayyor"
        FAILED = "failed", "Xato"

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reports"
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    format = models.CharField(max_length=5, choices=Format.choices)
    params = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    file = models.FileField(upload_to="reports/", null=True, blank=True)
    error = models.TextField(blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Report #{self.pk} {self.type}/{self.format} ({self.status})"
