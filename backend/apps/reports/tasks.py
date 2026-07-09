from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.reports.datasets import build_dataset
from apps.reports.models import Report
from apps.reports.renderers import RENDERERS

_EXTENSIONS = {
    Report.Format.EXCEL: "xlsx",
    Report.Format.WORD: "docx",
    Report.Format.PDF: "pdf",
}


@shared_task
def generate_report(report_id):
    """Build + render a report in the worker (BCKND-63). Any failure sets `status=failed` +
    `error` so a report is never left `pending`/`processing` forever."""
    report = Report.objects.filter(pk=report_id).first()
    if report is None:
        return
    report.status = Report.Status.PROCESSING
    report.save(update_fields=["status", "updated_at"])
    try:
        content = RENDERERS[report.format](build_dataset(report))
        report.file.save(
            f"report_{report.pk}.{_EXTENSIONS[report.format]}",
            ContentFile(content), save=False,
        )
        report.status = Report.Status.DONE
        report.error = ""
    except Exception as exc:  # a bad param / missing native lib must not hang the report
        report.status = Report.Status.FAILED
        report.error = str(exc)
    report.completed_at = timezone.now()
    report.save(update_fields=["file", "status", "error", "completed_at", "updated_at"])
