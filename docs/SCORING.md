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

## 6. Deferred: BMI & other categories

BMI, functional, morphofunctional and psychological scoring are **not** part of physical
readiness and have **no criteria yet** — see `DEFERRED.md`. `TestSession.height_cm` /
`weight_kg` are nullable placeholders for that future work.

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
