from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.catalog.models import BatteryItem
from apps.catalog.selectors import get_norm

# Read-only pre-flight (BCKND-30). Every battery exercise must have an active norm for
# EACH single year of its TOIFA range × gender, so `finalize` never hits an unexpected
# `unscored` indicator in production (SCORING.md §7). Run before go-live; gaps → exit 1.


class Command(BaseCommand):
    help = "Check that every battery exercise has an active norm for each covered age × gender."

    def handle(self, *args, **options):
        on_date = timezone.localdate()
        gaps = []
        items = BatteryItem.objects.select_related(
            "battery__age_category", "exercise"
        ).order_by("battery__age_category__ordinal", "battery__gender", "order")
        for item in items:
            battery = item.battery
            category = battery.age_category
            for age in range(category.age_min, category.age_max + 1):
                if get_norm(item.exercise, battery.gender, age, on_date) is None:
                    gaps.append((item.exercise, battery.gender, age))

        if not gaps:
            self.stdout.write(
                self.style.SUCCESS(
                    "check_physical_norms: barcha battareya mashqlari uchun normalar mavjud."
                )
            )
            return

        for exercise, gender, age in gaps:
            self.stdout.write(
                self.style.ERROR(f"  norma topilmadi: {exercise} · {gender} · {age} yosh")
            )
        raise CommandError(
            f"check_physical_norms: {len(gaps)} ta mashq × yosh × jins uchun norma yetishmayapti."
        )
