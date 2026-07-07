from django.db import models

from apps.common.models import Gender, TimeStampedModel


class Region(TimeStampedModel):
    name = models.CharField(max_length=100)
    # Stable identifier for seeds/imports — don't key on the (Uzbek) display name.
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(TimeStampedModel):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["region", "name"]
        constraints = [
            models.UniqueConstraint(fields=["region", "name"], name="uniq_district_per_region"),
        ]

    def __str__(self):
        return self.name


class Organization(TimeStampedModel):
    class Type(models.TextChoices):
        OTM = "OTM", "OTM"
        OPSTTM = "OPSTTM", "OPSTTM"

    name = models.CharField(max_length=200)
    # Classification / filter only — does NOT affect physical scoring.
    type = models.CharField(max_length=10, choices=Type.choices)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="organizations")
    district = models.ForeignKey(
        District, on_delete=models.PROTECT, related_name="organizations", null=True, blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SportType(TimeStampedModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AgeCategory(TimeStampedModel):
    """TOIFA grouping — six ordinals (1: 7–8 … 6: 18–29)."""

    ordinal = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=50)
    age_min = models.PositiveSmallIntegerField()
    age_max = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["ordinal"]
        verbose_name = "age category"
        verbose_name_plural = "age categories"

    def __str__(self):
        return self.name


class Exercise(TimeStampedModel):
    """The physical-exercise pool (replaces the deferred TestType)."""

    class ValueType(models.TextChoices):
        SECONDS = "seconds", "Soniya"
        MINSEC = "minsec", "Daqiqa:soniya"
        COUNT = "count", "Son"
        CM_SIGNED = "cm_signed", "Santimetr (ishorali)"

    class Direction(models.TextChoices):
        HIGHER = "higher", "Ko'proq — yaxshiroq"
        LOWER = "lower_is_better", "Kamroq — yaxshiroq"

    name = models.CharField(max_length=150)
    unit = models.CharField(max_length=20)
    value_type = models.CharField(max_length=10, choices=ValueType.choices)
    direction = models.CharField(max_length=15, choices=Direction.choices)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class TestBattery(TimeStampedModel):
    """The ordered 5 exercises an athlete of a given (age_category, gender) performs."""

    age_category = models.ForeignKey(
        AgeCategory, on_delete=models.CASCADE, related_name="batteries"
    )
    gender = models.CharField(max_length=6, choices=Gender.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["age_category", "gender"]
        verbose_name = "test battery"
        verbose_name_plural = "test batteries"
        constraints = [
            models.UniqueConstraint(
                fields=["age_category", "gender"], name="uniq_battery_per_group"
            ),
        ]

    def __str__(self):
        return f"{self.age_category} · {self.get_gender_display()}"


class BatteryItem(TimeStampedModel):
    battery = models.ForeignKey(TestBattery, on_delete=models.CASCADE, related_name="items")
    exercise = models.ForeignKey(
        Exercise, on_delete=models.PROTECT, related_name="battery_items"
    )
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["battery", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["battery", "order"], name="uniq_item_order_per_battery"
            ),
            models.UniqueConstraint(
                fields=["battery", "exercise"], name="uniq_exercise_per_battery"
            ),
        ]

    def __str__(self):
        return f"{self.battery} #{self.order} {self.exercise}"
