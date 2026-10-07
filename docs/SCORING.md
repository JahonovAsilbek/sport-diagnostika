# SPORT-DIAGNOSTIKA.UZ — Scoring specification (physical readiness)

The complete logic of the scoring engine for **physical readiness** — the one category
with real client criteria. Models: `DATA_MODEL.md`. Parked categories: `DEFERRED.md`.
This document is the source of the `apps/scoring/domain/` implementation.

> Status: **methodology agreed** from the client's `Jismoniy tayyorgarlik mezonlari`
> tables. The exact band numbers are **data** (seeded from those tables), not code.

---

## 1. Principle

A raw exercise result (`Measurement.raw_value`) → **points (10 / 8 / 6)** via the
`Norm` + `NormBand` table. No bound lives in code — everything is data. Sum the 5
exercises → total (max 50) → **daraja (I / II / III)** via `DarajaThreshold`.

```
raw_value ──(NormBand)──► points 10/8/6 ──(Σ over 5 exercises)──► total 0–50
                                                                     │
                                                    daraja + color ◄─┘
```

There is **one scheme** (block-independent). The two-strategy OTM/OPSTTM model is parked
(`DEFERRED.md`).

---

## 2. Exercise pool & batteries

The pool has ~9 exercises; each `(age_category × gender)` **battery** picks an ordered 5.
`Exercise.direction`: `lower_is_better` (time — less = better) or `higher_is_better`.

| Exercise (uz) | unit / value_type | direction |
|---|---|---|
| 30 m ga yuqori startdan yugurish | s (`seconds`) | lower |
| 100 m ga pastki startdan yugurish | s (`seconds`) | lower |
| 400 m ga pastki startdan yugurish | daq:s (`minsec`→s) | lower |
| Turgan joydan uzunlikka sakrash | sm (`count`/cm) | higher |
| Gimnastika oʻrindigʻida oldinga egilish | sm signed (`cm_signed`) | higher |
| Argʻimchoqda sakrash (1 daq) | marta (`count`) | higher |
| Yerga tayanib qoʻllarni bukish (30 s) | marta (`count`) | higher |
| Skameykaga tayanib qoʻllarni bukish (30 s) | marta (`count`) | higher |
| Turnikda tortilish | marta (`count`) | higher |

> **The battery differs by group** (this is the crux):
> - **young (toifa 1–3, 7–12):** 30 m · uzunlikka sakrash · oldinga egilish ·
>   push-ups (**boys**: yerga / **girls**: skameyka) · argʻimchoq.
> - **older (toifa 4–5, 13–17):** 100 m · 400 m · uzunlikka sakrash · oldinga egilish ·
>   (**boys**: turnikda tortilish / **girls**: skameyka).
> - **adults (toifa 6, 18–29):** 100 m · argʻimchoq · uzunlikka sakrash · oldinga egilish
>   · (**men**: turnikda tortilish / **women**: skameyka).
>
> So exercise #4/#5 differ **by gender**, and the running distances differ **by age**.
> The exact 5 per group are stored in `TestBattery`/`BatteryItem`, seeded from the tables.

---

## 3. Raw value → points (10/8/6) algorithm

1. Find the athlete's `age` at the session date; from it derive the `AgeCategory` (TOIFA)
   and thus the `TestBattery` (which 5 exercises).
2. For each battery exercise, find the matching `Norm`:
   `exercise + gender + (age between age_min and age_max)` (§4).
3. The `NormBand` whose `[lower_bound, upper_bound)` contains `raw_value` gives the
   `points` (10, 8 or 6).
4. **`direction` is baked into the bounds**, not reasoned about by the engine: for a
   `lower_is_better` exercise the best (10-point) band holds the smallest numbers, exactly
   as printed in the tables. The engine only checks which range the value falls into.
5. **Clamp (out of range):** a value better than the best band → `points = 10`; worse
   than the worst band → `points = 0` (below norm — never an error).
6. **If no norm is found:** the indicator is `unscored`, finalize is blocked, the admin
   is signalled (audit). (§7)

**Sample (real — 14-yosh oʻgʻil bola, 100 m):**

| points | range (s) |
|---|---|
| 10 | 14.0 – 14.2 |
| 8 | 14.3 – 14.5 |
| 6 | 14.6 – 14.8 |
| — | < 14.0 → clamp 10 ; > 14.8 → 0 |

> mm:ss values (400 m e.g. `1:20`) are normalized to seconds before comparison.
> Signed flexibility (`+9`, and negatives) is stored/compared as signed cm.

---

## 4. Norm lookup

Physical norms are **sport- and block-independent**. Lookup is exact:

```
exercise + gender + age ∈ [age_min, age_max]   (+ latest valid_from ≤ session_date)
```

- 7–17: a norm per single year (`age_min = age_max = year`).
- 18–29: one norm (`age_min = 18, age_max = 29`).
- Norms are **versioned** (`valid_from`). Because `Evaluation` is a snapshot, old
  evaluations keep the norm that applied then; after a norm change the admin recomputes
  via `POST /evaluations/recompute/`.

---

## 5. Aggregation → total → daraja

```
physical_total = Σ points over the 5 battery exercises        # each 10/8/6/0 → max 50
ranking_score  = physical_total
daraja         = DarajaThreshold(physical_total)
```

| total | daraja | color |
|---|---|---|
| 48 – 50 | I daraja | 🟢 green |
| 38 – 46 | II daraja | 🟡 yellow |
| 30 – 36 | III daraja | 🔴 red |
| < 30 | none (nishonsiz) | 🔴 red |

- `≥ 48` also flags "next year recommended for the special requirement directly"
  (from the tables); `= 50` = "gʻoliblik" (victory). These are display flags derived from
  the total, optional to surface.
- Daraja bounds live in `DarajaThreshold` (data). **Open item:** confirm they are
  constant across all tables (they appear fixed at 48/38/30).

---

## 6. Other categories

Psychological questionnaires and functional indicators are scored by the separate
`diagnostics` module (§12) and **never** feed `physical_total`, daraja or the ranking.
BMI and morphofunctional scoring still have **no criteria** — see `DEFERRED.md`.
`TestSession.height_cm` / `weight_kg` are nullable placeholders for that future work.

---

## 7. Edge cases

| Case | Behavior |
|---|---|
| Incomplete session (not all 5 battery exercises entered) | `finalize` rejected → `400`, missing exercises returned |
| No norm for exercise × age × gender | indicator `unscored`, session not finalized, admin signalled |
| Value better than best band | clamp → 10 (§3.5) |
| Value worse than worst band | 0 points (below norm) → likely `daraja = none` |
| Negative/absurd raw value | input validation (exercise unit bounds) → `422` (flexibility negatives are valid) |
| mm:ss time | normalized to seconds before band comparison |
| Equal `ranking_score` | same `RANK()`; display tiebreak: latest evaluation date, then full name |
| Battery undefined for a group | cannot open the physical form; admin must define the `TestBattery` first |

---

## 8. Recommendation generation (dependency)

During `finalize`, once points are computed, `RecommendationRule`s are checked: if a
`condition` holds (e.g. "turnikda tortilish points ≤ 6" or "physical_total < 30"), a
`Recommendation` is written from `template_text`. Rules are admin-managed, not in code.
Samples:

- turnikda tortilish ≤ 6 → "Kuch koʻrsatkichi past. Kuch mashqlari hajmini oshirish tavsiya etiladi."
- physical_total < 30 → "Koʻkrak nishoni meʼyoriga yetmadi. Umumiy jismoniy tayyorgarlikni oshirish kerak."

---

## 9. Worked examples (real numbers)

**14-yosh oʻgʻil bola** (battery: 100 m · 400 m · uzunlikka sakrash · oldinga egilish · turnikda tortilish):
- 100 m `14.4 s` → 8 · 400 m `1:22` → 8 · uzunlikka `178 sm` → 10 · egilish `+9` → 8 ·
  turnik `13 marta` → 8
- total = 8+8+10+8+8 = **42** → **II daraja** 🟡 · ranking_score = 42

**14-yosh qiz bola** — same battery **except #5** = skameykaga tayanib qoʻl bukish (not
turnik). Illustrates that the exercise set itself is gender-specific.

**7-yosh bola** — battery uses **30 m** sprint and **argʻimchoq**, not 100 m/400 m —
illustrating age-driven exercise selection.

---

## 10. Loading and storing norms

- **Admin UI** (Django admin + DRF) — manual entry/editing of `Exercise`, `TestBattery`,
  `Norm` + `NormBand`, `DarajaThreshold`.
- **Seed command** — `seed_physical` loads the ~24 tables
  (11 years × 2 genders + 18–29 × 2 genders) into `Norm`/`NormBand` + the batteries.
- **Versioning** — `valid_from`; old Evaluation snapshots are preserved.

---

## 11. Open items to confirm with the client
1. Exact **TOIFA 4/5 boundary** within ages 13–17.
2. **Below-worst-band** result (0 / "did not meet") and **above-best clamp** (→10).
3. **birth_date vs birth_year** precision (norms are per single year).
4. Whether **"Maxsus talab boʻyicha"** implies a second (general) norm tier.
5. Confirm `DarajaThreshold` is constant across all tables (48/38/30).

---

## 12. Diagnostics scoring — questionnaires + functional indicators (B14)

Models: `DATA_MODEL.md` §6. Source: `resources/` (client, Aug–Sep 2026). Code:
`apps/diagnostics/domain/` (pure functions, same style as `scoring/domain/`). Everything
below the formulas is **seed data** (`seed_diagnostics`), editable in admin.

### 12.1 One questionnaire formula

```
score(scale) = scale.offset + Σ over the scale's ScaleKeys of contribution(key)

contribution(key) =
    choice item (single|multi): key.weight  if key.option was chosen, else 0
    rating item:                key.weight × answered value
level(scale)  = ScaleBand where lower ≤ score < upper   →  label + color
                none → "daraja belgilanmagan" (score still shown)
```

That one formula covers every delivered methodology:

| Methodology | Items / answers | Scales (ScaleKey) | Offset | Bands (seed) |
|---|---|---|---|---|
| **Spielberger–Khanin** | 40 rating 1–4 (XH 1–20, XSh 21–40) | `xh`: +1 on 3,4,6,7,9,12,13,14,17,18 · −1 on 1,2,5,8,10,11,15,16,19,20 · `xsh`: +1 on 2,3,4,5,8,9,11,12,14,15,17,18,20 · −1 on 1,6,7,10,13,16,19 (XSh's own numbering; stored as items 21–40, i.e. XSh *k* = item 20+*k*) | 50 / 35 | each `[20,31)` past 🟢 · `[31,46)` o'rta 🟡 · `[46,81)` yuqori 🔴 (lower_better) |
| **OPS** | 28 single Ha/Yo'q | `uv` 1,5,…,25 · `sp` 2,6,…,26 · `zn` 3,7,…,27 · `others` 4,8,…,28 — weight 1 on the keyed answer · `total` = all 28 | 0 | **none** (0–7 per component, 0–28 total; higher = less favourable) |
| **Milman** | 40 items; single (3–4 options), #17 multi | `emotional` 1,2,8,13,14,15 · `self_regulation` 3,12,16,18,19,20 · `motivation` 4,9,10,11,21,22 · `stability` 5,6,7,23,24,25 — per-option weights −2…+2 from the key table · `stress_inner_unknown` 23–26 · `stress_outer_unknown` 27–30 · `stress_inner_meaningful` 31–34 · `stress_outer_meaningful` 35–38 (a=2, b=1, v=1, g=0) · `stress_total` 23–38 | 0 | components: `(−∞,0)` o'rtachadan past 🔴 · `[0,1)` o'rtacha 🟡 · `[1,+∞)` o'rtachadan yuqori 🟢 · `stress_total`: `[0,8)` past · `[8,13)` o'rtacha · `[13,33)` yuqori · subtypes: **none** |
| **Frester** | 21 rating 1–9 | `total`: weight 1 on all 21 | 0 | **none** (21–189) |
| **Raven** | 30 single (6/8 options) | `total`: weight 1 on the correct option | 0 | **not seeded** — no key, no norms |

Milman specifics: #17 is a **multi** item scored by no scale; its options carry `group`
(`a` → neytral · `g, d, j, z, i` → stenik · `b, v, e` → astenik) and the result shows the
chosen groups. #39–40 are control items: answers stored and shown, not scored.
Items 18–20 are keyed to `self_regulation` (the item list + original Milman), not to the
emotional column where the delivered key table prints them — **to confirm** (§12.5).

### 12.2 Finalize rules (questionnaire)
- Every item must have an answer (`single`/`rating`: exactly one; `multi`: ≥ 1) →
  otherwise `400` with the missing item numbers.
- Rating value outside `[rating_min, rating_max]` → `400`.
- Writes one `ScaleResult` per scale of the instrument (snapshot of score, label, color).
- Re-finalize is not allowed; super_admin recompute re-runs the formula over stored
  responses with the current keys/bands.

### 12.3 Functional indicators

```
level(reading) = IndicatorBand(indicator, age_min ≤ age ≤ age_max, gender ∈ {athlete, null},
                               valid_from ≤ check.date [latest], lower ≤ value < upper)
                 none → empty label (value still shown)
```
`age` = the athlete's age at the check date (same `age_at` as physical scoring).
Bands may be non-monotonic. Seed (from the client's infographics; lower bound
inclusive, upper exclusive):

**SpO₂ (%) — all ages**: `[95,101)` Me'yor 🟢 · `[93,95)` E'tibor 🟡 · `[90,93)` Past 🟠 ·
`[0,90)` Jiddiy past 🔴.

**Resting pulse (urish/min)** — age-specific "athlete physiological" and normal ranges
(the Yuqori/Juda yuqori split at 120 is taken from the tonometry sheet's pulse table and
applied to all ages — **to confirm**):

| Age | Past (bradikardiya) 🔴 | Sportchi uchun fiziologik 🟢 | Me'yor 🟢 | Yuqori 🟡 | Juda yuqori 🔴 |
|---|---|---|---|---|---|
| 7–10 | < 50 | 50–69 | 70–110 | 111–120 | > 120 |
| 11–14, 15–17 | < 45 | 45–59 | 60–100 | 101–120 | > 120 |
| 18+ | < 40 | 40–59 | 60–100 | 101–120 | > 120 |

**Blood pressure (mmHg)** — each value its own indicator:

| Age | `bp_sys` Me'yor | `bp_dia` Me'yor | Below → Past 🟡 · above → Yuqori 🟠 |
|---|---|---|---|
| 7–10 | 95–115 | 60–75 | outside the normal range |
| 11–17 | 100–120 | 60–80 | outside the normal range |

Adults (18+), from the adult table: `bp_sys` `[0,100)` Past 🟡 · `[100,120)` Optimal 🟢 ·
`[120,130)` Bir oz ko'tarilgan 🟡 · `[130,140)` Yuqori 🟠 · `[140,180)` Ancha yuqori 🔴 ·
`[180,∞)` Juda yuqori 🔴; `bp_dia` `[0,60)` Past 🟡 · `[60,80)` Optimal 🟢 · `[80,90)` Yuqori 🟠 ·
`[90,120)` Ancha yuqori 🔴 · `[120,∞)` Juda yuqori 🔴. The sheet notes child values are
"approximate orientation" — shown as such in the UI.

Finalize: at least one reading; values must be positive and within sane bounds
(SpO₂ ≤ 100, pulse 20–250, BP 30–300) → otherwise `400`.

### 12.4 Edge cases
| Case | Behavior |
|---|---|
| Scale has no bands | score stored + shown, label "daraja belgilanmagan" |
| Score/value falls in a gap between bands | same as no band (data-validation in admin prevents overlap, not gaps) |
| Instrument edited after assessments exist | finalized results keep their snapshot; super_admin may recompute |
| Athlete outside every IndicatorBand age range | reading stored, empty label |
| Draft never finalized | not shown in history/results |

### 12.5 Open items to confirm with the client (diagnostics)
1. **Raven**: the correct-answer key for all 30 items, a raw → IQ/percentile/level table
   (by age?), clean item images, and the right to reproduce them.
2. **Frester**: level thresholds for the total (and per factor?).
3. **OPS**: level thresholds for the components / total.
4. **Milman**: items 18–20 → self-regulation or emotional? Items 23–25 keyed +2 on
   "stability" for "ha" looks inverted — confirm. Is "0 = average" exact, or is there a
   tolerance band? Labels for stress total `< 8` / `> 12`; thresholds for the 4 subtypes;
   how to read mixed #17 answers; any use for control items #39–40.
5. **Khanin**: a score of exactly **30** (doc says "< 30" low and "31–45" moderate; seeded as
   low); the printed labels of answers 1–4; XH item 3 "his etmayapman" (negated in
   translation but keyed as direct).
6. **Functional**: one combined BP category (worse of sys/dia) or separate levels; whether
   functional levels should drive recommendations.
7. **Visibility**: who may see psychological results (coach? ministry?) — minors' data.
