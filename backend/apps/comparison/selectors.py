from apps.scoring.selectors import latest_evaluation


def compare_athletes(athletes):
    """Build the side-by-side rows (in the given order) and the `leader` id.

    Each row is the athlete's latest Evaluation (or a no-data row if none). `leader` is the
    id with the highest `physical_total` among evaluated athletes — request order breaks ties
    — or `None` if no athlete has an evaluation.
    """
    rows = []
    leader_id = None
    leader_total = None
    for athlete in athletes:
        evaluation = latest_evaluation(athlete)
        rows.append({
            "id": athlete.id,
            "full_name": athlete.full_name,
            "physical_total": evaluation.physical_total if evaluation else None,
            "ranking_score": evaluation.ranking_score if evaluation else None,
            "daraja": evaluation.daraja if evaluation else None,
            "color": evaluation.color if evaluation else None,
            "indicators": list(evaluation.indicators.all()) if evaluation else [],
        })
        if evaluation is not None and (
            leader_total is None or evaluation.physical_total > leader_total
        ):
            leader_total = evaluation.physical_total
            leader_id = athlete.id
    return rows, leader_id
