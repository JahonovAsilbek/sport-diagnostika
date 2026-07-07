from apps.catalog.models import AgeCategory


class AgeOutOfRange(Exception):
    """An athlete's age at a given date maps to no TOIFA AgeCategory (≈ <7 or >29)."""

    def __init__(self, age):
        self.age = age
        super().__init__(f"Yosh ({age}) hech qaysi TOIFA oralig'iga tushmaydi.")


def age_at(birth_year, on_date):
    """Calendar-year age — norms are keyed per single year (SCORING §11)."""
    return on_date.year - birth_year


def match_age_category(categories, age):
    """Pick the TOIFA whose `[age_min, age_max]` contains `age`; `None` if none match.

    The single matching rule, shared by `age_category_for` (one athlete, session time)
    and the list serializer (which passes a cached list to avoid an N+1 on the 6-row
    TOIFA table). `categories` must be ordered by `ordinal`.
    """
    for category in categories:
        if category.age_min <= age <= category.age_max:
            return category
    return None


def age_category_for(birth_year, on_date):
    """Return the TOIFA `AgeCategory` for an athlete's age at `on_date`.

    Raises `AgeOutOfRange` when the age falls outside every category — the caller must
    not silently bucket an out-of-range athlete (TASK BCKND-35). Computed at session
    time (not stored); drives the `TestBattery` selection in B6/B7.
    """
    age = age_at(birth_year, on_date)
    category = match_age_category(AgeCategory.objects.order_by("ordinal"), age)
    if category is None:
        raise AgeOutOfRange(age)
    return category
