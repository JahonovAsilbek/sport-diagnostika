from apps.scoring.models import Evaluation


def _base():
    return Evaluation.objects.select_related(
        "age_category", "region", "sport_type"
    ).prefetch_related("indicators__exercise")


def athlete_evaluations(athlete, date_range=None):
    """An athlete's Evaluation snapshots, newest session first (history view). `date_range`
    (start, end) inclusively narrows `session_date` when given (BCKND-70)."""
    qs = _base().filter(athlete=athlete)
    if date_range:
        qs = qs.filter(session_date__range=date_range)
    return qs


def latest_evaluation(athlete, date_range=None):
    """The athlete's most recent Evaluation (within `date_range` if given), or `None`."""
    return athlete_evaluations(athlete, date_range).first()
