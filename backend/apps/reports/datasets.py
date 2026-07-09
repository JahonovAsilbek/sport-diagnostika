"""Report datasets — turn a Report request into a generic (title, columns, rows) table, reusing
the rating/scoring selectors. Each builder scopes to the requester, so a report never leaks
out-of-scope data (the same scope is also asserted at request time for a clean 403)."""
from dataclasses import dataclass

from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.athletes.models import Athlete
from apps.common.permissions import REGION_ADMIN
from apps.common.scoping import scope_queryset
from apps.rating.selectors import ranked_athletes, region_rating
from apps.reports.models import Report
from apps.scoring.selectors import latest_evaluation


@dataclass
class ReportDataset:
    title: str
    subtitle: str
    columns: list
    rows: list


def _scoped_athlete(user, athlete_id):
    if athlete_id is None:
        raise ValidationError({"params": "athlete majburiy."})
    athlete = (
        scope_queryset(
            Athlete.objects.all(), user,
            region_field="region_id", organization_field="organization_id", coach_field="coach",
        )
        .filter(pk=athlete_id)
        .first()
    )
    if athlete is None:
        raise PermissionDenied("Bu sportchi ko'lamingizdan tashqarida.")
    return athlete


def _filters(params):
    mapping = {
        "region": "region_id", "sport_type": "sport_type_id",
        "age_category": "age_category_id", "gender": "gender",
    }
    return {field: params[key] for key, field in mapping.items() if params.get(key) is not None}


def assert_params_in_scope(report_type, params, user):
    """Request-time scope guard → `PermissionDenied` (403). The ranking selectors re-scope at
    build time, so this is a friendly early check, not the sole enforcement."""
    if report_type == Report.Type.ATHLETE:
        _scoped_athlete(user, params.get("athlete"))
    elif getattr(user, "role", None) == REGION_ADMIN:
        region = params.get("region")
        if region is not None and region != user.region_id:
            raise PermissionDenied("Faqat o'z viloyatingiz hisobotini so'rashingiz mumkin.")


def _athlete_dataset(params, user):
    athlete = _scoped_athlete(user, params.get("athlete"))
    columns = ["Mashq", "Natija", "Ball"]
    evaluation = latest_evaluation(athlete)
    if evaluation is None:
        return ReportDataset(athlete.full_name, "Baholanmagan", columns, [])
    subtitle = f"Umumiy ball: {evaluation.physical_total} — {evaluation.get_daraja_display()}"
    rows = [[i.exercise.name, str(i.raw_value), i.points] for i in evaluation.indicators.all()]
    return ReportDataset(athlete.full_name, subtitle, columns, rows)


def _ranking_dataset(params, user, title):
    columns = ["#", "Sportchi", "Ball", "Daraja"]
    rows = [
        [evaluation.rank, evaluation.athlete.full_name,
         evaluation.ranking_score, evaluation.get_daraja_display()]
        for evaluation in ranked_athletes(_filters(params), user)
    ]
    return ReportDataset(title, "", columns, rows)


def _republic_dataset(params, user):
    columns = ["#", "Viloyat", "I daraja soni", "O'rtacha ball"]
    rows = [
        [row["rank"], row["region__name"], row["daraja_i_count"],
         round(float(row["avg_score"] or 0), 1)]
        for row in region_rating(_filters(params), user)
    ]
    return ReportDataset("Respublika reytingi", "", columns, rows)


_BUILDERS = {
    Report.Type.ATHLETE: _athlete_dataset,
    Report.Type.REGION: lambda params, user: _ranking_dataset(params, user, "Viloyat reytingi"),
    Report.Type.SPORT: lambda params, user: _ranking_dataset(params, user, "Sport turi reytingi"),
    Report.Type.REPUBLIC: _republic_dataset,
}


def build_dataset(report):
    """Build the (scoped) dataset for a report from its type + params."""
    return _BUILDERS[report.type](report.params, report.requested_by)
