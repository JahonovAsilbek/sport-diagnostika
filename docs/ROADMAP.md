# SPORT-DIAGNOSTIKA.UZ — Roadmap (big blocks)

The project is split into 3 tracks. Each track has its own prefix; small tasks are
given with that prefix + a continuous number (for example `BCKND-1`, `DVPS-1`, `FRNTND-1`).

- **BCKND** — backend (Django + DRF, domain logic, API)
- **DVPS** — devops / infrastructure (Docker, deployment, CI, monitoring)
- **FRNTND** — frontend (Vue 3 SPA)

Source documents: `ARCHITECTURE.md` · `DATA_MODEL.md` · `API.md` · `SCORING.md`.

> Status: **blocks are locked**. Next step — break each block into small tasks
> (block by block, finish one before moving to the next).

---

## Cross-track dependency

```
        DVPS (infrastructure — supports both tracks)
          │
          ▼
        BCKND (as the API gets ready)
          │  API contract (docs/API.md)
          ▼
        FRNTND (depends on backend endpoints)
```

Ordering principle: a **BCKND block** delivers the API → the matching **FRNTND block**
consumes it. **DVPS** provides the environment at the start and deployment/monitoring at the end.

---

## BCKND — Backend blocks (in dependency order)

| Block | Name | Scope | Dependency |
|---|---|---|---|
| **B1** | Foundation | Django project, settings (dev/prod), base models (TimeStamped), DRF + OpenAPI, Celery app wiring, lint/test setup | — |
| **B2** | Identity & Access | User model, 5 roles, JWT (login/refresh/logout/me), permission framework, region/organization scoping foundation | B1 |
| **B3** | Reference Data | Region, District, Organization, SportType, Age/WeightCategory, TestType — model + API + admin + seed | B2 |
| **B4** | Norms | Norm + NormBand model, lookup/fallback logic, admin + API, versioning, seed | B3 |
| **B5** | Athletes | Athlete model, CRUD API, filter, age-category computation, scoping, coach linking | B3 |
| **B6** | Measurements | TestSession, Measurement, manual-entry API, validation, `finalize` trigger | B4, B5 |
| **B7** | Scoring engine ★ | Pure domain: BMI, norm→score, OTM/OPSTTM strategy, aggregation, level/color, Evaluation snapshot, recompute task | B4, B6 |
| **B8** | Rating & Ranking | RANK() queries, "Top Athletes", region ranking, Redis cache + invalidation | B7 |
| **B9** | Comparison | Side-by-side endpoint for 2–3 athletes | B7 |
| **B10** | Recommendations | RecommendationRule model, generation on `finalize`, API | B7 |
| **B11** | Excel import/export | Bulk upload pipeline (staging→validation→commit), template | B5, B6 |
| **B12** | Reports | Async PDF/Word/Excel (Celery), status/download, report types | B8 |
| **B13** | Audit & Stats | AuditLog (signal), dashboard/stats endpoints | B2 |

---

## DVPS — DevOps / infrastructure blocks

| Block | Name | Scope | Dependency |
|---|---|---|---|
| **D1** | Containerization | Dockerfile (backend), docker-compose: db (Postgres), redis, web, worker, beat | BCKND B1 |
| **D2** | Local dev environment | `.env` management, Makefile/scripts, hot-reload, seed commands | D1 |
| **D3** | Nginx + static | Reverse proxy, serving the SPA build, routing `/api` `/admin` `/media` | D1 |
| **D4** | CI pipeline | Lint (ruff), test (pytest), build check | D1 |
| **D5** | Production deploy | VPS provisioning, gunicorn, env/secret management, TLS (Let's Encrypt) | D3 |
| **D6** | Backup & restore | PostgreSQL automatic backup, restore procedure, media backup | D5 |
| **D7** | Monitoring & logging | Health-check, error tracking, log aggregation, uptime alert | D5 |

---

## FRNTND — Frontend blocks (Vue 3 SPA)

| Block | Name | Scope | Dependency (BCKND) |
|---|---|---|---|
| **F1** | Foundation | Vite + Vue 3 + Pinia + Router, UI kit, API client (axios), interceptor, auth store | — |
| **F2** | Auth & layout | Login page, JWT storage/refresh, route guard, app shell (navbar/sidebar), role-based menu | B2 |
| **F3** | Catalog UI | Reference data views (sport type/region/test type), management where needed | B3, B4 |
| **F4** | Athletes UI | Athlete list, filter, card page, CRUD form | B5 |
| **F5** | Measurements UI | Test entry forms, session, `finalize`, Excel import UI | B6, B11 |
| **F6** | Results UI | Athlete scoring result, BMI, level, color indicator, history | B7 |
| **F7** | Rating UI | Rating table, "Top Athletes", region ranking, filters | B8 |
| **F8** | Comparison UI | Side-by-side view for 2–3 athletes | B9 |
| **F9** | Recommendation & Report UI | Recommendations view, report request + download (async status) | B10, B12 |
| **F10** | Dashboard UI | Stats, charts, role-based home page | B13 |

---

## Estimated size

| Track | Blocks | Estimated tasks |
|---|---|---|
| BCKND | 13 | ~75–90 |
| DVPS | 7 | ~20–25 |
| FRNTND | 10 | ~45–55 |
| **Total** | **30 blocks** | **~140–170 tasks** |

---

## Scope boundaries & open questions

| # | Topic | Status | Note |
|---|---|---|---|
| TZ #13 | **Training-load monitoring** (load low/at norm/high, recovery insufficient) | ⏳ **To be asked of the client** | Skipped for now. New block (`B14`), inside Evaluation, or a later stage — decision after the client's answer. **Remind the user next session.** |
| TZ #6, #18 | **Device integration** (Polar H10, spirography, etc.) | ❌ **Out of scope** | No work now. **All metrics are entered manually.** May be revisited in the future. |
| Gap | **Personal-data / PII protection** (minors' health & biometric data, consent, retention, view-access logging) | ⏳ **Open** | Left open for now; revisit before go-live (legal/compliance implications). |
| Gap | **Athlete duplicate prevention** (no unique national ID in the model) | ⚠️ **Known limitation** | No technical de-dup. Mitigation: **train moderators not to enter duplicates.** |
| Gap | **Bulk norm import** | ❌ **Not now** | Norms are **entered manually** via admin. No bulk-import tooling planned for now. |
| Gap | **Email / notifications** (password reset, report-ready, account created) | ❌ **Deferred** | No email/SMS backend for now. "Forgot password" UI has no backend flow yet. |
| Gap | **Initial data migration** from the client's existing Excel | 📌 **Planned later** | An Excel file exists; its template + import will be worked out in detail later. |
| Gap | **Report branding** (official letterhead, logo, signature blocks) | ⏳ **Ask the client** | Open question — report format/branding to be confirmed with the client. |
| Gap | **Staging environment** | ❌ **Out of scope** | Only two people on the project (dev + owner); dev + prod is enough. |

---

## Working order (agreed)

1. The blocks are **locked** in this document (current state).
2. Then, block by block, small tasks are created (`docs/TASK.md`), and we **do not
   start the next until the current one is finished**.
3. Recommended starting order: `DVPS-D1` + `BCKND-B1` (foundation) →
   `BCKND-B2` (auth) → `FRNTND-F1/F2` ... — once a backend block delivers its API,
   the matching frontend block hooks in.
