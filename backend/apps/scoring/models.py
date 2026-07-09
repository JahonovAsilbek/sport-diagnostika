from django.db import models

from apps.common.models import Gender, TimeStampedModel


class Evaluation(TimeStampedModel):
    """A stored scoring snapshot for one finalized `TestSession` (single-scheme physical
    readiness). The ranking dims are denormalized/snapshotted so `RANK()` (B8) scans one
    indexed table without joining a possibly-transferred athlete; `age_category` is the
    TOIFA computed at `session_date`. `ranking_score == physical_total`."""

    class Daraja(models.TextChoices):
        FIRST = "I", "I daraja"
        SECOND = "II", "II daraja"
        THIRD = "III", "III daraja"
        NONE = "none", "Nishonsiz"

    class Color(models.TextChoices):
        GREEN = "green", "Yashil"
        YELLOW = "yellow", "Sariq"
        RED = "red", "Qizil"

    session = models.OneToOneField(
        "measurements.TestSession", on_delete=models.CASCADE, related_name="evaluation"
    )
    athlete = models.ForeignKey(
        "athletes.Athlete", on_delete=models.PROTECT, related_name="evaluations"
    )

    # Snapshot ranking dims — frozen from the session (itself frozen from the athlete).
    age_category = models.ForeignKey(
        "catalog.AgeCategory", on_delete=models.PROTECT, related_name="+"
    )
    gender = models.CharField(max_length=6, choices=Gender.choices)
    region = models.ForeignKey("catalog.Region", on_delete=models.PROTECT, related_name="+")
    sport_type = models.ForeignKey("catalog.SportType", on_delete=models.PROTECT, related_name="+")
    session_date = models.DateField()

    physical_total = models.PositiveSmallIntegerField()  # 0–50
    daraja = models.CharField(max_length=4, choices=Daraja.choices)
    color = models.CharField(max_length=6, choices=Color.choices)
    ranking_score = models.PositiveSmallIntegerField()  # = physical_total
    computed_at = models.DateTimeField()

    class Meta:
        ordering = ["-session_date", "-id"]
        indexes = [
            models.Index(
                fields=["region", "sport_type", "age_category", "gender", "ranking_score"],
                name="eval_ranking_idx",
            ),
        ]

    def __str__(self):
        return f"{self.athlete} — {self.physical_total} ({self.daraja})"


class IndicatorScore(TimeStampedModel):
    """One exercise's contribution to an Evaluation: the raw value and the points it earned."""

    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="indicators")
    exercise = models.ForeignKey("catalog.Exercise", on_delete=models.PROTECT, related_name="+")
    raw_value = models.DecimalField(max_digits=8, decimal_places=2)
    points = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["evaluation", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["evaluation", "exercise"], name="uniq_indicator_per_exercise"
            ),
        ]

    def __str__(self):
        return f"{self.exercise} → {self.points}"
