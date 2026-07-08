from celery import shared_task
from rest_framework.exceptions import ValidationError

from apps.measurements.models import TestSession
from apps.scoring.services import evaluate_session


@shared_task
def recompute_evaluations(filter_kwargs=None):
    """Re-score finalized sessions after a norm change (BCKND-47).

    Runs in the worker (never the web process). Streams sessions in chunks so a large slice
    stays memory-bounded. A session that can no longer be scored — e.g. a norm was removed,
    making an indicator unscored — is skipped (its prior Evaluation is left intact by
    `evaluate_session`'s early unscored check), not fatal to the batch. The norm version is
    pinned by each session's date, so historical norms are used.
    """
    filter_kwargs = filter_kwargs or {}
    sessions = TestSession.objects.filter(
        status=TestSession.Status.FINALIZED, **filter_kwargs
    ).iterator(chunk_size=200)
    recomputed = skipped = 0
    for session in sessions:
        try:
            evaluate_session(session)
            recomputed += 1
        except ValidationError:
            skipped += 1
    # B8: invalidate the rating cache for the affected partitions.
    return {"recomputed": recomputed, "skipped": skipped}
