---
name: project_architecture
description: "SPORT-DIAGNOSTIKA backend/full-app architecture — stack, modules, physical-readiness-first scoring model"
metadata: 
  node_type: memory
  type: project
  originSessionId: b9ce4b4d-c064-40c7-9573-f3ffc2d7c413
---

The static landing (lite at root, premium under `premium/`) is evolving into a
full **Python web platform** built from `SPORT.docx` (TTZ). Architecture agreed
2026-06-16; **pivoted to physical-readiness-first 2026-07-07**. Backend implemented
through **B8 Rating & Ranking ★** (accounts · catalog + seeded norms/batteries · athletes ·
measurements · scoring · rating = `RANK()` leaderboards + region ranking + Redis cache)
against the running colima Postgres/Redis stack; per-task progress lives in `docs/TASK.md`.
**B9 (comparison) is next** — a thin side-by-side endpoint reading the scoring selectors.

**Stack (decided):** Django 5 + DRF · Vue 3 + Vite + Pinia SPA · PostgreSQL 16 ·
Celery + Redis (fon + cache) · JWT auth · Docker Compose on own VPS · Nginx +
Gunicorn. Reports: openpyxl/python-docx/WeasyPrint in Celery.

**Pattern:** modular monolith (NOT microservices — 3000–5000 users is small).
Django apps = modules with clean layers (domain/services/selectors, HackSoft
styleguide). Modules (downward deps only): accounts (auth + region-scope) →
catalog (reference data + scoring NORMS/batteries/thresholds) → athletes →
measurements → scoring (★ pure domain engine) → rating/recommendations/comparison
→ reports. Cross-cutting: audit, import/export, admin.

**PIVOT (2026-07-07) — physical readiness only.** The client delivered criteria for
**only** the state "Jismoniy tayyorgarlik darajasi" (physical-readiness) standard
(two files in `resources/`: `… 7-17 yoshgacha.docx`, `… 18-29 yosh.doc`). Functional,
morphofunctional, psychological and BMI criteria **do not exist yet** and may have a
different structure. Decision: build **physical end-to-end, defer the rest**. The old
**OTM/OPSTTM two-strategy** model (1–5 pts × 10 tests → 50 → % → 5/3 levels, BMI, the
four extra categories, sport/block-specific norms) is **parked, not cancelled**, in
`docs/DEFERRED.md`. Concrete standard facts: [[project_physical_readiness]].

**Scoring model (locked, physical readiness):** each exercise's raw result →
**10 / 8 / 6 points** (NOT 1–5) via `Norm` + `NormBand` (data, no bounds in code).
**5 exercises** → `physical_total` **0–50** → `daraja I / II / III / none` via
`DarajaThreshold` (I:48–50 · II:38–46 · III:30–36 · <30 none). `ranking_score =
physical_total`. The **5 exercises are chosen per `(AgeCategory × gender)`** through an
explicit `TestBattery` + `BatteryItem` (exactly 5) — the exercise itself differs by
gender (boys turnikda tortilish ↔ girls skameykaga qoʻl bukish) and by age (30 m →
100 m, +400 m for older). The standard is **universal by age × gender,
block-independent**; `Organization.type` (OTM|OPSTTM) is **classification/filter only**,
not a scoring axis. Evaluation is a **stored snapshot** (`Evaluation` +
`IndicatorScore`); ranking dims (region, sport_type, age_category, gender, session_date)
are snapshotted so history survives athlete transfers.

**Core entities:** `AgeCategory` (TOIFA ordinal 1–6, age_min/max) · `Exercise` (pool;
replaces old `TestType`) · `TestBattery` + `BatteryItem` · `Norm`
(exercise × age_range × gender — **no sport, no block**) · `NormBand`
(points, lower/upper bound) · `DarajaThreshold`. Norm lookup uses **numeric age**
(a norm per single year 7–17, one 18–29 bucket), not the TOIFA FK. Ranking partition =
`(region, sport_type, age_category, gender)` — **no block**; computed via Postgres
`RANK()` + Redis cache, not a table.

**Security core (unchanged):** region-scoping enforced server-side on every request,
never trusting client filters. **5 roles:** Super admin, Viloyat admin, Murabbiy,
Laboratoriya xodimi/operator, Vazirlik vakili.

**Scoped-write convention** (established in `athletes`, reused by `measurements`): the
read/write role split lives in `common/permissions.DataEntryOrReadOnly` (write =
super_admin/region_admin/coach/lab_operator; ministry read-only). Each scoped data
ViewSet adds `ScopedQuerysetMixin` + `scope_region_field`/`scope_organization_field`/
`scope_coach_field` so an out-of-scope pk naturally 404s, plus a create guard in
`perform_create` — a coach-created row **forces `coach=self`**, and a scoped creator can
only place/open a row for an in-scope target (athletes) else 403. Sessions snapshot the
athlete's dims at open (age_category computed at session date) and are scoped via
`athlete__coach` + the snapshot region/org; only `draft` sessions are mutable, `finalize`
validates the full 5-exercise battery before transitioning.
`age_category` (TOIFA) is **computed, never stored** (`athletes.selectors.age_category_for`
raises `AgeOutOfRange` outside 7–29); list filters translate it to a `birth_year` range in
SQL, not per-row.

**Scoring engine (`apps/scoring`, B7).** `domain/points.resolve_points(norm, raw)` is
**direction-agnostic**: it re-sorts bands by `lower_bound` (needed — `NormBand` default
ordering is `-points`) and infers direction from which end the top-points band sits on, so
it never reads `Exercise.direction` (clamp: past the top band's outer edge → 10, past the
worst → 0). `services.evaluate_session` is `@transaction.atomic` and **idempotent** (deletes
+ recreates the session's Evaluation), so recompute/re-finalize replace cleanly; a missing
norm → `ValidationError({"unscored":[...]})`, never scored 0. **Dependency rule:** scoring
sits *below* measurements/athletes — measurements/athletes may import scoring at the API
layer only (`measurements/api.py` finalize, `athletes/api.py` sub-routes); scoring imports
their selectors/models, never their `api`. **Finalize wiring:** the `/sessions/{id}/finalize/`
action wraps `finalize_session` + `evaluate_session` in **one** `transaction.atomic()`
(`ATOMIC_REQUESTS=False`, so without it an unscored failure would strand the session
finalized-but-unscored), and returns **200** with the evaluation body (API.md says 202 but
its body is synchronous — 200 is correct). Recompute (`POST /evaluations/recompute/`,
super_admin) validates through an allowlist serializer — raw request data never reaches
`.filter()`. Tests run Celery **eager** (`config/settings/test.py`, Redis-free).

**Rating (`apps/rating`, B8).** Ranking is **computed, not stored**. `selectors.py`: latest
Evaluation per athlete via `DISTINCT ON (athlete_id)` **as a subquery**, then a separate outer
query with `Window(Rank(), partition_by=[region,sport_type,age_category,gender],
order_by=ranking_score DESC)` — the two can't share one query (DISTINCT ON ↔ window collide).
Ties share rank (only score in the window order); display tiebreak `-session_date, name`.
Region ranking aggregates then **ranks in Python** (a SQL window over GROUP BY is fragile).
Scope is applied **before** the window. **Cache (`cache.py`)**: keyed `rating:{endpoint}:
{scope_token}:{filters}:{gen}` — the **scope_token is mandatory** (else two region_admins share
a key → ranking leak). Invalidation = a global generation counter bumped on ANY Evaluation
write, wired from `rating/apps.py ready()` via `post_save`/`post_delete` on `Evaluation` →
`transaction.on_commit(bump_generation)` (so scoring never imports rating; recompute covered
free). All cache access is best-effort (Redis outage can't break a write/read). Cached values
must be **plain lists** (DRF `ReturnList` isn't picklable). Testing on_commit invalidation needs
the `django_capture_on_commit_callbacks` fixture (pytest wraps tests in a rolled-back txn).
**DVPS-7:** `django-celery-beat` installed; compose `beat` uses `DatabaseScheduler` and waits on
`web` healthy (migrations first). No `PeriodicTask` yet — invalidation is event-driven.

Full docs (all English): `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/API.md`,
`docs/SCORING.md`, `docs/DEFERRED.md`, `docs/ROADMAP.md`, `docs/TASK.md`. Docs are
**LOCKED** for the physical scope.

**Workflow:** strict design-first — implementation starts at BCKND-1 but ONLY on an
explicit go ([[feedback_design_before_code]]). See [[project_sport_diagnostika]],
[[project_physical_readiness]].
</content>
</invoke>
