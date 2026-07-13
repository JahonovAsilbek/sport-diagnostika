"""Athlete assignment/transfer services (BCKND-68).

The assignment ledger (`AthleteAssignmentHistory`) is append-only: exactly one open record
(`valid_to=None`) per athlete is the current placement. `transfer_athlete` is the ONLY mutator
of an athlete's placement FKs — it closes the open record, opens a new one, and syncs the
athlete's denormalized FKs, atomically. Past TestSessions/Evaluations snapshot their own dims,
so a transfer never rewrites history (BCKND-39).
"""

from django.db import transaction
from django.utils import timezone

from apps.athletes.models import Athlete, AthleteAssignmentHistory

# The placement fields tracked by the ledger and kept in sync on the athlete.
ASSIGNMENT_FIELDS = ("region", "district", "organization", "sport_type", "coach")


def open_initial_assignment(athlete, *, changed_by=None, reason="Initial"):
    """Open the first (current) assignment record for a freshly created athlete."""
    return AthleteAssignmentHistory.objects.create(
        athlete=athlete,
        region=athlete.region,
        district=athlete.district,
        organization=athlete.organization,
        sport_type=athlete.sport_type,
        coach=athlete.coach,
        changed_by=changed_by,
        valid_from=timezone.localdate(),
        reason=reason,
    )


@transaction.atomic
def transfer_athlete(
    athlete, *, region, district, organization, sport_type, coach, changed_by, reason
):
    """Move `athlete` to a new (fully-resolved) placement, atomically. A no-op transfer (target
    equals the current assignment) writes nothing and returns the current record. Otherwise the
    open record is closed, a new one opened, and the athlete's FKs synced."""
    # Lock the athlete row for the duration; the partial unique constraint is the final backstop
    # against two concurrent transfers both opening a record.
    Athlete.objects.select_for_update().get(pk=athlete.pk)

    target = {
        "region": region,
        "district": district,
        "organization": organization,
        "sport_type": sport_type,
        "coach": coach,
    }
    current = athlete.assignment_history.filter(valid_to__isnull=True).first()
    if current is not None and all(
        getattr(current, f"{name}_id") == (obj.pk if obj else None) for name, obj in target.items()
    ):
        return current  # nothing changed

    today = timezone.localdate()
    if current is not None:
        current.valid_to = today
        current.save(update_fields=["valid_to", "updated_at"])

    record = AthleteAssignmentHistory.objects.create(
        athlete=athlete,
        changed_by=changed_by,
        valid_from=today,
        reason=reason,
        **target,
    )

    # Sync the athlete's denormalized FKs (this also emits an Athlete AuditLog row).
    for name, obj in target.items():
        setattr(athlete, name, obj)
    athlete.save(update_fields=list(ASSIGNMENT_FIELDS))
    return record
