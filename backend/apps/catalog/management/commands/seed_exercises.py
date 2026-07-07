from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Exercise

# The physical-exercise pool (SCORING.md §2). Which 5 make up each (age×gender) battery
# is seeded later by seed_physical (BCKND-32) together with the norm tables.
# (name, unit, value_type, direction, order) — idempotent by name.
LOWER = Exercise.Direction.LOWER
HIGHER = Exercise.Direction.HIGHER
V = Exercise.ValueType

EXERCISES = [
    ("30 m ga yuqori startdan yugurish", "s", V.SECONDS, LOWER, 1),
    ("100 m ga pastki startdan yugurish", "s", V.SECONDS, LOWER, 2),
    ("400 m ga pastki startdan yugurish", "daq:s", V.MINSEC, LOWER, 3),
    ("Turgan joydan uzunlikka sakrash", "sm", V.COUNT, HIGHER, 4),
    ("Gimnastika oʻrindigʻida oldinga egilish", "sm", V.CM_SIGNED, HIGHER, 5),
    ("Argʻimchoqda sakrash (1 daqiqa)", "marta", V.COUNT, HIGHER, 6),
    ("Yerga tayanib qoʻllarni bukish (30 soniya)", "marta", V.COUNT, HIGHER, 7),
    ("Skameykaga tayanib qoʻllarni bukish (30 soniya)", "marta", V.COUNT, HIGHER, 8),
    ("Turnikda tortilish", "marta", V.COUNT, HIGHER, 9),
]


class Command(BaseCommand):
    help = "Seed the ~9 physical Exercise rows (the pool) from SCORING.md §2 (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for name, unit, value_type, direction, order in EXERCISES:
            _, was_created = Exercise.objects.get_or_create(
                name=name,
                defaults={
                    "unit": unit,
                    "value_type": value_type,
                    "direction": direction,
                    "order": order,
                },
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(f"seed_exercises: +{created} exercises."))
