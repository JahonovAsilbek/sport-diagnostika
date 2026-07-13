# TRACEABILITY — TZ → task matrix + UAT checklist (DVPS-20)

This is the **QA acceptance basis**: it maps every requirement of the customer spec
(`SPORT.docx`, the TTZ) to the task(s) that implement it and to a concrete acceptance
check, then gives a UAT checklist for client sign-off.

**Source of truth precedence:** `docs/TASK.md` (tasks) > `SPORT.docx` (TZ) > the other
`docs/`. When a task changes, update the matching row here. Requirement names are kept in
the TZ's Uzbek with an English gloss; task IDs reference `docs/TASK.md`.

**Scope note — physical-first.** The platform was re-scoped to the **physical-readiness**
standard first (10/8/6 points × exercises → `physical_total` 0–50 → daraja I/II/III). The
**functional**, **morphofunctional**, and **psychological** criteria in the TZ are parked
until the client delivers their real structure (`docs/DEFERRED.md`). Those show as
**Deferred** below — they are coverage gaps by design, not omissions.

**Status legend:** ✅ Done · 🟡 Partial (physical scope done; a slice deferred) ·
⛔ Deferred (awaiting client criteria). At the time of writing **115 of 116 non-deferred
tasks are complete** (only DVPS-20, this document, was open); every "Done" row below is
backed by merged + tested code.

---

## A. TZ requirement traceability

| # | TZ requirement (Uzbek → gloss) | Status | Implementing task(s) | Acceptance check |
|---|--------------------------------|--------|----------------------|------------------|
| 1 | **Sportchi bazasi** — athlete personal e-card | 🟡 | BCKND-34/35/36/37, BCKND-68 (transfer history), FRNTND-10/11/12 | Create an athlete via `/api/v1/athletes/` with FISh, birth year, gender, region, district, organization, sport, age category (TOIFA, auto), coach; the card page renders them; a scoped user only sees in-scope athletes. **Deferred fields:** weight category (DEF-1), height/weight/BMI/training staj/competitions (DEF-5, morphofunctional). |
| 2 | **Hududlar bo'yicha ajratish** — 14 regions (incl. Karakalpakstan + Tashkent city) | ✅ | BCKND-17, BCKND-23 (seed), BCKND-14/20/37 (scoping), FRNTND-10/19 | Region/District seeded for all 14 regions; athlete list filters by region; `/rating/regions/` breaks down by region; region_admin sees only their region. |
| 3 | **Sport turlari bo'yicha saralash** — filter/rank by sport | ✅ | BCKND-18, BCKND-23 (seed sports), BCKND-36 (filters), BCKND-49/50, FRNTND-18 | Pick a sport on the rating view → ranking filters to that sport type. |
| 4 | **Yosh kategoriyasi bo'yicha saralash** — per-age norms | ✅ | BCKND-18 (AgeCategory/TOIFA), BCKND-35, BCKND-23, BCKND-26/32 (per-age norms) | An athlete's TOIFA is derived from birth year; scoring uses the age-appropriate norm; rating filters by age category. |
| 5 | **Jismoniy tayyorgarlik testi** — physical test battery | ✅ | BCKND-19 (Exercise/Battery), BCKND-24 (seed), BCKND-39/40 (session+entry), BCKND-26/27/44 (norms→points), FRNTND-13 | Open a session for an athlete; the battery presents the age×gender exercises; entering a raw value auto-converts to 10/8/6 points via the norm bands. |
| 6 | **Funksional tayyorgarlik testi** — HR/Polar H10/VO₂/spirography… | ⛔ | DEF-2 (functional test types), DEF-6 (non-physical evaluation), Polar H10 = TZ #18 future | **Gap — deferred.** No functional criteria delivered yet; blocked in `DEFERRED.md §2`. Client action required (open question). |
| 7 | **Avtomatik baholash tizimi** — auto scoring → total | 🟡 | BCKND-43 (Evaluation), BCKND-44 (points), BCKND-45 (daraja), BCKND-46 (service), BCKND-28 (thresholds) | Finalize a session → an Evaluation snapshot with `physical_total` (0–50) + daraja I/II/III. **Deviation:** the TZ's 85–100/65–84/0–64 **percentage** bands (physical+functional) were re-scoped to physical `0–50 → daraja` (functional half deferred; percentage scheme parked as DEF-4). Documented in `docs/SCORING.md`. |
| 8 | **Avtomatik reyting** — rank high→mid→low across dimensions | 🟡 | BCKND-49 (RANK selectors), BCKND-50 (rating API), BCKND-51 (cache), BCKND-70 + FRNTND-26 (period), FRNTND-18 | `/rating/top/` ranks athletes high→low within a (region, sport, age, gender) partition; results snapshot the dimensions. **Partial:** organization / OPSTTM-vs-OTM breakdown is on the dashboard (`by_organization_type`), not a ranking partition. |
| 9 | **Rangli indikator** — green/yellow/red | ✅ | BCKND-43/45 (color on snapshot), FRNTND (DarajaBadge severities) | Daraja I → green, II → yellow, III → red badge everywhere an evaluation shows. |
| 10 | **Sportchini solishtirish** — compare 2–3 athletes | ✅ | BCKND-53/54, FRNTND-20, BCKND-70 + FRNTND-26 (period) | Pick 2–3 athletes → side-by-side matrix; the leader and per-exercise winners are highlighted. |
| 11 | **Viloyatlar reytingi** — region ranking | ✅ | BCKND-50 (`/rating/regions/`), FRNTND-19 | The regions tab ranks regions by daraja-I count / average; visible to ministry/super_admin (and a region_admin for their own region). |
| 12 | **Sport turi bo'yicha eng kuchlilar** — strongest per sport | ✅ | BCKND-49/50, FRNTND-18 | Filter the rating by a sport → the strongest athletes for that sport are listed top-down. |
| 13 | **Mashg'ulot yuklamasini nazorat** — training-load status | ⛔ | (none — parked) | **Gap — deferred.** Training-load criteria not delivered; tracked as an open question (`project_open_questions`). Client action required. |
| 14 | **Tavsiya berish moduli** — recommendations | ✅ | BCKND-55/56/57, FRNTND-21, FRNTND-9 (RulesManager) | Finalizing a session generates recommendations from the **data-driven** rule set (thresholds are data, not code); a super_admin edits the rules via the UI. |
| 15 | **Hisobot chiqarish** — PDF/Word/Excel reports | 🟡 | BCKND-62/63/64, DVPS-9 (WeasyPrint), FRNTND-22, period via BCKND-70 | Request an athlete/region/sport/republic report → async build → download in PDF/Word/Excel. **Partial:** dedicated OPSTTM / OTM-student report *types* are folded into org-type filtering; separate non-physical report types are deferred (DEF-7). |
| 16 | **Admin panel** — manage catalog + criteria | ✅ | BCKND-22 (catalog admin), BCKND-31 (norms/thresholds admin), BCKND-15 (users), FRNTND-9 | A super_admin manages users, sports, regions, age categories, organizations, coaches, scoring norms/thresholds, and reports via Django admin + the SPA management views. |
| 17 | **Foydalanuvchi rollari** — 5 roles, scoped | ✅ | BCKND-10 (roles), BCKND-13 (permissions), BCKND-14 (scoping), BCKND-69 (login security), FRNTND-6 (guards) | super_admin (all), region_admin (own region), coach (own athletes), lab_operator (data entry), ministry (read-only stats) — each sees only its scope, enforced server-side. |
| 18 | **Ma'lumot kiritish** — manual + Excel bulk (Polar H10 future) | 🟡 | BCKND-40 (manual entry) + FRNTND-13; BCKND-58/59/60 (import) + FRNTND-15 | Enter results manually in a session **and** bulk-upload via the Excel template (validated async, then committed). **Future:** Polar H10 / device integration (deferred with TZ #6). |
| — | **Asosiy texnik topshiriq** — unified base → auto analysis → rank → select → recommend | 🟡 | Whole system (rows 1–18) | End-to-end: enter physical data → auto-score → rank/compare/report → recommend. Functional/morphofunctional half of the "unified base" deferred. |
| ★ | **"Eng kuchli sportchilarni aniqlash" tugmasi** — the Top-Athletes selector (the TZ's single most-emphasised feature) | ✅ | BCKND-49/50, FRNTND-18 | On the rating view pick sport + region + age + gender → the **Top Athletes** podium/list returns the highest-scoring athletes automatically. |

---

## B. Coverage gaps & deferred items (surfaced for the client)

Every gap traces to missing client criteria and is parked in `docs/DEFERRED.md` — none is
an implementation miss.

- **TZ #6 Funksional tayyorgarlik** ⛔ — functional test types + scoring (`DEF-2`, `DEF-6`).
- **TZ #13 Mashg'ulot yuklamasi** ⛔ — training-load model + thresholds (open question).
- **TZ #1 morphofunctional fields** 🟡 — weight category (`DEF-1`), BMI/height/weight/staj/
  competitions (`DEF-5`).
- **TZ #7 scoring bands** 🟡 — physical `0–50 → daraja` shipped; the TZ's percentage
  (85/65) + functional-inclusive scheme is parked (`DEF-4`).
- **TZ #15 report types** 🟡 — OPSTTM / OTM-student dedicated report types (`DEF-7`).
- **TZ #18 device integration** 🟡 — Polar H10 and other devices (future, with #6).

**Action for the client:** deliver the functional / morphofunctional / psychological
criteria (their real structure) to unblock #6, #13, and the deferred fields — same way the
physical criteria unblocked #1–#5, #7.

---

## C. Cross-cutting / platform (supporting all TZ features)

| Area | Task(s) | Acceptance check |
|------|---------|------------------|
| Auth (JWT login/refresh/logout/me) | BCKND-11/12, BCKND-16 | Log in → receive tokens; refresh; logout blacklists; `/me` returns the profile. |
| Region/org scoping framework | BCKND-14/20, applied per app | Every list/detail is filtered server-side by the caller's scope; client filters can't widen it. |
| Snapshot integrity | BCKND-39 (sessions), BCKND-43 (evaluations), BCKND-68 (transfers) | A transfer/edit never rewrites past rankings — dimensions are snapshotted. |
| Audit log | BCKND-65/67 | Mutations of audited models emit an AuditLog row. |
| Dashboard / stats | BCKND-66, FRNTND-23/24 | Home shows KPIs, daraja distribution, region bars, OTM/OPSTTM split. |
| Caching + recompute | BCKND-47 (recompute), BCKND-51 (cache) | Rating responses cache per filter set; invalidated on new evaluations. |
| Login security | BCKND-69 | Throttling + (username, IP) lockout after N failures; generic no-enumeration error. |
| Period filter | BCKND-70 + FRNTND-26 | Rating/comparison/history/reports accept an optional quarter/half/year; absent → latest. |
| i18n (uz/ru/kk/en) | FRNTND-25 | UI chrome switches locale (persisted); reference content stays Uzbek; kk falls back to uz. |
| Containerisation | DVPS-1..9 | `docker compose` brings up db/redis/web/worker/beat; reports render (WeasyPrint). |
| CI / deploy / TLS | DVPS-14/15/16 | CI runs ruff + `ruff format --check` + pytest + docker build on push; VPS deploy behind nginx + Let's Encrypt. |
| Backups / monitoring / logging | DVPS-17/18/19 | Scheduled DB+media backup with restore; health checks + uptime; centralised logs + error tracking. |

---

## D. UAT checklist — client sign-off

Run on a seeded staging instance. Each item is pass/fail; capture a note on any fail.
Group 1 gates the rest (nothing works without auth + scope).

### 1. Access & roles (TZ #17)
- [ ] Log in as **super_admin** → see all navigation + all regions' data.
- [ ] Log in as **region_admin** → athletes/rating limited to own region; no other region visible.
- [ ] Log in as **coach** → only own athletes; can enter data; cannot manage users/norms.
- [ ] Log in as **lab_operator** → can enter measurements; read-only elsewhere.
- [ ] Log in as **ministry** → read-only statistics + rating; no data entry.
- [ ] Wrong password ×N → account temporarily locked; error does not reveal which field was wrong.
- [ ] Switch UI language uz → ru → kk → en; choice persists on reload; region/sport names stay Uzbek.

### 2. Athlete base & data entry (TZ #1, #18)
- [ ] Create an athlete with all physical fields; TOIFA age category is derived automatically.
- [ ] Athlete card shows identity, scope, sessions, and the evaluation tab.
- [ ] Transfer an athlete to a new region/org → history records the move; past evaluations unchanged.
- [ ] Enter a measurement session manually → each raw value shows its 10/8/6 points.
- [ ] Download the Excel template → bulk-upload → validation errors shown per row → commit succeeds.

### 3. Scoring & indicators (TZ #5, #7, #9)
- [ ] Finalize a session → Evaluation shows `physical_total` /50 + daraja I/II/III.
- [ ] Daraja renders green (I) / yellow (II) / red (III).
- [ ] Below-threshold total shows "Nishonsiz"; not-yet-evaluated shows "Baholanmagan".

### 4. Rating, Top Athletes & regions (TZ #2, #3, #4, #8, #11, #12, ★)
- [ ] **Top Athletes:** pick sport + region + age + gender → highest scorers listed automatically.
- [ ] Full rating table ranks high→low; row click opens the athlete card.
- [ ] Region ranking lists regions by daraja-I count / average.
- [ ] Apply a period (e.g. Q2 2026) → rating reflects latest-within-period; URL is shareable; clearing → latest.

### 5. Comparison (TZ #10)
- [ ] Compare 2–3 athletes → side-by-side matrix; leader + per-exercise winners highlighted.
- [ ] A comparison link (`?athletes=…&period_…`) reopens the same comparison.

### 6. Recommendations (TZ #14)
- [ ] A finalized athlete shows generated recommendations tied to weak indicators.
- [ ] super_admin edits a recommendation rule (threshold/text) → new evaluations reflect it.

### 7. Reports (TZ #15)
- [ ] Request an athlete report (PDF) → status polls pending→processing→done → download opens.
- [ ] Request region / sport / republic reports in Word and Excel → each downloads.
- [ ] Apply a period to a report → the output is scoped to that period; a bad combo is rejected.

### 8. Admin (TZ #16)
- [ ] super_admin manages catalog (regions/sports/age categories/organizations/coaches).
- [ ] super_admin manages scoring norms + daraja thresholds (data-driven, not code).
- [ ] super_admin manages users (create/scope/deactivate).

### 9. Deferred — confirm expectations with the client
- [ ] Functional readiness (TZ #6), training-load (TZ #13), morphofunctional fields, and device
      integration are **understood to be out of the current physical-first scope** pending criteria.
