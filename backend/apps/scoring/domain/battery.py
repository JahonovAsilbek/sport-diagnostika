"""Battery resolution — the ordered 5 exercises for an (age_category, gender) group."""

from apps.catalog.models import TestBattery


def battery_for(age_category, gender):
    """The ordered `Exercise`s an athlete of `(age_category, gender)` performs, or `None`
    if the admin hasn't defined an active `TestBattery` for the group yet.

    The battery differs by group — young toifalar use 30 m + argʻimchoq, older ones 100 m +
    400 m, and #4/#5 differ by gender (SCORING.md §2). This is the pure `(age_category,
    gender)` resolver; `measurements.selectors.resolve_battery` is its session-bound sibling.
    """
    battery = (
        TestBattery.objects.filter(age_category=age_category, gender=gender, is_active=True)
        .prefetch_related("items__exercise")
        .first()
    )
    if battery is None:
        return None
    return [item.exercise for item in battery.items.all()]
