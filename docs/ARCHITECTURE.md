# SPORT-DIAGNOSTIKA.UZ — Architecture

Functional and physical monitoring platform for student-athletes.
Source specification: `SPORT.docx` (technical spec, TTZ).

> Status: **architecture agreed**, implementation not started.
> Next step: data model (ERD).

---

## 1. Goal and scope

Evaluation, monitoring and analysis of the physical, functional,
morphofunctional and psychological state of OTM (higher-education
institutions) student-athletes and OPSTTM (olympic/paralympic prep
centers) student-athletes, plus **automatic selection of the top athletes**.

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

## 3. Core domain rules (from TTZ)

**Two blocks, two evaluation logics:**

| | OTM block | OPSTTM block |
|---|---|---|
| Indicators | BMI + Physical(5) + Functional(5) | BMI + Physical + Functional + Morphofunctional + Psychological |
| Evaluation | 10 tests × 1–5 points = 50 points → percentage | each indicator: High/Normal/Low |
| Levels | 5: 90–100 very high · 75–89 high · 60–74 medium · 40–59 low · 0–39 very low | 3: High/Normal/Low |

**BMI:** `weight(kg) / height(m)²` → 6 categories (<16 … 35+).

**Critical architecture decisions:**

1. **Evaluation norms are DATA, not code.** Point/level thresholds are
   stored along the `(age category × sex × sport type × test type)`
   dimension. Managed by the admin. The scoring engine reads the norms and
   converts the raw result into points/level. Never hardcoded.
2. **Two blocks = two strategies** (polymorphism): `OtmEvaluationStrategy`,
   `OpsttmEvaluationStrategy` — behind a single interface.
3. **Rating is read-oriented heavy aggregation.** It is cached, with
   invalidation/recomputation when data changes. PostgreSQL
   `RANK() OVER (PARTITION BY ...)`.
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
  REFERENCE DATA (catalog)  ◄── region, district, sport type, age/weight cat.,
        │                       organization, test type, NORMS
  ATHLETES (registry)
        │
  MEASUREMENTS (manual + Excel import)
        │
  SCORING ENGINE ★  (BMI, points, percentage, level, color — OTM/OPSTTM strategy)
        ├──────────────┬──────────────┐
  RATING/RANKING   RECOMMENDATIONS   COMPARISON
        │
  REPORTS (PDF/Word/Excel — background job)

  Cross-cutting: AUDIT LOG · IMPORT/EXPORT · ADMIN
```

| Module (Django app) | Responsibility | Depends on |
|---|---|---|
| `accounts` | User, 5 roles, JWT, region-scoping | — |
| `catalog` | Reference data + evaluation norms | accounts |
| `athletes` | Athlete card | catalog |
| `measurements` | Test session, raw result, Excel import | athletes, catalog |
| `scoring` ★ | BMI, raw→points→percentage→level→color (pure domain) | measurements, catalog |
| `rating` | Rating, "Top Athletes", region rating (cache) | scoring |
| `recommendations` | Rule-based recommendation text | scoring |
| `comparison` | 2–3 athletes side by side | scoring |
| `reports` | PDF/Word/Excel (Celery) | rating, scoring, athletes |
| `common` | Audit, base model, permission, mixin | — |

## 6. Key flow — "Top Athletes"

```
filter (sport type + region + age + sex)
  → region-scope check (accounts)
  → rating: is it in cache? ── yes → return
       │ no
  → scoring engine (measurements raw + catalog norms → points/level)
  → PostgreSQL RANK() OVER (PARTITION BY ... ORDER BY points DESC)
  → result into Redis cache (TTL + invalidation)
  → TOP list + colored indicator (🟢🟡🔴)
```

## 7. Layers inside a Django app (clean architecture)

HackSoft styleguide approach — logic lives outside views/models:

```
apps/scoring/
├── models.py
├── domain/        # PURE Python (no Django import, fully unit-testable)
│   ├── strategies.py   # Otm/Opsttm evaluation strategies
│   ├── tvi.py          # BMI formula + categories
│   └── levels.py       # points→percentage→level→color
├── services.py    # use-cases (write logic)
├── selectors.py   # read queries
├── serializers.py · api.py · tasks.py
└── tests/
```

This makes it possible to test the complex evaluation logic in isolation,
without a DB.

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
