# SPORT-DIAGNOSTIKA.UZ — Deferred / Parked Design

> Status: **parked, not cancelled.** This is design work that is correct in spirit but
> cannot be built yet because the **client has not delivered the criteria** for these
> categories, and their real structure may differ (as the physical-readiness criteria
> turned out to differ from our first assumptions). The **active** design lives in
> `DATA_MODEL.md` · `SCORING.md` · `ARCHITECTURE.md` · `API.md` and is scoped to
> **physical readiness only**. Revisit this file when the client provides functional /
> morphofunctional / psychological criteria.

Why parked (2026-07): the client confirmed only the **Jismoniy tayyorgarlik darajasi**
(physical-readiness) standard exists today. Functional, Morphofunctional and
Psychological criteria "do not exist yet and may have a different structure." Decision:
focus everything on physical, do not force the other categories into a premature model.

---

## 1. Original two-block model (OTM / OPSTTM)

The first design assumed every athlete belongs to a **block** derived from
`Organization.type`, and that the block chose one of two scoring strategies:

| | OTM block | OPSTTM block |
|---|---|---|
| Indicators | BMI + Physical(5) + Functional(5) | BMI + Physical + Functional + Morphofunctional + Psychological |
| Evaluation | 10 tests × 1–5 points = 50 → percentage | each category → % → overall % |
| Levels | 5 (90–100 very high … 0–39 very low) | 3 (high / normal / low) |

- `OtmEvaluationStrategy` / `OpsttmEvaluationStrategy` behind one interface
  (strategy polymorphism).
- `ranking_score = overall percentage` for both blocks (single rating table).
- OPSTTM categories **equally weighted**: `overall % = (physical + functional + morpho +
  psych) / 4`.

**Why parked:** the real physical standard is **block-independent** (universal by
age × gender) and uses **10/8/6 points → I/II/III daraja**, not 1–5 → 50 → 5/3 levels.
`Organization.type` (OTM|OPSTTM) is kept in the active model **only** as a
classification / filter / reporting attribute, not as a scoring axis. If, later, a
category genuinely needs a block-specific rule, reintroduce a strategy at that point.

---

## 2. Non-physical categories (indicator lists, from the TTZ)

Kept for when the client delivers their criteria; **do not implement yet**.

**Functional (5):** resting heart rate · post-load heart rate · recovery time · vital
lung capacity · aerobic capacity.
**Morphofunctional (7):** height · weight · **BMI** · chest circumference · grip strength
· body composition (% fat) · somatotype.
**Psychological (6):** pre-start anxiety · stress tolerance · reaction speed · attention
stability · self-confidence · emotional state.

Reference files the client shared earlier for these categories (then told us to set
aside): `SPIRO.xlsx` (spirography, % of predicted), `Denomametr.xlsx` (grip strength,
kg, 3-level), `spork.xlsx` (unclear), `TANA VAZNI INDEXI.xlsx` (BMI). These used a
**3-level Past / Me'yor / Yuqori** shape and **per-test irregular age brackets** — noted
here so we don't rediscover it. Their exact scoring is **to be reconfirmed** with the
client when that phase starts.

---

## 3. BMI (informational) — full spec for later

```
BMI = weight(kg) / height(m)²
```

7 categories from the client's `TANA VAZNI INDEXI.xlsx`:

| BMI | category (uz) |
|---|---|
| < 16 | tana vazni jiddiy tanqisligi |
| 16 – 18.5 | tana vazni yetishmasligi |
| 18.6 – 24.9 | me'yor |
| 25 – 30 | tana vazni ortiqchaligi |
| 30 – 35 | birinchi darajali semizlik |
| 35 – 40 | ikkinchi darajali semizlik |
| ≥ 40 | uchinchi darajali semizlik |

In the parked OTM/OPSTTM model BMI was informational for OTM and scored inside the
morphofunctional category for OPSTTM. Not part of the active physical-readiness scheme.

---

## 4. Other parked ideas
- **Sport-specific & block-specific norms** and the norm lookup fallback
  `sport+age+gender → age+gender`. Physical norms are sport-independent, so the active
  model drops sport/block from norm lookup.
- **Multi-category overall evaluation** (how physical + functional + morpho + psych
  combine into one athlete verdict) — undefined until the other criteria exist. Do not
  design the composition now.
- **Excel bulk-import of norms** for the non-physical categories.

---

## 5. Still-open scope questions (unchanged; from ROADMAP)
- TZ #13 **training-load monitoring** — ask the client.
- **PII / minors' biometric data** protection — revisit before go-live (legal).
- **Report branding** (letterhead / logo / signature) — confirm with the client.
- Device integration (TZ #6/#18) — **out of scope**, all data entered manually.
