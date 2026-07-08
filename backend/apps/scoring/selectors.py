from apps.scoring.models import Evaluation


def _base():
    return Evaluation.objects.select_related(
        "age_category", "region", "sport_type"
    ).prefetch_related("indicators__exercise")


def athlete_evaluations(athlete):
    """An athlete's Evaluation snapshots, newest session first (history view)."""
    return _base().filter(athlete=athlete)


def latest_evaluation(athlete):
    """The athlete's most recent Evaluation, or `None`."""
    return athlete_evaluations(athlete).first()
