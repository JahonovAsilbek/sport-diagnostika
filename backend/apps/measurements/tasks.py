from celery import shared_task

from apps.measurements.import_services import FileImportError, read_rows, validate_row
from apps.measurements.models import ImportBatch, ImportRow
from apps.scoring.domain.battery import battery_for


@shared_task
def validate_import_batch(batch_id):
    """Parse + validate an uploaded batch in the worker (BCKND-59). Idempotent — clears any
    prior rows so a retry is deterministic. Per-row errors set `error_count` but the batch is
    `validated`; only a file-level problem makes it `failed`."""
    batch = (
        ImportBatch.objects.select_related("uploaded_by", "age_category")
        .filter(pk=batch_id)
        .first()
    )
    if batch is None:
        return
    batch.rows.all().delete()
    batch.status = ImportBatch.Status.VALIDATING
    batch.save(update_fields=["status", "updated_at"])

    exercises = battery_for(batch.age_category, batch.gender)
    if exercises is None:
        return _fail(batch, "Bu guruh uchun test batareyasi aniqlanmagan.")
    try:
        rows = read_rows(batch.file.open("rb"), exercises)
    except FileImportError as exc:
        return _fail(batch, str(exc))

    import_rows, error_count = [], 0
    for row_number, row_dict in rows:
        status, errors, athlete = validate_row(row_dict, batch, batch.uploaded_by, exercises)
        if status == ImportRow.Status.ERROR:
            error_count += 1
        import_rows.append(ImportRow(
            batch=batch, row_number=row_number, raw_data=row_dict,
            status=status, errors=errors, athlete=athlete,
        ))
    ImportRow.objects.bulk_create(import_rows)

    batch.row_count = len(import_rows)
    batch.error_count = error_count
    batch.status = ImportBatch.Status.VALIDATED
    batch.save(update_fields=["row_count", "error_count", "status", "updated_at"])


def _fail(batch, message):
    batch.status = ImportBatch.Status.FAILED
    batch.error = message
    batch.save(update_fields=["status", "error", "updated_at"])
