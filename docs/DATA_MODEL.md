# SPORT-DIAGNOSTIKA.UZ — Data Model (ERD)

Source: `SPORT.docx` (TTZ) + the client's **physical-readiness criteria**
(`resources/Jismoniy tayyorgarlik mezonlari …`). Architecture: `ARCHITECTURE.md`.
Parked design (OTM/OPSTTM, functional/morpho/psych): `DEFERRED.md`.

> Status: **physical readiness implemented** (§0–§5). **Diagnostics (psychological
> questionnaires + functional indicators) designed** in §6 (B14, 2026-10) from the
> client's Aug–Sep 2026 materials — a separate module that leaves the physical model
> untouched. Morphofunctional/BMI remain parked (`DEFERRED.md`).

---

## 0. Scope decision (2026-07)

The client delivered only the state **"Jismoniy tayyorgarlik darajasi"** standard.
We build **physical readiness end-to-end** and defer the rest. Key facts driving the
model:

- Scoring is **10 / 8 / 6 points** per exercise (not 1–5). 5 exercises → **max 50** →
  badge **daraja I / II / III** (`48–50 / 38–46 / 30–36`; `<30` = no badge).
- The **set of 5 exercises is chosen per `(age category × gender)`** from a ~9-exercise
  pool; the exercise itself can differ by gender (boys pull-ups ↔ girls bench push-ups)
  and by age (30m → 100m, +400m for older).
- Standard is **universal by age × gender** — no OTM/OPSTTM block, no sport type in
  scoring. `Organization.type` stays only for classification / filtering / reports.
- Norms differ **per single year** (7–17), plus one `18–29` bucket → age is a numeric
  range on the norm, not a fixed category FK.

---

## 1. Design Decisions (agreed)

| Question | Decision | Reason |
|---|---|---|
| Norm keying | `Norm(exercise, age_min, age_max, gender)` + `NormBand` | Real tables are per single year × gender; no sport/block |
| Points scale | `NormBand.points` ∈ {10, 8, 6, …} (data) | Client tables use 10/8/6, not 1–5 |
| Which 5 exercises | Explicit `TestBattery(age_category, gender)` + `BatteryItem` | Selection varies by group; drives the entry form |
| Level / daraja | `DarajaThreshold(level, total_min, total_max)` (data) | I/II/III from the total; not hardcoded |
| Is Evaluation stored | **Stored** (snapshot) | Ranking is read-heavy; reproducible if norms change |
| Age category (TOIFA) | Catalog for grouping/ranking; **norm lookup uses numeric age** | Two granularities: battery per TOIFA, norm per year |
| Age at evaluation | **Computed** from birth + session date | Age changes over time |
| Block (OTM/OPSTTM) | `Organization.type` = classification only | Physical standard is block-independent |
| Height / weight / BMI | Nullable on `TestSession`; **BMI deferred** (`DEFERRED.md`) | Belongs to morpho, no criteria yet |
| Athlete transfers | Current values on `Athlete` + `AthleteAssignmentHistory`; ranking dims **snapshotted** on `TestSession`/`Evaluation` | Historical/period rankings use org/region/sport as at session time |
| Periods (quarter/half/year) | **Derived from `TestSession.date`** (calendar) | No period entity |
| i18n | **UI strings only** (uz/ru/kk/en); reference content stays Uzbek | Avoids multilingual content modeling |
| Ranking index | Composite index on Evaluation ranking dims | Fast `RANK()` |

---

## 2. ERD — relationship diagram

```
  ┌─── IDENTITY ────────────────────────────────────────────────┐
  │  Region ──o<── District                                      │
  │    │ │         │                                             │
  │    │ └──o<── User (role: super/region/coach/operator/ministry)│
  │    │             │ region_id, organization_id (scope)        │
  └────┼─────────────┼──────────────────────────────────────────┘
       │             │
  ┌─── CATALOG ──────┼──────────────────────────────────────────┐
  │  Organization (type: OTM|OPSTTM — classification) >o── Region │
  │  SportType     AgeCategory (TOIFA 1–6)                        │
  │  Exercise (unit, value_type, direction)                      │
  │      │                                                       │
  │      ├──||──o<── Norm (exercise×age_range×gender) ──o<── NormBand
  │      │                                        (raw range → points)
  │      └──o<── BatteryItem >o── TestBattery (age_category×gender)
  │  DarajaThreshold (level → total range)                       │
  └──────────────────┼───────────────────────────────────────────┘
                     │ (scoring engine reads norms + battery + thresholds)
  ┌─── ATHLETE ──────┼───────────────────────────────────────────┐
  │  Athlete >o── Region, District, Organization, SportType,      │
  │            >o── User(coach)                                   │
  └──────┬────────────────────────────────────────────────────────┘
         │ 1
  ┌─── MEASUREMENT ──┼──────────────────────────────────────────┐
  │  TestSession (date, entered_by, source, snapshot dims)       │
  │      │ 1                                                     │
  │      └──o<── Measurement >o── Exercise  (raw_value)          │
  │  ImportBatch ──o<── ImportRow                                │
  └──────┼───────────────────────────────────────────────────────┘
         │ 1 : 1
  ┌─── EVALUATION (snapshot) ───────────────────────────────────┐
  │  Evaluation (physical_total 0–50, daraja, color)             │
  │      │ 1                                                     │
  │      └──o<── IndicatorScore >o── Exercise  (raw, points)     │
  └──────┬───────────────────────────────────────────────────────┘
         │ 1
  ┌─── OUTPUT ───────┼──────────────────────────────────────────┐
  │  Recommendation >o── RecommendationRule                      │
  │  Report (type, format, params, status, file)                 │
  │  (Ranking = RANK() over Evaluation + Redis cache, not a table)│
  └──────────────────────────────────────────────────────────────┘

  Cross-cutting:  AuditLog >o── User
```
`||──o<` = one-to-many · `>o──` = many-to-one (FK)

---

## 3. Entities and Fields

### CATALOG (reference — admin-managed)

**Region** — `id · name · code` (14: Qoraqalpogʻiston + Toshkent city + 12 regions)
**District** — `id · region_id → · name`
**Organization** — `id · name · type(OTM|OPSTTM) · region_id → · district_id →`
> `type` is a **classification / filter** attribute (reports, "which athletes are
> OPSTTM"). It does **not** affect physical scoring.

**SportType** — `id · name · code` (30+) — used on the athlete card, filters, ranking.
**AgeCategory (TOIFA)** ★ — `id · ordinal(1–6) · name · age_min · age_max`
> Six categories: `1: 7–8 · 2: 9–10 · 3: 11–12 · 4/5: 13–17 (split TBC) · 6: 18–29`.
> Used to pick the `TestBattery` and to group rankings/reports. **Open item:** confirm
> the 13–17 split into the 4th/5th toifa with the client.

**Exercise** ★ (the exercise pool; replaces the old `TestType`) —
`id · name · unit · value_type(seconds|minsec|count|cm_signed) · direction(higher|lower_is_better) · order · is_active`
> Pool (Uzbek reference names): 30 m yugurish · 100 m yugurish · 400 m yugurish ·
> turgan joydan uzunlikka sakrash · gimnastika oʻrindigʻida oldinga egilish (signed) ·
> argʻimchoqda sakrash · yerga tayanib qoʻl bukish · skameykaga tayanib qoʻl bukish ·
> turnikda tortilish · (agility "9 fishka", footnoted). `value_type` tells the SPA how to
> render the input and how to store the number (mm:ss → seconds).

**TestBattery** ★ — `id · age_category_id → · gender · is_active`  (one per group)
**BatteryItem** ★ — `id · battery_id → · exercise_id → · order`  (exactly 5 per battery)
> Defines **which ordered exercises** an athlete of a given `(age_category, gender)`
> performs. The data-entry form is built directly from this. Example: `(4th toifa,
> male)` → [100 m, 400 m, uzunlikka sakrash, oldinga egilish, turnikda tortilish];
> `(4th toifa, female)` → the same but #5 = skameykaga tayanib qoʻl bukish.

**Norm** ★ (header) — `id · exercise_id → · age_min · age_max · gender · valid_from · is_active`
> **No sport_type, no block.** For 7–17: `age_min = age_max = year`. For adults:
> `age_min = 18, age_max = 29`. Versioned by `valid_from`.
**NormBand** ★ (lines) — `id · norm_id → · points(10|8|6…) · lower_bound · upper_bound`
> `[lower_bound, upper_bound)` — lower inclusive, upper exclusive. `direction` is baked
> into the ordering of bounds (as in the tables). Bounds are numeric: time in **seconds**
> (mm:ss converted), counts as integers, flexibility as **signed cm**.

**DarajaThreshold** ★ — `id · level(I|II|III) · total_min · total_max`
> Total (0–50) → badge. Currently `I: 48–50 · II: 38–46 · III: 30–36 · <30: none`.
> Data-driven so the client can adjust without a code change.

### IDENTITY

**User** — `id · username · password(hash) · full_name · phone/email · role(super_admin|region_admin|coach|lab_operator|ministry) · region_id →(scope) · organization_id →(scope) · is_active`
> Region-scoping: `region_admin` → own `region_id`; `coach` → own athletes;
> `lab_operator` → own `organization_id`.

### ATHLETE

**Athlete** — `id · last_name · first_name · middle_name · birth_year · gender · region_id → · district_id → · organization_id → · sport_type_id → · razryad · coach_id → User · training_experience · main_competitions · is_active · created_at`
> `age_category` (TOIFA) is **computed** from age at session date, not stored on the
> athlete. `weight_category` is **deferred** (morpho). **Open item:** `birth_year` vs
> `birth_date` — norms are per single year (7–17), so a full `birth_date` gives correct
> age at the session date; confirm precision with the client.

**AthleteAssignmentHistory** — `id · athlete_id → · organization_id → · region_id → · district_id → · sport_type_id → · coach_id → User · valid_from · valid_to(null = current) · changed_by → User · reason`
> Effective-dated transfer timeline. On any org/region/district/sport/coach change,
> close the current record and open a new one.

### MEASUREMENT

**TestSession** — `id · athlete_id → · date · entered_by → User · source(manual|excel) · import_batch_id → · status(draft|finalized)` + **snapshot dims** `age_category · gender · region_id · organization_id · sport_type_id` + optional `height_cm · weight_kg`(nullable, future morpho)
> Snapshot dims freeze where the athlete was at session time so historical/period
> rankings are stable after a transfer. Period (quarter/half/year) derives from `date`.
**Measurement** — `id · session_id → · exercise_id → · raw_value`
> One row per exercise in the athlete's battery (5 for physical).
**ImportBatch** — `id · uploaded_by → · file · status(uploaded|validating|validated|committed|failed) · row_count · error_count · created_at`
**ImportRow** — `id · batch_id → · row_number · raw_data(json) · status · errors(json)`

### EVALUATION (computed snapshot)

**Evaluation** — `id · session_id →(1:1) · athlete_id →(denorm) · age_category(snapshot) · gender(denorm) · region_id(denorm) · sport_type_id(denorm) · session_date(denorm) · physical_total(0–50) · daraja(I|II|III|none) · color(green|yellow|red) · ranking_score(=physical_total) · computed_at`
**IndicatorScore** — `id · evaluation_id → · exercise_id → · raw_value · points`
> `ranking_score = physical_total`. Ranking dims (`region`, `sport_type`, `age_category`,
> `gender`, `session_date`) are denormalized onto Evaluation so `RANK()` runs on one
> indexed table without joining a possibly-transferred athlete. **Composite index** on
> `(region_id, sport_type_id, age_category, gender, ranking_score)`.

### OUTPUT

**RecommendationRule** — `id · exercise_id →/category · condition(points/total threshold) · template_text · is_active`
> e.g. "turnikda tortilish points ≤ 6 → strength low" or "physical_total < 30 → below
> badge norm". Admin-managed, not in code.
**Recommendation** — `id · evaluation_id → · rule_id → · text · created_at`
**Report** — `id · type(athlete|region|sport|republic) · format(pdf|word|excel) · params(json) · requested_by → · status(pending|processing|done|failed) · file · created_at · completed_at`

### CROSS-CUTTING

**AuditLog** — `id · user_id → · action · entity_type · entity_id · changes(json) · created_at · ip`

---

## 4. Evaluation Logic (physical readiness)

Each exercise's raw result → **points (10/8/6)** via `Norm`/`NormBand`. Sum → total →
daraja. Full algorithm and worked examples: `SCORING.md`.

```
per exercise:  raw_value ──(NormBand of the athlete's age×gender norm)──► points (10/8/6)
               clamp: better than best band → 10 ; worse than worst band → 0

physical_total = Σ points over the 5 battery exercises        # max 50
daraja         = DarajaThreshold(physical_total)              # I / II / III / none
ranking_score  = physical_total
```

| total | daraja | color |
|---|---|---|
| 48–50 | I daraja | 🟢 green |
| 38–46 | II daraja | 🟡 yellow |
| 30–36 | III daraja | 🔴 red |
| < 30 | none (nishonsiz) | 🔴 red |

> The daraja bounds live in `DarajaThreshold` (data), not in code.

---

## 5. Ranking and Cache

Ranking is NOT a table — computed over `Evaluation.ranking_score`:

```sql
RANK() OVER (PARTITION BY <region, sport_type, age_category, gender> ORDER BY ranking_score DESC)
```

> **Block dropped** from the partition (physical is block-independent). `sport_type`
> stays a partition/filter dimension (from the athlete) so "top athletes in a sport" is
> still answerable, even though norms are sport-independent.

Cached in Redis (filter combo = key; TTL + invalidation on new Evaluation), or recomputed
by Celery Beat. **Period filter:** ranking/comparison/history/reports accept an optional
`period_type(quarter|half|year)` + value, applied as a `session_date` range. No period
entity. With no period, the latest Evaluation per athlete is used. Ties → same `RANK()`;
display tiebreak: latest evaluation date, then full name.

---

## 6. Diagnostics — psychological questionnaires + functional indicators (B14)

Source: the client's Aug–Sep 2026 materials in `resources/` — five psychological
methodologies (OPS, V.E. Milman, Spielberger–Khanin, R. Frester, Raven) and two
functional reference sheets (pulse oximetry, automatic tonometry). Scoring rules:
`SCORING.md` §12.

### 6.1 Decisions (2026-10-07)

| Question | Decision | Reason |
|---|---|---|
| Where it lives | New app **`apps/diagnostics`**; `Evaluation`/rating/comparison stay physical-only | Questionnaires and categorical vital-sign levels don't fit `Measurement`/`NormBand`/`physical_total`; mixing would make a psych session the athlete's "latest" evaluation in the ranking |
| Who enters answers | **Staff** (coach / lab_operator / admins) transcribe the athlete's paper form | No athlete login; same roles and scoping as measurements |
| Answer keys, weights, offsets, bands | **DATA** (`ScaleKey`, `ScaleBand`, `IndicatorBand`) | Project invariant: thresholds are data; client gaps get filled by data, not code |
| Incomplete client criteria | Build with what exists; a scale with no band shows the score with "daraja belgilanmagan"; Raven is not seeded | Unblocks the rest; answers from the client become data updates |
| Overall psych/functional verdict, ranking | **None** (v1) | No client rule exists (DEFERRED §4) |
| Old DEF-2/4/6/7 design | **Superseded** for psych/functional | Real criteria are per-methodology raw scores / categorical levels, not "% → overall %" |

### 6.2 ERD

```
  ┌─── DIAGNOSTICS CATALOG (data, super_admin + seed_diagnostics) ─────────┐
  │  Instrument ──o<── Item ──o<── Option (code a/b/v…, value?, group?)    │
  │      │                │                                                │
  │      └──o<── Scale ──o<── ScaleKey >o── Item, Option?   (weight)       │
  │                 └──o<── ScaleBand (score range → label, color)         │
  │  Indicator ──o<── IndicatorBand (age×gender×value range → label, color)│
  └────────────────────────────────────────────────────────────────────────┘
  ┌─── DIAGNOSTICS RESULTS (snapshot) ─────────────────────────────────────┐
  │  Assessment >o── Athlete, Instrument   (date, status, snapshot dims)   │
  │      ├──o<── Response >o── Item, Option?   (value?)                    │
  │      └──o<── ScaleResult >o── Scale   (score, label, color)            │
  │  FunctionalCheck >o── Athlete   (date, status, snapshot dims)          │
  │      └──o<── FunctionalReading >o── Indicator   (value, label, color)  │
  └────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Entities

**Instrument** — `id · code(unique) · name · description · instructions · time_limit_min? · is_active`
> One psychological methodology (`ops`, `milman`, `khanin`, `frester`; `raven` later).
**Item** — `id · instrument_id → · number · text · response_type(single|multi|rating) · rating_min? · rating_max?`
> Unique `(instrument, number)`. `single` = one option (Ha/Yo'q, a/b/v); `multi` = several
> options (Milman #17); `rating` = an integer in `[rating_min, rating_max]` (Khanin 1–4,
> Frester 1–9).
**Option** — `id · item_id → · code · text · group? · order`
> Unique `(item, code)`. `code` is the printed letter (`a, b, v, g, d, e, j, z, i` — the
> Cyrillic order transliterated). `group` is a free label for categorical items (Milman
> #17: `neytral | stenik | astenik`). Rating items have no options.
**Scale** — `id · instrument_id → · code · name · offset(decimal, default 0) · direction(higher_better|lower_better) · order`
> A scored dimension: a component, subscale or total (e.g. Khanin `xh`, `xsh`; OPS `uv`,
> `sp`, `zn`, `others`, `total`). `direction` drives display only (which end is "good").
**ScaleKey** — `id · scale_id → · item_id → · option_id →? · weight(decimal)`
> The answer key as data. Choice item: `(item, option) → weight` (no row = 0). Rating
> item: `option = null` and the answer value is multiplied by `weight` (±1). Unique
> `(scale, item, option)`. One item may feed several scales (Milman 23–25).
**ScaleBand** — `id · scale_id → · lower(decimal) · upper(decimal) · label · color`
> `[lower, upper)`, same convention as `NormBand`. Non-overlapping per scale (validated).
> No band covering the score → result label empty = "daraja belgilanmagan".

**Indicator** — `id · code(unique) · name · unit · order · is_active`
> Functional vital sign: `spo2` (%), `pulse_rest` (urish/min), `bp_sys`, `bp_dia` (mmHg).
> Blood pressure is two indicators so each value is one number.
**IndicatorBand** — `id · indicator_id → · age_min · age_max · gender? · lower · upper · label · color · valid_from`
> `[lower, upper)`; `gender = null` = both. Bands need **not** be monotonic (both a low and
> a high pulse are warnings). Versioned by `valid_from`, pinned to the check date (as
> `Norm`). Non-overlapping per `(indicator, age range, gender, valid_from)` (validated).

**Assessment** — `id · athlete_id → · instrument_id → · date · entered_by → User · status(draft|finalized) · finalized_at?` + **snapshot dims** `age_category · gender · region_id · organization_id · sport_type_id`
> One administration of one instrument. Snapshot dims frozen at creation, exactly as on
> `TestSession`, so history survives transfers.
**Response** — `id · assessment_id → · item_id → · option_id →? · value?`
> `single`: one row with `option`; `multi`: one row per chosen option; `rating`: one row
> with `value`. Unique `(assessment, item, option)`.
**ScaleResult** — `id · assessment_id → · scale_id → · score(decimal) · label · color`
> Written on finalize; `label`/`color` copied from the band (snapshot — a later band edit
> doesn't rewrite history; super_admin can recompute explicitly).

**FunctionalCheck** — `id · athlete_id → · date · entered_by → User · status(draft|finalized) · finalized_at?` + **snapshot dims** (as `Assessment`)
**FunctionalReading** — `id · check_id → · indicator_id → · value(decimal) · label · color`
> Unique `(check, indicator)`. Not every indicator is required per check (a check may
> record only SpO₂ + pulse). `label`/`color` resolved on finalize from the band for the
> athlete's age at `date` (+ gender); no band → empty label.

### 6.4 Invariants
- Keys, offsets and bands are **data**; the engine has one formula (`SCORING.md` §12).
- Finalize is the only place results are computed; finalized rows are read-only for
  non-super_admin.
- Scoping is the measurements scoping (`ScopedQuerysetMixin` via the athlete), server-side.
- Nothing in `diagnostics` writes to `Evaluation`, rating, comparison, or recommendations.
