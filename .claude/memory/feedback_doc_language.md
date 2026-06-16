---
name: feedback_doc_language
description: Internal technical docs in English; Uzbek is only for product/UI content
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b9ce4b4d-c064-40c7-9573-f3ffc2d7c413
---

On SPORT-DIAGNOSTIKA the user wants **internal technical docs in English**. I had
written all `docs/*.md` in Uzbek; the user pushed back ("docs nega ingliz tilida
yozilmayapti?") — the example they gave (orientedTV/TASK.md) was fully English.

**Why:** "Uzbek-first" applies to the **product/UI** (landing site, athlete-facing
strings, the TZ source) — NOT to internal engineering docs, which should be English
(industry standard, matches the reference project).

**How to apply:** Write architecture/data-model/API/roadmap/task docs and code
comments in English. Keep Uzbek only for actual UI-facing copy and stored display
values. For these docs the user chose **FULL English** for domain terms too:
levels OTM = very_high/high/medium/low/very_low, OPSTTM = high/normal/low; test
names translated (e.g. "30m sprint"); **TVI renamed to BMI** everywhere (incl.
field names bmi_value/bmi_category). Proper nouns kept: OTM, OPSTTM, region names
(Namangan, etc.), product name. A Uzbek→UI label map will be needed later for
seed/UI. See [[project_architecture]].
