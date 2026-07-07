import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import (
    AgeCategory,
    BatteryItem,
    DarajaThreshold,
    Exercise,
    Norm,
    NormBand,
    TestBattery,
)
from apps.catalog.validators import assert_bands_no_overlap

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "physical_norms.json"
# Norm edition. Re-seeding a NEW edition (bump this) preserves old Evaluation snapshots.
EDITION = date(2020, 1, 1)

# exercise key (in the data file) -> a case-insensitive substring of the seeded Exercise name
KEY_KEYWORD = {
    "30m": "30 m",
    "100m": "100 m",
    "400m": "400 m",
    "jump": "uzunlikka",
    "flex": "egilish",
    "rope": "imchoq",
    "pushup_floor": "yerga",
    "pushup_bench": "skameyka",
    "pullup": "tortilish",
}

DARAJA = [("I", 48, 50), ("II", 38, 46), ("III", 30, 36)]


def build_bands(ranges, value_type):
    """Contiguous `[lower, upper)` bands from the table's 3 discrete ranges.

    Each band runs from its own low up to the next band's low; the outermost band
    extends one measurement step past its high. `direction` needs no handling here —
    the points just descend or ascend with the raw value.
    """
    step = Decimal("0.1") if value_type == "seconds" else Decimal("1")
    ordered = sorted(ranges, key=lambda r: r["low"])
    out = []
    for i, r in enumerate(ordered):
        lower = Decimal(str(r["low"]))
        if i + 1 < len(ordered):
            upper = Decimal(str(ordered[i + 1]["low"]))
        else:
            upper = Decimal(str(r["high"])) + step
        out.append((r["points"], lower, upper))
    return out


class Command(BaseCommand):
    help = "Idempotently seed physical-readiness norms, batteries and daraja thresholds."

    @transaction.atomic
    def handle(self, *args, **options):
        tables = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        exercises = self._resolve_exercises()

        norms = bands = batteries = items = 0
        for table in tables:
            age_category = AgeCategory.objects.filter(
                age_min__lte=table["age_min"], age_max__gte=table["age_max"]
            ).first()
            if age_category is None:
                raise CommandError(
                    f"No AgeCategory covers {table['age_min']}-{table['age_max']} — "
                    "run seed_catalog first."
                )
            battery, created = TestBattery.objects.get_or_create(
                age_category=age_category, gender=table["gender"]
            )
            batteries += created

            for order, entry in enumerate(table["exercises"], start=1):
                exercise = exercises[entry["key"]]
                norm, created = Norm.objects.get_or_create(
                    exercise=exercise,
                    age_min=table["age_min"],
                    age_max=table["age_max"],
                    gender=table["gender"],
                    valid_from=EDITION,
                )
                norms += created
                built = build_bands(entry["ranges"], exercise.value_type)
                assert_bands_no_overlap(
                    [{"lower_bound": lo, "upper_bound": hi} for _, lo, hi in built]
                )
                for points, lower, upper in built:
                    _, created = NormBand.objects.update_or_create(
                        norm=norm, points=points,
                        defaults={"lower_bound": lower, "upper_bound": upper},
                    )
                    bands += created
                _, created = BatteryItem.objects.update_or_create(
                    battery=battery, order=order, defaults={"exercise": exercise}
                )
                items += created

        for level, total_min, total_max in DARAJA:
            DarajaThreshold.objects.update_or_create(
                level=level, defaults={"total_min": total_min, "total_max": total_max}
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_physical: +{norms} norms, +{bands} bands, +{batteries} batteries, "
                f"+{items} battery items, {len(DARAJA)} daraja thresholds."
            )
        )

    def _resolve_exercises(self):
        resolved = {}
        for key, keyword in KEY_KEYWORD.items():
            exercise = Exercise.objects.filter(name__icontains=keyword).first()
            if exercise is None:
                raise CommandError(
                    f"Exercise for '{key}' (keyword '{keyword}') not found — "
                    "run seed_exercises first."
                )
            resolved[key] = exercise
        return resolved
