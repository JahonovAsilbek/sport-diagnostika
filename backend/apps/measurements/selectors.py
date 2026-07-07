from apps.catalog.models import TestBattery


def resolve_battery(session):
    """The group's `TestBattery` (with ordered items prefetched) for the session's
    snapshot `(age_category, gender)`, or `None` if the admin hasn't defined one yet
    (the entry form can't open — SCORING.md §7)."""
    return (
        TestBattery.objects.filter(
            age_category=session.age_category, gender=session.gender, is_active=True
        )
        .prefetch_related("items__exercise")
        .first()
    )


def battery_exercise_ids(session):
    """Ordered exercise ids required for the session, or `None` if no battery."""
    battery = resolve_battery(session)
    if battery is None:
        return None
    return [item.exercise_id for item in battery.items.all()]


def missing_exercises(session):
    """Battery exercise ids that still have no `Measurement`. `None` if no battery
    is defined for the group (distinct from `[]` = complete)."""
    required = battery_exercise_ids(session)
    if required is None:
        return None
    entered = set(session.measurements.values_list("exercise_id", flat=True))
    return [eid for eid in required if eid not in entered]
