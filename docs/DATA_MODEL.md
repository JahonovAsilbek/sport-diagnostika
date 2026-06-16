# SPORT-DIAGNOSTIKA.UZ — Data Model (ERD)

Source: `SPORT.docx` (technical spec (TTZ)). Architecture: `ARCHITECTURE.md`.

> Status: **model agreed**. Migration/implementation not started.

---

## 1. Design Decisions (agreed)

| Question | Decision | Reason |
|---|---|---|
| Evaluation norms | `Norm` (header) + `NormBand` (bounds) | Data-driven, admin-editable, sport-specific override |
| Is Evaluation stored | **Stored** (snapshot) | Ranking is read-heavy; result is reproducible even if norms change |
| Coach | `User(role=coach)`, `Athlete.coach → User` | Single source (login + card field is one person) |
| Age category | **Computed** (`birth_year` + test date) | Age changes over time, storing it causes drift |
| Block (OTM/OPSTTM) | Derived from `Organization.type` | Single source |
| Height / weight / BMI | Snapshot in `TestSession`, BMI computed | Changes over time, tied to the session |
| OPSTTM ranking | `ranking_score = overall percentage` (same as OTM) | Both blocks are compared in one ranking table |
| OPSTTM category weighting | **Equal weight** (average of the 4 category percentages) | So a category with many tests (morpho=7) does not dominate the overall |
| BMI role | In OTM **informational** (not scored); in OPSTTM scored within **morpho** | TTZ: OTM = 10 tests = 50 points; "body mass index" counted in morpho |
| Periods (quarter/half/year) | **Derived from `TestSession.date`** (calendar), not an entity | Simplest; ranking/reports/history filter by `period_type` + value |
| Athlete transfers | Current values on `Athlete` + an **`AthleteAssignmentHistory`** timeline; ranking dimensions **snapshotted** on `TestSession`/`Evaluation` | History matters; historical/period rankings must use region/org/sport as they were at session time |
| i18n | **UI strings only** (4 langs: uz/ru/kk/en, vue-i18n); reference content stays Uzbek | Avoids heavy multilingual content modeling |
| Input validation bounds | `TestType.valid_min` / `valid_max` | Reject absurd raw values at entry |
| Ranking index | Composite index on the Evaluation ranking dimensions | Fast `RANK()` over (region, sport, age, gender, block) |

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
  │  Organization (type: OTM|OPSTTM) >o── Region, District       │
  │  SportType   AgeCategory   WeightCategory >o─ SportType      │
  │  TestType (block, category, unit, direction)                 │
  │      │                                                       │
  │      └──||──o<── Norm ──o<── NormBand                         │
  │                   (test×age×gender×sport?×block → bands)     │
  └──────────────────┼───────────────────────────────────────────┘
                     │ (scoring engine reads the norms)
  ┌─── ATHLETE ──────┼───────────────────────────────────────────┐
  │  Athlete >o── Region, District, Organization, SportType,      │
  │            >o── WeightCategory, >o── User(coach)              │
  └──────┬────────────────────────────────────────────────────────┘
         │ 1
  ┌─── MEASUREMENT ──┼──────────────────────────────────────────┐
  │  TestSession (date, height_cm, weight_kg, entered_by, source)│
  │      │ 1                                                     │
  │      └──o<── Measurement >o── TestType  (raw_value)          │
  │  ImportBatch ──o<── ImportRow                                │
  └──────┼───────────────────────────────────────────────────────┘
         │ 1 : 1
  ┌─── EVALUATION (snapshot) ───────────────────────────────────┐
  │  Evaluation (bmi, category %, total %, level, color)         │
  │      │ 1                                                     │
  │      └──o<── IndicatorScore >o── TestType  (raw, score 1-5)  │
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
**SportType** — `id · name · code` (30+)
**AgeCategory** — `id · name · min_age · max_age(null = 22+)` (12–13, 14–15, 16–17, 18–21, 22+)
**WeightCategory** — `id · sport_type_id → · gender · name · min_kg · max_kg`
**TestType** ★ — `id · name · block(OTM|OPSTTM|both) · category(physical|functional|morpho|psych) · unit · direction(higher|lower_is_better) · valid_min · valid_max · order · is_active`
> `valid_min`/`valid_max` bound acceptable raw input (reject absurd/negative values at entry).

**Norm** ★ (header) — `id · test_type_id → · age_category_id → · gender · sport_type_id →(null = all sports) · block · valid_from`
**NormBand** ★ (lines) — `id · norm_id → · score(1-5) · lower_bound · upper_bound`
> Lookup priority: `sport+age+gender` → if not found → `age+gender` (generic).
> `direction`, together with the band bounds, converts the raw value into a 1–5 score.

### IDENTITY

**User** — `id · username · password(hash) · full_name · phone/email · role(super_admin|region_admin|coach|lab_operator|ministry) · region_id →(scope) · organization_id →(scope) · is_active`
> Region-scoping: `region_admin` → only their own `region_id`; `coach` → only their own athletes; `lab_operator` → their own organization.

### ATHLETE

**Athlete** — `id · last_name · first_name · middle_name · birth_year · gender · region_id → · district_id → · organization_id →(→ block) · sport_type_id → · razryad · coach_id → User · weight_category_id → · training_experience · main_competitions · is_active · created_at`
> `age_category` is not stored — it is computed from `birth_year` + test date.
> The athlete row holds **current** assignment; changes over time are tracked in
> `AthleteAssignmentHistory`.

**AthleteAssignmentHistory** — `id · athlete_id → · organization_id → · region_id → · district_id → · sport_type_id → · coach_id → User · valid_from · valid_to(null = current) · changed_by → User · reason`
> Effective-dated transfer timeline. On any org/region/district/sport/coach change,
> close the current record (`valid_to`) and open a new one. Enables "where was this
> athlete in Q1 2025" and audit of transfers.

### MEASUREMENT

**TestSession** — `id · athlete_id → · date · height_cm · weight_kg · block(snapshot) · region_id(snapshot) · organization_id(snapshot) · sport_type_id(snapshot) · entered_by → User · source(manual|excel) · import_batch_id → · status(draft|finalized)`
> `block`, `region`, `organization`, `sport_type` are **snapshotted** from the athlete
> at session time so historical/period rankings reflect where the athlete was then
> (not after a later transfer). The period (quarter/half/year) is **derived from `date`**.
**Measurement** — `id · session_id → · test_type_id → · raw_value`
**ImportBatch** — `id · uploaded_by → · file · status(uploaded|validating|validated|committed|failed) · row_count · error_count · created_at`
**ImportRow** — `id · batch_id → · row_number · raw_data(json) · status · errors(json)`

### EVALUATION (computed snapshot)

**Evaluation** — `id · session_id →(1:1) · athlete_id →(denorm) · block · region_id(denorm) · sport_type_id(denorm) · age_category(snapshot) · gender(denorm) · session_date(denorm) · bmi_value · bmi_category · physical_pct · functional_pct · morpho_pct · psych_pct · total_points(OTM) · percentage · level · color(green|yellow|red) · ranking_score · computed_at`
**IndicatorScore** — `id · evaluation_id → · test_type_id → · category · raw_value · score(1-5)`
> `ranking_score = percentage` (both blocks). In OPSTTM, `percentage` = average of the 4 category percentages.
> Ranking dimensions (`region`, `sport_type`, `age_category`, `gender`, `block`,
> `session_date`) are denormalized/snapshotted onto Evaluation so `RANK()` runs on a
> single indexed table without joining a possibly-transferred athlete. **Composite
> index** on `(region_id, sport_type_id, age_category, gender, block, ranking_score)`.
> Period filters derive from `session_date`.

### OUTPUT

**RecommendationRule** — `id · test_type_id →/category · condition(level/threshold) · template_text · is_active`
**Recommendation** — `id · evaluation_id → · rule_id → · text · category · created_at`
**Report** — `id · type(athlete|region|sport|opsttm|otm|republic) · format(pdf|word|excel) · params(json) · requested_by → · status(pending|processing|done|failed) · file · created_at · completed_at`

### CROSS-CUTTING

**AuditLog** — `id · user_id → · action · entity_type · entity_id · changes(json) · created_at · ip`

---

## 4. Evaluation Logic (final)

Each test's raw result is converted into a **1–5 score** via `Norm`/`NormBand`
(`direction` accounts for the lower/higher direction).

### OTM block — 5 levels

```
Physical:   5 tests × 1-5 = max 25
Functional: 5 tests × 1-5 = max 25
─────────────────────────────────────
Total = 50 points → percentage = points / 50 × 100
BMI = separate informational indicator (NOT scored)

90–100% → very high   75–89% → high   60–74% → medium
40–59%  → low          0–39%  → very low
```

Test list (TTZ sample):
- Physical: 30m sprint · pull-ups · 1000m run · agility · flexibility/coordination
- Functional: resting heart rate · post-load heart rate · recovery time · vital lung capacity · aerobic capacity

### OPSTTM block — 3 levels (categories equally weighted)

```
Physical:      5 × 1-5 = max 25 → physical_pct
Functional:    5 × 1-5 = max 25 → functional_pct
Morpho (+BMI): 7 × 1-5 = max 35 → morpho_pct
Psychological: 6 × 1-5 = max 30 → psych_pct
──────────────────────────────────────────────
percentage = (physical_pct + functional_pct + morpho_pct + psych_pct) / 4
ranking_score = percentage

high · normal · low   (bounds are set in the Norm table)
```

Indicators (TTZ):
- Physical: 30m sprint · pull-ups · 1000m run · agility · coordination
- Functional: heart rate · recovery time · vital lung capacity · cardiovascular · aerobic capacity
- Morphofunctional: height · weight · BMI · chest circumference · grip strength · body composition · somatotype
- Psychological: pre-start anxiety · stress tolerance · reaction speed · attention stability · self-confidence · emotional state

### Color indicator
🟢 green = high level · 🟡 yellow = medium/normal · 🔴 red = low.
The level → color mapping is stored in `Evaluation.color` depending on the block.

---

## 5. Ranking and Cache

Ranking is NOT a separate table — it is computed over `Evaluation.ranking_score`:

```sql
RANK() OVER (PARTITION BY <region, sport, age_category, gender, block> ORDER BY ranking_score DESC)
```

The result is cached in Redis (TTL + invalidation when data changes).
When a new `Evaluation` is computed, the relevant slice's cache is invalidated, or
Celery Beat recomputes it on a schedule. The "region ranking" (count of high-level
athletes) is an aggregate query; for the ministry report a periodic snapshot
may be stored.

**Period filter:** ranking, comparison, history and reports accept an optional
`period_type` (quarter|half|year) + value, applied as a `session_date` range derived
from the calendar (Q1 = Jan–Mar, H1 = Jan–Jun, etc.). No period entity. When no
period is given, the latest Evaluation per athlete is used.
