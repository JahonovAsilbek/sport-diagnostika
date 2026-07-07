---
name: project_physical_readiness
description: "SPORT-DIAGNOSTIKA physical-readiness standard — the concrete 10/8/6 scoring, TOIFA/age norms, per-group batteries, daraja bands"
metadata: 
  node_type: memory
  type: project
  originSessionId: b9ce4b4d-c064-40c7-9573-f3ffc2d7c413
---

The platform was scoped to **physical readiness only** on 2026-07-07 (see
[[project_architecture]] for the pivot rationale). This file records the concrete,
non-obvious facts of the state **"Jismoniy tayyorgarlik darajasi"** standard so we don't
re-derive them.

**Source (the ONLY criteria the client delivered):** two files in `resources/` —
`Jismoniy tayyorgarlik mezonlari … 7-17 yoshgacha.docx` and `… 18-29 yosh.doc`.
Everything else (functional / morphofunctional / psychological / BMI) has **no criteria
yet** and is parked in `docs/DEFERRED.md`.

**Scoring shape — 10 / 8 / 6, not 1–5.** Each exercise's raw result maps to **10, 8 or
6 points** (or 0 when below the worst band) via `Norm`/`NormBand`. All bounds are **data
seeded from the tables**, never hardcoded. `direction` is baked into band ordering
(a `lower_is_better` time exercise puts the smallest numbers in the 10-point band), so
the engine only checks which range the raw value falls in.

**Age structure.** TOIFA (`AgeCategory`) ordinal 1–6 spanning ages **7–29**:
`1: 7–8 · 2: 9–10 · 3: 11–12 · 4/5: 13–17 (split TBC) · 6: 18–29`. But **norm lookup is
by numeric age**, not the TOIFA FK: a norm **per single year** for 7–17
(`age_min = age_max = year`) and **one 18–29 bucket**. TOIFA is used to pick the battery
and to group rankings/reports. Norms are **sport- and block-independent** and versioned
by `valid_from`.

**Battery — the crux.** The **5 exercises are chosen per `(TOIFA × gender)`** from a
~9-exercise pool, stored explicitly in `TestBattery` + `BatteryItem` (exactly 5). Two
axes of variation:
- **Exercise #4/#5 differ by gender:** boys/men do **turnikda tortilish** (pull-ups) or
  **yerga tayanib qoʻl bukish**; girls/women do **skameykaga tayanib qoʻl bukish**
  (bench push-ups).
- **Running distance differs by age:** young (7–12) run **30 m**; older (13–29) run
  **100 m**, and 13–17 adds **400 m**.

Per-group batteries seeded from the tables:
- **young (toifa 1–3, 7–12):** 30 m · uzunlikka sakrash · oldinga egilish · push-ups
  (boys yerga / girls skameyka) · argʻimchoqda sakrash.
- **older (toifa 4–5, 13–17):** 100 m · 400 m · uzunlikka sakrash · oldinga egilish ·
  (boys turnikda tortilish / girls skameyka).
- **adults (toifa 6, 18–29):** 100 m · argʻimchoqda sakrash · uzunlikka sakrash ·
  oldinga egilish · (men turnikda tortilish / women skameyka).

**Exercise pool** (Uzbek reference names, with `value_type` for the SPA input):
30 m yugurish (`seconds`) · 100 m yugurish (`seconds`) · 400 m yugurish
(`minsec`→seconds) · turgan joydan uzunlikka sakrash (`count`/cm) · gimnastika
oʻrindigʻida oldinga egilish (`cm_signed`, negatives valid) · argʻimchoqda sakrash
(`count`) · yerga tayanib qoʻl bukish (`count`) · skameykaga tayanib qoʻl bukish
(`count`) · turnikda tortilish (`count`). (agility "9 fishka" is footnoted, not in the
active batteries.) mm:ss times normalize to seconds before band comparison.

**Aggregation → daraja.** `physical_total = Σ points over the 5 exercises` (max 50) →
`daraja` via `DarajaThreshold` (data): **I: 48–50 🟢 · II: 38–46 🟡 · III: 30–36 🔴 ·
<30 none (nishonsiz) 🔴**. `ranking_score = physical_total`. Display flags from the
tables: `≥48` = "next year recommended for the special requirement directly", `=50` =
"gʻoliblik".

**Open items to confirm with the client** (also in `docs/SCORING.md` §11,
[[project_open_questions]]):
1. Exact **TOIFA 4/5 boundary** inside ages 13–17.
2. **Below-worst band → 0** and **above-best clamp → 10** behaviour.
3. **birth_date vs birth_year** precision — norms are per single year, so a full
   birth_date gives the correct age at the session date.
4. Whether **"Maxsus talab boʻyicha"** implies a second (general) norm tier.
5. Confirm `DarajaThreshold` is **constant** across all tables (appears fixed at
   48/38/30).
</content>
