from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import Role
from apps.common.models import Gender, TimeStampedModel


class Athlete(TimeStampedModel):
    """A registered student-athlete. The first region-scoped data entity.

    `age_category` (TOIFA) is NOT stored — it depends on the session date and is derived
    via `age_category_for` (selectors). `weight_category` is deferred (morpho, DEFERRED.md).
    """

    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    birth_year = models.PositiveSmallIntegerField(db_index=True)
    gender = models.CharField(max_length=6, choices=Gender.choices)

    region = models.ForeignKey("catalog.Region", on_delete=models.PROTECT, related_name="athletes")
    district = models.ForeignKey(
        "catalog.District",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="athletes",
    )
    organization = models.ForeignKey(
        "catalog.Organization", on_delete=models.PROTECT, related_name="athletes"
    )
    sport_type = models.ForeignKey(
        "catalog.SportType", on_delete=models.PROTECT, related_name="athletes"
    )
    # SET_NULL (not PROTECT): users are soft-deactivated, never deleted, but keep the
    # athlete if a coach account is ever removed. limit_choices_to guards the admin form.
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": Role.COACH},
        related_name="athletes",
    )

    razryad = models.CharField(max_length=50, blank=True)
    training_experience = models.CharField(max_length=100, blank=True)
    main_competitions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return " ".join(p for p in (self.last_name, self.first_name, self.middle_name) if p)

    @property
    def block(self):
        """OTM/OPSTTM classification, read from the organization — never a scoring axis."""
        return self.organization.type

    def clean(self):
        if self.district_id and self.region_id and self.district.region_id != self.region_id:
            raise ValidationError(
                {"district": "Tuman tanlangan viloyatga tegishli bo'lishi kerak."}
            )


class AthleteAssignmentHistory(TimeStampedModel):
    """An append-only ledger of an athlete's placement (region/district/organization/sport_type/
    coach) over time (BCKND-68). Exactly ONE open record (`valid_to=None`) per athlete is the
    current assignment, kept in sync with the athlete's denormalized FKs by the transfer service
    (`services.transfer_athlete`). Past TestSessions/Evaluations snapshot their own dims, so a
    transfer never rewrites history (BCKND-39)."""

    athlete = models.ForeignKey(
        Athlete, on_delete=models.CASCADE, related_name="assignment_history"
    )
    region = models.ForeignKey("catalog.Region", on_delete=models.PROTECT, related_name="+")
    district = models.ForeignKey(
        "catalog.District", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    organization = models.ForeignKey(
        "catalog.Organization", on_delete=models.PROTECT, related_name="+"
    )
    sport_type = models.ForeignKey("catalog.SportType", on_delete=models.PROTECT, related_name="+")
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": Role.COACH},
        related_name="+",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-valid_from", "-id"]
        constraints = [
            # The invariant: at most one open (current) assignment per athlete.
            models.UniqueConstraint(
                fields=["athlete"],
                condition=models.Q(valid_to__isnull=True),
                name="uniq_open_assignment_per_athlete",
            )
        ]

    def __str__(self):
        return f"{self.athlete_id}: {self.valid_from} → {self.valid_to or 'hozir'}"
