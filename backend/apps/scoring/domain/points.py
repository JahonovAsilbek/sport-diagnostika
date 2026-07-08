"""Raw value → points (10/8/6) — the pure band-resolution core (SCORING.md §3)."""


def resolve_points(norm, raw_value):
    """Return the points a `raw_value` earns against a `norm`'s bands.

    The `NormBand` whose half-open `[lower_bound, upper_bound)` contains `raw_value` gives
    its points (10/8/6). `direction` is already baked into how the bands were entered
    (SCORING.md §3.4) — the engine only checks which range the value falls into.

    Out of range → clamp (§3.5): a value past the *outer* edge of the best (top-points)
    band scores that top; past the outer edge of the worst band scores 0 (below norm, never
    an error). Direction is inferred from which end the top band sits on, so no `direction`
    lookup is needed:

    - lower_is_better: the top band holds the smallest numbers (it's ``bands[0]`` once sorted
      by ``lower_bound``) → below the range is better → top; above is worse → 0.
    - higher_is_better: the top band is ``bands[-1]`` → above the range is better → top;
      below is worse → 0.

    Assumes the bands are contiguous and monotonic in points (guaranteed by the seed tables +
    ``assert_bands_no_overlap``); an interior gap can't occur and falls through to 0.
    """
    bands = sorted(norm.bands.all(), key=lambda b: b.lower_bound)
    if not bands:
        return 0
    for band in bands:
        if band.lower_bound <= raw_value < band.upper_bound:
            return band.points
    top = max(band.points for band in bands)
    if raw_value < bands[0].lower_bound:
        return bands[0].points if bands[0].points == top else 0
    if raw_value >= bands[-1].upper_bound:
        return bands[-1].points if bands[-1].points == top else 0
    return 0
