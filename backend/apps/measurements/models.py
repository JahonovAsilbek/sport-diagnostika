from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import Gender, TimeStampedModel


class TestSession(TimeStampedModel):
    """One physical-battery testing occasion for an athlete. Carries snapshot ranking
    dims frozen at session-open time so a later transfer (BCKND-68) never rewrites
    historical/period rankings. `age_category` is the TOIFA computed at `date`."""

    class Source(models.TextChoices):
        MANUAL = "manual", "Qo'lda"
        EXCEL = "excel", "Excel"

    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        FINALIZED = "finalized", "Yakunlangan"

    athlete = models.ForeignKey(
        "athletes.Athlete", on_delete=models.PROTECT, related_name="sessions"
    )
    date = models.DateField(default=timezone.localdate)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entered_sessions"
    )
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    # Snapshot dims — frozen from the athlete at session open. No `block` (physical is
    # block-independent; Organization.type stays classification only).
    age_category = models.ForeignKey(
        "catalog.AgeCategory", on_delete=models.PROTECT, related_name="+"
    )
    gender = models.CharField(max_length=6, choices=Gender.choices)
    region = models.ForeignKey("catalog.Region", on_delete=models.PROTECT, related_name="+")
    organization = models.ForeignKey(
        "catalog.Organization", on_delete=models.PROTECT, related_name="+"
    )
    sport_type = models.ForeignKey(
        "catalog.SportType", on_delete=models.PROTECT, related_name="+"
    )

    # Nullable placeholders for future morpho work (BMI is deferred) — not on the athlete.
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.athlete} — {self.date} ({self.get_status_display()})"

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT


class Measurement(TimeStampedModel):
    """One raw result for one battery exercise. minsec is stored as seconds, signed
    flexibility as signed cm (the value_type parse happens at entry — services.py)."""

    session = models.ForeignKey(
        TestSession, on_delete=models.CASCADE, related_name="measurements"
    )
    exercise = models.ForeignKey(
        "catalog.Exercise", on_delete=models.PROTECT, related_name="+"
    )
    raw_value = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["session", "exercise"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "exercise"], name="uniq_measurement_per_exercise"
            ),
        ]

    def __str__(self):
        return f"{self.exercise} = {self.raw_value}"


class ImportBatch(TimeStampedModel):
    """A bulk Excel upload of physical results for one (age_category, gender) group. Staged:
    validated per row in the worker, then committed into sessions/measurements/evaluations."""

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Yuklandi"
        VALIDATING = "validating", "Tekshirilmoqda"
        VALIDATED = "validated", "Tekshirildi"  # may carry error rows
        FAILED = "failed", "Xato"  # file-level (unreadable/wrong header/over cap)
        COMMITTED = "committed", "Saqlandi"

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="import_batches"
    )
    file = models.FileField(upload_to="imports/")
    age_category = models.ForeignKey(
        "catalog.AgeCategory", on_delete=models.PROTECT, related_name="+"
    )
    gender = models.CharField(max_length=6, choices=Gender.choices)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPLOADED)
    row_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True, default="")  # file-level failure reason (status=failed)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "import batch"
        verbose_name_plural = "import batches"

    def __str__(self):
        return f"Import #{self.pk} ({self.get_status_display()})"


class ImportRow(TimeStampedModel):
    """One parsed row of an `ImportBatch`, validated independently (a bad row never aborts
    the batch). `raw_data` is the sanitized cell map; `created_session` is set at commit."""

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        VALID = "valid", "Yaroqli"
        ERROR = "error", "Xato"

    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="rows")
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    errors = models.JSONField(default=list)
    athlete = models.ForeignKey(
        "athletes.Athlete", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_session = models.ForeignKey(
        TestSession, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_by_row",
    )

    class Meta:
        ordering = ["batch", "row_number"]

    def __str__(self):
        return f"Row {self.row_number} ({self.status})"
