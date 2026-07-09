from django.db import models

from apps.common.models import TimeStampedModel


class RecommendationRule(TimeStampedModel):
    """An admin-managed rule: when an evaluation's metric satisfies `comparator threshold`,
    write a `Recommendation` from `template_text`. Rules are DATA, evaluable without code —
    `exercise` set → the rule targets that exercise's `IndicatorScore.points`; `exercise`
    null → it targets the `physical_total` (SCORING.md §8)."""

    class Comparator(models.TextChoices):
        LTE = "lte", "≤"
        LT = "lt", "<"
        GTE = "gte", "≥"
        GT = "gt", ">"

    exercise = models.ForeignKey(
        "catalog.Exercise", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    comparator = models.CharField(max_length=3, choices=Comparator.choices)
    threshold = models.PositiveSmallIntegerField()
    template_text = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        target = self.exercise if self.exercise_id else "physical_total"
        return f"{target} {self.get_comparator_display()} {self.threshold}"


class Recommendation(TimeStampedModel):
    """A generated recommendation for one Evaluation. `text` snapshots the rule's template at
    generation time, so it survives the rule being edited or deleted (`rule` is SET_NULL)."""

    evaluation = models.ForeignKey(
        "scoring.Evaluation", on_delete=models.CASCADE, related_name="recommendations"
    )
    rule = models.ForeignKey(
        RecommendationRule, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    text = models.TextField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text
