from apps.catalog.models import Norm


def get_norm(exercise, gender, age, on_date):
    """Return the active Norm for `exercise × gender`, covering `age`, with the latest
    `valid_from <= on_date` — or None (the caller marks that indicator ``unscored``).

    The lookup is exact: no sport/block, no fallback. `on_date` (the session date, not
    "now") pins the norm version so historical evaluations stay reproducible.
    """
    return (
        Norm.objects.filter(
            exercise=exercise,
            gender=gender,
            age_min__lte=age,
            age_max__gte=age,
            is_active=True,
            valid_from__lte=on_date,
        )
        .order_by("-valid_from")
        .first()
    )
