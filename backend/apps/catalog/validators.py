from django.core.exceptions import ValidationError


def assert_bands_no_overlap(bands):
    """Raise ValidationError if any two `[lower_bound, upper_bound)` bands overlap.

    `bands` is an iterable of objects/dicts exposing lower_bound/upper_bound. Half-open
    intervals: two are disjoint iff one ends at-or-before the other starts.
    """

    def bounds(band):
        if isinstance(band, dict):
            return band["lower_bound"], band["upper_bound"]
        return band.lower_bound, band.upper_bound

    intervals = sorted((bounds(b) for b in bands), key=lambda pair: pair[0])
    for (_, upper_prev), (lower_next, _) in zip(intervals, intervals[1:], strict=False):
        if lower_next < upper_prev:
            raise ValidationError("Norm bantlari bir-birining ustiga tushmasligi kerak.")
