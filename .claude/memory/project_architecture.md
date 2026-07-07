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
2026-06-16; **pivoted to physical-readiness-first 2026-07-07**; implementation not
yet started.

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

Full docs (all English): `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/API.md`,
`docs/SCORING.md`, `docs/DEFERRED.md`, `docs/ROADMAP.md`, `docs/TASK.md`. Docs are
**LOCKED** for the physical scope.

**Workflow:** strict design-first — implementation starts at BCKND-1 but ONLY on an
explicit go ([[feedback_design_before_code]]). See [[project_sport_diagnostika]],
[[project_physical_readiness]].
</content>
</invoke>
