---
name: project_architecture
description: "SPORT-DIAGNOSTIKA backend/full-app architecture decisions — stack, modules, scale approach"
metadata: 
  node_type: memory
  type: project
  originSessionId: b9ce4b4d-c064-40c7-9573-f3ffc2d7c413
---

The static landing (lite at root, premium under `premium/`) is evolving into a
full **Python web platform** built from `SPORT.docx` (TTZ). Architecture agreed
2026-06-16, implementation not yet started.

**Stack (decided):** Django 5 + DRF · Vue 3 + Vite + Pinia SPA · PostgreSQL 16 ·
Celery + Redis (fon + cache) · JWT auth · Docker Compose on own VPS · Nginx +
Gunicorn. Reports: openpyxl/python-docx/WeasyPrint in Celery.

**Pattern:** modular monolith (NOT microservices — 3000–5000 users is small;
microservices would be over-engineering). Django apps = modules with clean
layers (domain/services/selectors, HackSoft styleguide).

**Modules + dependency direction (downward only):** accounts (auth + region-scope)
→ catalog (reference data + scoring NORMS) → athletes → measurements → scoring
(★ pure domain engine, OTM/OPSTTM strategies) → rating/recommendations/comparison
→ reports. Cross-cutting: audit, import/export, admin.

**Critical domain rules:** (1) scoring norms are DATA not code — thresholds keyed
by age-cat × gender × sport × test-type, admin-managed. (2) Two blocks = two
eval strategies: OTM (10 tests × 1–5 = 50pts → % → 5 levels) vs OPSTTM (4
indicators, 3 levels Yuqori/Me'yor/Past). (3) TVI = vazn/bo'y². (4) Ratings are
cached + recomputed on change (Postgres RANK() OVER). (5) Region-scoping is the
security core. 5 roles: Super admin, Viloyat admin, Murabbiy, Laboratoriya
xodimi/operator, Vazirlik vakili.

**Scoring model (locked, see `docs/DATA_MODEL.md`):** each test → 1–5 points via
Norm/NormBand. OTM = 10 tests (5 physical + 5 functional) = 50 pts → % → 5 levels;
TVI is informational only (NOT in the 50). OPSTTM = 4 categories (physical 5,
functional 5, morpho 7 incl. TVI, psych 6), each → category %, overall % = average
of the 4 (categories equal-weighted), → 3 levels (yuqori/me'yor/past).
ranking_score = overall % for BOTH blocks (one rating table). Evaluation is a
stored snapshot (Evaluation + IndicatorScore). age_category & block are derived,
not stored. Coach = User(role=coach).

Full docs (all English): `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`,
`docs/API.md`, `docs/SCORING.md`, `docs/ROADMAP.md`, `docs/TASK.md`.

**Task breakdown DONE** (`docs/TASK.md`): 110 tasks ordered by dependency, not by
track — BCKND-1..67 (B1–B13), DVPS-1..19 (D1–D7), FRNTND-1..24 (F1–F10). Cross-track
DVPS tasks sit with the backend block that needs them (DVPS-7 beat scheduler for B8,
DVPS-8 media volume for B11/B12, DVPS-9 WeasyPrint libs for B12). Format: `# PREFIX-N
— Title` + what/how + `Edge case:` (style from orientedTV/docs/TASK.md). Open choices
flagged in tasks: TypeScript vs JS (FRNTND-1), UI kit PrimeVue vs Naive (FRNTND-4).
Next step: implementation, starting BCKND-1 — but ONLY on an explicit go
([[feedback_design_before_code]]).
See [[project_sport_diagnostika]].
