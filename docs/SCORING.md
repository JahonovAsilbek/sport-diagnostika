# SPORT-DIAGNOSTIKA.UZ — Scoring specification

The complete logic of the scoring engine. Models: `DATA_MODEL.md`.
This document is the source of the `apps/scoring/domain/` implementation.

> Status: **methodology agreed**. The exact norm numbers (bounds) are obtained
> from a sports-science specialist — the samples below are **illustrative**.

---

## 1. Principle

A raw test result (`Measurement.raw_value`) → is converted to a **score of 1–5**,
via the `Norm` + `NormBand` table. No bound lives in the code — everything is
data. Score → category percentage → overall percentage → level → color.

```
raw_value ──(NormBand)──► score 1-5 ──(aggregation)──► category % ──► overall %
                                                                        │
                                                          level + color ◄┘
```

---

## 2. Test/indicator catalog (TestType seed)

Each `TestType`: `block · category · unit · direction`.
`direction`: `lower_is_better` (time — less = better) or `higher_is_better`.

### OTM block — 10 tests (5 + 5)

| # | Test | category | unit | direction |
|---|---|---|---|---|
| 1 | Speed (30m sprint) | physical | s | lower |
| 2 | Strength (pull-ups) | physical | reps | higher |
| 3 | Endurance (1000m run) | physical | s | lower |
| 4 | Agility (agility test) | physical | s | lower |
| 5 | Flexibility/coordination | physical | cm | higher |
| 6 | Resting heart rate | functional | bpm | lower |
| 7 | Post-load heart rate | functional | bpm | lower |
| 8 | Recovery time | functional | s | lower |
| 9 | Vital lung capacity | functional | ml | higher |
| 10 | Aerobic capacity | functional | ml/kg/min | higher |

### OPSTTM block — 23 indicators (5 + 5 + 7 + 6)

**Physical (5):** speed · strength · endurance · agility · coordination
**Functional (5):** resting heart rate · post-load heart rate · recovery · lung capacity · aerobic capacity
**Morphofunctional (7):** height · weight · **BMI** · chest circumference · grip strength · body composition (% fat) · somatotype
**Psychological (6):** pre-start anxiety · stress tolerance · reaction speed · attention stability · self-confidence · emotional state

> `direction` is set in the seed for each indicator. Psychological tests are
> usually test scores (higher = better); pre-start anxiety may be inverted
> (the specialist decides).

---

## 3. Raw value → score (1–5) algorithm

1. The matching `Norm` for the athlete's given test, age category, gender (and,
   if needed, sport type, block) is found (lookup — §4).
2. Whichever `NormBand` range the `raw_value` falls into, that band's `score`
   is taken.
3. **Bound rule:** a band range is `[lower_bound, upper_bound)` —
   lower inclusive, upper exclusive (no ambiguity at the join points).
4. **`direction` is accounted for not in the band but in the bound values** —
   that is, norm bands are entered in the order matching `direction` (in the
   30m sprint, a smaller time = score 5). The engine assigns a score based on
   the band range and does not reason about direction.
5. **Out of range (clamp):** a value better than even the best band →
   `score = 5`; worse than even the worst band → `score = 1`. Never an
   error.
6. **If no norm is found:** no score is assigned, the indicator is marked
   `unscored`, the admin is signaled (audit). The session is not finalized (§7).

**Sample (illustrative)** — 30m sprint, age 14–15, male, OTM:

| score | range (s) |
|---|---|
| 5 | < 4.5 |
| 4 | 4.5 – 4.8 |
| 3 | 4.8 – 5.2 |
| 2 | 5.2 – 5.6 |
| 1 | ≥ 5.6 |

---

## 4. Norm lookup and fallback

It takes the first match, going from specific to general:

```
1) test_type + age_category + gender + sport_type + block   (most specific)
2) test_type + age_category + gender + block                (sport-agnostic)
```

A norm with `sport_type = null` = common to all sport types (mainly OTM and
OPSTTM physical/functional). A sport-specific norm (OPSTTM, "matching the
sport type's requirement") overrides the generic one.

Norms are **versioned** (`valid_from`). Since an `Evaluation` is a snapshot,
old evaluations are stored based on the norm at that time; if a norm changes,
the admin recomputes via `POST /evaluations/recompute/`.

---

## 5. Block aggregation

### OTM — 5 levels

```
physical_points   = Σ score(5 physical tests)    # max 25
functional_points = Σ score(5 functional tests)  # max 25
total_points      = physical_points + functional_points   # max 50
percentage        = total_points / 50 × 100
ranking_score     = percentage
```
BMI is computed and its category/color is shown, but it **does not count toward
the score**.

| percentage | level | color |
|---|---|---|
| 90–100 | very high | 🟢 green |
| 75–89 | high | 🟢 green |
| 60–74 | medium | 🟡 yellow |
| 40–59 | low | 🔴 red |
| 0–39 | very low | 🔴 red |

### OPSTTM — 3 levels (categories equally weighted)

```
physical_pct   = Σ score(physical)  / (5 × 5) × 100
functional_pct = Σ score(functional)/ (5 × 5) × 100
morpho_pct     = Σ score(morpho+BMI) / (7 × 5) × 100
psych_pct      = Σ score(psychological)/ (6 × 5) × 100
percentage     = (physical_pct + functional_pct + morpho_pct + psych_pct) / 4
ranking_score  = percentage
```

| percentage (illustrative — confirmed by the specialist) | level | color |
|---|---|---|
| ≥ 75 | high | 🟢 green |
| 50 – 74 | normal | 🟡 yellow |
| < 50 | low | 🔴 red |

> The OPSTTM 3-level bounds (75/50) are **approximate**; the exact value comes
> from the specialist. It is recommended to store the level bounds too in a
> configuration table similar to `Norm` (not hardcoded in the code) —
> `LevelThreshold(block, lower, level)`.

---

## 6. BMI (body mass index)

```
BMI = weight(kg) / height(m)²        # from TestSession.weight_kg, height_cm
```

Health category (both blocks — informational):

| BMI | category |
|---|---|
| < 16 | severe underweight |
| 16 – 18.4 | underweight |
| 18.5 – 24.9 | normal |
| 25 – 29.9 | overweight |
| 30 – 34.9 | obesity class I |
| ≥ 35 | obesity class II |

- **OTM:** only this category + color is shown (`bmi_category`). Not in the score.
- **OPSTTM:** besides the category above, BMI is also converted to a **1–5 score**
  within the morphofunctional category (via a separate `Norm` for BMI — for
  example, the "normal" range = 5 points, decreasing the further out it goes).
  The optimal BMI may differ by sport type (the specialist enters the norm).

---

## 7. Edge cases

| Case | Behavior |
|---|---|
| Incomplete session (block tests not complete) | `finalize` is rejected → `400`, the list of missing tests is returned |
| No norm found | the indicator is `unscored`, the session is not finalized, the admin is signaled |
| Out-of-range value | clamp (5 or 1) — §3.5 |
| Negative/absurd raw value | validation on input (`min/max` on the test type) → `422` |
| Equal `ranking_score` in the ranking | the same `rank` (SQL `RANK()`); secondary order for display: last evaluation date, then full name |
| Block test set | for each block, the list of "mandatory tests" (OTM=10, OPSTTM=23) is determined by `TestType.is_active` + block |

---

## 8. Recommendation generation (dependency)

During `finalize`, once the scores are computed, the `RecommendationRule`s are
checked: if a `condition` (for example "endurance score ≤ 2" or
"functional_pct < 50") is satisfied, a `Recommendation` is written from the
`template_text`. The rules are admin-managed, not in the code. Sample:

- endurance ≤ 2 → "Endurance is low. Increasing the volume of aerobic exercises is recommended."
- recovery ≤ 2 → "The heart rate recovers slowly after load. Increase recovery exercises."

---

## 9. Worked examples

**OTM athlete** (height 1.78, weight 70):
- BMI = 70 / 1.78² = 22.1 → "normal" 🟢 (informational)
- Physical: 5+4+4+5+3 = 21 / 25
- Functional: 4+3+4+4+5 = 20 / 25
- total = 41 / 50 → 82% → **high** 🟢 · ranking_score = 82

**OPSTTM athlete:**
- physical_pct = 22/25 = 88%, functional_pct = 20/25 = 80%,
  morpho_pct = 28/35 = 80%, psych_pct = 24/30 = 80%
- percentage = (88+80+80+80)/4 = 82% → **high** 🟢 · ranking_score = 82

---

## 10. Loading and storing norms

- **Admin UI** (Django admin + DRF) — manual entry/editing of norms + bands.
- **Excel import** — bulk loading of norms (future: management command
  `seed_norms` + fixture).
- **Versioning** — `valid_from`; the old Evaluation snapshot is preserved.

---

## 11. Information needed from the specialist (open)

The following are obtained from the sports-science specialist/client — the
model is ready, only the data is filled in:

1. The exact **NormBand bounds** for each test (in the age × gender × sport cross-section).
2. The OPSTTM **3-level bounds** (high/normal/low percentage).
3. The **measurement methodology** and `direction` of the psychological tests.
4. The sport-type-specific **BMI optimal ranges** (for OPSTTM morpho).
5. The full list of recommendation **rules**.
