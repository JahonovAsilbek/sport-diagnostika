# SPORT-DIAGNOSTIKA.UZ — Architecture

Physical-readiness monitoring platform for student-athletes.
Source specification: `SPORT.docx` (technical spec, TTZ) + the client's
**physical-readiness criteria** (`Jismoniy tayyorgarlik mezonlari` tables).

> Status: **architecture agreed, physical-readiness scope.** Implementation not started.
> Parked design (OTM/OPSTTM dual strategy, functional / morphofunctional / psychological,
> BMI): `DEFERRED.md`. Models: `DATA_MODEL.md` · scoring: `SCORING.md` · API: `API.md`.

---

## 1. Goal and scope

Evaluation, monitoring and analysis of student-athletes' **physical readiness**, plus
**automatic selection of the top athletes**. The client delivered only the state
**"Jismoniy tayyorgarlik darajasi"** standard, so the platform is built
**physical-readiness end-to-end**; the functional, morphofunctional and psychological
categories (and BMI) are **parked** — see `DEFERRED.md` — until the client provides their
criteria.

- Scope now: **physical readiness only** — the single category with real criteria today.
- Scale: **3000–5000 users** (role holders). Athlete records may be
  considerably more.
- Requirements: clean architecture, easy to maintain, online + mobile
  friendly, fast, secure.

At this scale **microservices are not needed** — that would be
over-engineering. Chosen path: **modular monolith** (single deploy, with
strictly bounded modules inside).

## 2. Technology stack

| Layer | Technology |
|---|---|
| Backend | Django 5 + Django REST Framework |
| DB | PostgreSQL 16 |
| Background jobs | Celery + Redis (broker), Celery Beat (scheduled jobs) |
| Cache | Redis |
| Auth | JWT (djangorestframework-simplejwt), access/refresh |
| Admin (TTZ #16) | Django admin — reference data management |
| Reports | openpyxl (Excel), python-docx (Word), WeasyPrint (PDF) — on Celery |
| Excel import | openpyxl + staging (validation → confirmation → commit) |
| Frontend | Vue 3 + Vite + Pinia + Vue Router (+ PrimeVue/Naive UI) |
| Web server | Nginx (SPA build + `/api/*` reverse proxy) |
| App server | Gunicorn (Django WSGI) |
| Container | Docker Compose |

## 3. Core domain rules (physical readiness)

**One scheme, block-independent.** A raw exercise result → **points (10 / 8 / 6)** via the
`Norm` + `NormBand` table; the 5 battery exercises sum to a **total (0–50)**, which maps to
a **daraja (I / II / III / none)** via `DarajaThreshold`:

| physical_total | daraja | color |
|---|---|---|
| 48–50 | I daraja | 🟢 green |
| 38–46 | II daraja | 🟡 yellow |
| 30–36 | III daraja | 🔴 red |
| < 30 | none (nishonsiz) | 🔴 red |

The 5 exercises are chosen per `(age category × gender)` from a ~9-exercise pool
(`TestBattery` / `BatteryItem`). The standard is **universal by age × gender** — there is
no sport type and no OTM/OPSTTM block in scoring. Full algorithm: `SCORING.md`.

**Critical architecture decisions:**

1. **Norms, level thresholds and recommendation rules are DATA, not code.** `NormBand`
   holds the raw-range → points (10/8/6) bands, keyed by `(exercise × age range × gender)`
   — **no sport type, no block**. `DarajaThreshold` holds the total → daraja bounds. Both
   are admin-managed; the scoring engine reads them and converts raw results into points
   and a daraja. Never hardcoded.
2. **One scoring scheme** — a single engine (points → total → daraja). The old two-strategy
   OTM/OPSTTM polymorphism (`OtmEvaluationStrategy` / `OpsttmEvaluationStrategy`) is
   **parked** in `DEFERRED.md`; `Organization.type (OTM|OPSTTM)` survives only as a
   **classification / filter / reporting** attribute and does **not** drive scoring.
3. **Rating is read-oriented heavy aggregation.** It is cached, with
   invalidation/recomputation when data changes. PostgreSQL
   `RANK() OVER (PARTITION BY region, sport_type, age_category, gender ORDER BY ranking_score DESC)` —
   **block dropped** from the partition; `sport_type` stays as a filter/partition dimension
   (from the athlete) though norms are sport-independent.
4. **Report generation is on a background queue** (does not block HTTP).
5. **Region-scoping is the security core.** A region admin sees only their
   own region, a coach only their own athletes. A mandatory filter on
   every request.

**5 roles:** Super admin · Region admin · Coach · Lab operator
(lab_operator) · Ministry representative.

## 4. Deploy topology (VPS + Docker Compose)

```
                          VPS (single server)
   ┌──────────────────────────────────────────────────────────┐
   │  Nginx :443  → SPA static build (Vue)                      │
   │              → /api/* reverse proxy → Gunicorn (Django) ×2 │
   │                                                            │
   │  Celery Worker (reports, import, rating)                   │
   │  Celery Beat (scheduled rating recomputation)              │
   │  Redis (broker + cache)                                    │
   │  PostgreSQL (volume)                                       │
   │  /media (report files)                                     │
   └──────────────────────────────────────────────────────────┘

   compose services: nginx · web · worker · beat · db · redis
```

## 5. Module (service) decomposition

Dependencies only point downward.

```
  IDENTITY & ACCESS  ◄── everything depends on it (auth + region-scope)
        │
  REFERENCE DATA (catalog)  ◄── region, district, sport type, organization,
        │                       AgeCategory (TOIFA), Exercise pool, TestBattery,
        │                       Norm/NormBand, DarajaThreshold
  ATHLETES (registry)
        │
  MEASUREMENTS (manual + Excel import — raw results for the 5 battery exercises)
        │
  SCORING ENGINE ★  (raw → points 10/8/6 → physical_total → daraja + color — single scheme)
        ├──────────────┬──────────────┐
  RATING/RANKING   RECOMMENDATIONS   COMPARISON
        │
  REPORTS (PDF/Word/Excel — background job)

  Cross-cutting: AUDIT LOG · IMPORT/EXPORT · ADMIN
```

| Module (Django app) | Responsibility | Depends on |
|---|---|---|
| `accounts` | User, 5 roles, JWT, region-scoping | — |
| `catalog` | Reference data: Exercise, AgeCategory (TOIFA), TestBattery/BatteryItem, Norm/NormBand, DarajaThreshold, Organization (type = classification) | accounts |
| `athletes` | Athlete card | catalog |
| `measurements` | Test session, raw results (5 battery exercises), Excel import | athletes, catalog |
| `scoring` ★ | raw → points (10/8/6) → physical_total → daraja + color (single-scheme, pure domain) | measurements, catalog |
| `rating` | Rating, "Top Athletes", region rating (cache) | scoring |
| `recommendations` | Rule-based recommendation text | scoring |
| `comparison` | 2–3 athletes side by side | scoring |
| `reports` | PDF/Word/Excel (Celery) | rating, scoring, athletes |
| `common` | Audit, base model, permission, mixin | — |

## 6. Key flow — "Top Athletes"

```
filter (sport type + region + age category + gender)
  → region-scope check (accounts)
  → rating: is it in cache? ── yes → return
       │ no
  → scoring engine (measurements raw + catalog norms → points 10/8/6 via NormBand
                    → physical_total 0–50 → daraja via DarajaThreshold)
  → PostgreSQL RANK() OVER (PARTITION BY region, sport_type, age_category, gender
                            ORDER BY ranking_score DESC)      # ranking_score = physical_total
  → result into Redis cache (TTL + invalidation)
  → TOP list + daraja + colored indicator (🟢🟡🔴)
```

## 7. Layers inside a Django app (clean architecture)

HackSoft styleguide approach — logic lives outside views/models:

```
apps/scoring/
├── models.py
├── domain/        # PURE Python (no Django import, fully unit-testable)
│   ├── battery.py   # resolve age × gender → the ordered 5 exercises (TestBattery)
│   ├── points.py    # raw_value → points 10/8/6 via NormBand + clamp
│   └── daraja.py    # physical_total → daraja (I/II/III/none) + color via DarajaThreshold
├── services.py    # use-cases (write logic — finalize → Evaluation snapshot)
├── selectors.py   # read queries
├── serializers.py · api.py · tasks.py
└── tests/
```

This makes it possible to test the evaluation logic in isolation, without a DB.

## 8. Project repository structure (proposal)

```
backend/      Django + DRF (the apps/ structure above)
frontend/     Vue 3 + Vite SPA
deploy/       docker-compose.yml, nginx conf, env samples
docs/         ARCHITECTURE.md (this file), then ERD, API spec
landing/      existing static landing (index.html, premium/) — to be moved
```
> Note: the current static landing is at the repo root. When backend/frontend
> are added, the final layout will be decided.
