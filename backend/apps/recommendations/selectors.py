from apps.scoring.selectors import latest_evaluation


def recommendations_for_athlete(athlete):
    """The recommendations from the athlete's latest Evaluation, or `[]` if none. Joins the
    rule + its exercise so the serializer's exercise lookup doesn't N+1."""
    evaluation = latest_evaluation(athlete)
    if evaluation is None:
        return []
    return list(evaluation.recommendations.select_related("rule", "rule__exercise"))
