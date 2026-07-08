"""Total → daraja + color (SCORING.md §5). Cut-offs are data (`DarajaThreshold`)."""
from apps.catalog.models import DarajaThreshold

# I daraja → green, II → yellow, III → red; below every threshold → nishonsiz (none) → red.
_COLOR_BY_LEVEL = {"I": "green", "II": "yellow", "III": "red"}


def daraja_for(total):
    """Map a `physical_total` (0–50) to `(daraja, color)` via `DarajaThreshold`.

    Returns `("none", "red")` when the total is below every threshold. Points are 0/6/8/10,
    so a total is always even and the odd gaps (37, 47) between the fixed bands never occur —
    every reachable total ≥ 30 lands in a band, and < 30 is nishonsiz.
    """
    threshold = DarajaThreshold.objects.filter(
        total_min__lte=total, total_max__gte=total
    ).first()
    if threshold is None:
        return "none", "red"
    return threshold.level, _COLOR_BY_LEVEL[threshold.level]
