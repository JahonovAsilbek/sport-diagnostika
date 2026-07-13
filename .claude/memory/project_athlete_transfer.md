---
name: project_athlete_transfer
description: Athlete placement is transfer-only via an append-only ledger; transfers never rewrite history
metadata:
  type: project
---

**Athlete placement (region/district/organization/sport_type/coach) is transfer-only** (BCKND-68).

- Never PATCH those FKs directly — `AthleteViewSet.perform_update` **rejects (400)** any PATCH/PUT
  that changes an assignment field. Change placement only via `POST /athletes/{id}/transfer/`
  (reason required, scoped through `_guard_scope`). Non-assignment fields (name, razryad, is_active)
  still PATCH normally.
- The ledger is `AthleteAssignmentHistory` (`apps/athletes/models.py`) with a **partial unique
  constraint** `uniq_open_assignment_per_athlete` (`condition=Q(valid_to__isnull=True)`) → exactly
  one open (current) record per athlete. `GET /athletes/{id}/history/` returns it newest-first.
- The logic lives in `apps/athletes/services.py` (the app's first service): `open_initial_assignment`
  (called from `perform_create`) and `transfer_athlete` (atomic, `select_for_update`, no-op when the
  target equals current, closes the open record + opens a new one + syncs the athlete's FKs).
- **History-safe by construction**: `TestSession` (`measurements/services.py open_session`) and
  `Evaluation` (`scoring/services.py evaluate_session`) snapshot their own region/org/sport_type/
  age_category/gender at creation, so a transfer never rewrites past sessions/evaluations/rankings.
  Any future placement-touching feature (e.g. BCKND-70 period filter) can rely on these snapshots.
- Migrations that add a "one open per X" ledger to an existing table need a **RunPython backfill**
  (one open record per existing row) or the invariant is already violated — see `athletes/0002`.

Athlete is already audited (`apps/audit/signals.py` `AUDITED`), so the transfer's FK sync emits an
AuditLog row too; the ledger is the richer domain record. Related: [[project_architecture]].
