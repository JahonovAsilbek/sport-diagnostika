# SPORT-DIAGNOSTIKA.UZ — Roadmap (big blocks)

The project is split into 3 tracks. Each track has its own prefix; small tasks are
given with that prefix + a continuous number (for example `BCKND-1`, `DVPS-1`, `FRNTND-1`).

- **BCKND** — backend (Django + DRF, domain logic, API)
- **DVPS** — devops / infrastructure (Docker, deployment, CI, monitoring)
- **FRNTND** — frontend (Vue 3 SPA)

Source documents: `ARCHITECTURE.md` · `DATA_MODEL.md` · `API.md` · `SCORING.md`.
Parked scope (functional / morphofunctional / psychological / OTM-OPSTTM): `DEFERRED.md`.

> Status: **blocks are locked, physical-readiness scope.** The project is built
> **physical-readiness-first** — the one category with real client criteria
> (`resources/Jismoniy tayyorgarlik mezonlari …`). Everything else is parked in
> `DEFERRED.md`, not deleted. Scoring is **10/8/6 points** per exercise, 5 exercises →
> **physical_total 0–50** → **daraja I/II/III**, universal by age × gender and
> block-independent.

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
| **B3** | Reference Data | Region, District, Organization, SportType, **AgeCategory (TOIFA 1–6)**, **Exercise pool**, **TestBattery + BatteryItem** — model + API + admin + seed | B2 |
| **B4** | Norms | **Norm(exercise, age_min/max, gender, valid_from)** + **NormBand(10/8/6)** + **DarajaThreshold** — lookup by numeric age (no sport/block), admin + API, versioning, `seed_physical` (the ~24 tables) | B3 |
| **B5** | Athletes | Athlete model, CRUD API, filter, TOIFA age-category computation, scoping, coach linking | B3 |
| **B6** | Measurements | TestSession, Measurement, **battery-driven 5-exercise entry**, validation, `finalize` trigger | B4, B5 |
| **B7** | Scoring engine ★ | Pure domain (single scheme): raw → points 10/8/6 via bands + clamp, Σ → physical_total, daraja via thresholds, Evaluation snapshot, recompute task | B4, B6 |
| **B8** | Rating & Ranking | RANK() by (region, sport_type, age_category, gender) — no block; "Top Athletes", region ranking, Redis cache + invalidation | B7 |
| **B9** | Comparison | Side-by-side endpoint for 2–3 athletes (physical_total, daraja, per-exercise points) | B7 |
| **B10** | Recommendations | RecommendationRule model (conditions on points/total), generation on `finalize`, API | B7 |
| **B11** | Excel import/export | Bulk upload of **physical** measurements (staging→validation→commit), template | B5, B6 |
| **B12** | Reports | Async PDF/Word/Excel (Celery) on physical results, status/download, report types | B8 |
| **B13** | Audit & Stats | AuditLog (signal), dashboard/stats endpoints (counts by daraja) | B2 |

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
| **F3** | Catalog UI | Reference data views (sport type/region/**exercise/battery**), norm + bands editor where needed | B3, B4 |
| **F4** | Athletes UI | Athlete list, filter, card page (daraja + TOIFA), CRUD form | B5 |
| **F5** | Measurements UI | **Physical battery entry form** (the 5 age×gender-specific inputs, auto-score), session, `finalize`, Excel import UI | B6, B11 |
| **F6** | Results UI | **physical_total + daraja + color + per-exercise points**, history | B7 |
| **F7** | Rating UI | Rating table (rank + daraja + color), "Top Athletes", region ranking, filters | B8 |
| **F8** | Comparison UI | Side-by-side view for 2–3 athletes | B9 |
| **F9** | Recommendation & Report UI | Recommendations view, report request + download (async status) | B10, B12 |
| **F10** | Dashboard UI | Stats (by daraja), charts, role-based home page | B13 |

---

## Estimated size

| Track | Blocks | Active tasks |
|---|---|---|
| BCKND | 13 | ~66 (a few parked in `DEFERRED.md`) |
| DVPS | 7 | ~20 |
| FRNTND | 10 | ~26 |
| **Total** | **30 blocks** | **~110 active** (+ a small parked set) |

> The physical-first re-scope removed several tasks (functional/morpho/psych/BMI
> scoring, OTM/OPSTTM strategies, weight categories); they are **parked, not deleted**
> — see the DEFERRED section at the end of `docs/TASK.md` and `docs/DEFERRED.md`.

---

## Scope boundaries & open questions

| # | Topic | Status | Note |
|---|---|---|---|
| Pivot | **Physical-readiness-first scope** | ✅ **Decided (2026-07)** | Only the state *"Jismoniy tayyorgarlik darajasi"* standard exists today; we build it end-to-end. Model in `DATA_MODEL.md`/`SCORING.md`. |
| Parked | **Functional / morphofunctional / psychological / BMI** categories + the **OTM/OPSTTM dual-strategy** scoring | 🅿️ **Deferred → `DEFERRED.md`** | Criteria not delivered by the client and their real structure may differ. `Organization.type` (OTM\|OPSTTM) is kept as a **classification/filter** attribute only, not a scoring axis. Revisit when criteria arrive. |
| Open | **TOIFA 4/5 boundary** within ages 13–17 | ⏳ **Ask the client** | Confirm exactly how the 13–17 span splits into the 4th/5th toifa (`SCORING.md` §11). |
| Open | **Below-worst-band / above-best clamp** | ⏳ **Confirm** | Worse than the worst band → 0 (below norm); better than the best band → 10. Confirm this is the intended behavior (`SCORING.md` §3.5, §11). |
| Open | **`birth_date` vs `birth_year`** | ⏳ **Confirm precision** | Norms are per single year (7–17); a full `birth_date` gives the correct age at the session date. Confirm the required precision. |
| Open | **"Maxsus talab boʻyicha"** — a second (general) norm tier? | ⏳ **Ask the client** | The tables mention a special-requirement tier; confirm whether it implies a second norm set (`SCORING.md` §11). |
| Open | **`DarajaThreshold` constant across tables?** | ⏳ **Confirm** | The daraja cut-offs appear fixed at 48/38/30, but confirm they hold for every table; they live in data so they can change without code. |
| TZ #13 | **Training-load monitoring** (load low/at norm/high, recovery insufficient) | ⏳ **To be asked of the client** | Skipped for now. A later stage or a new block after the client's answer. **Remind the user next session.** |
| TZ #6, #18 | **Device integration** (Polar H10, spirography, etc.) | ❌ **Out of scope** | No work now. **All metrics are entered manually.** May be revisited later. |
| Gap | **Personal-data / PII protection** (minors' health & biometric data, consent, retention, view-access logging) | ⏳ **Open** | Left open for now; revisit before go-live (legal/compliance). |
| Gap | **Athlete duplicate prevention** (no unique national ID in the model) | ⚠️ **Known limitation** | No technical de-dup. Mitigation: **train moderators not to enter duplicates.** |
| Gap | **Initial data / norm loading** | ✅ **`seed_physical`** | The client's physical tables (`resources/Jismoniy tayyorgarlik mezonlari …`) load via the idempotent `seed_physical` command (B4). Bulk norm import for other categories stays parked (`DEFERRED.md`). |
| Gap | **Email / notifications** (password reset, report-ready, account created) | ❌ **Deferred** | No email/SMS backend for now. "Forgot password" UI has no backend flow yet. |
| Gap | **Report branding** (official letterhead, logo, signature blocks) | ⏳ **Ask the client** | Report format/branding to be confirmed with the client. |
| Gap | **Staging environment** | ❌ **Out of scope** | Only two people on the project (dev + owner); dev + prod is enough. |

---

## Working order (agreed)

1. The blocks are **locked** in this document (current state, physical-readiness scope).
2. Then, block by block, small tasks are created (`docs/TASK.md`), and we **do not
   start the next until the current one is finished**.
3. Recommended starting order: `DVPS-D1` + `BCKND-B1` (foundation) →
   `BCKND-B2` (auth) → `FRNTND-F1/F2` ... — once a backend block delivers its API,
   the matching frontend block hooks in.
