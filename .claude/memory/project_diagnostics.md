---
name: project_diagnostics
description: B14/F11 diagnostics — psych questionnaires + functional vital signs as a separate `diagnostics` app; keys/bands are data; client gaps listed in SCORING §12.5
metadata:
  type: project
---

**2026-10-07 — client delivered non-physical criteria** (`resources/`, Aug–Sep 2026):
psych methodologies OPS, V.E. Milman, Spielberger–Khanin (XH/XSh), R. Frester, Raven +
two infographics (pulse oximetry SpO₂/pulse, tonometry BP/pulse). Designed as **BLOK B14
(BCKND-72…79) + F11 (FRNTND-33…37)**; docs: `DATA_MODEL.md` §6, `SCORING.md` §12,
`API.md` §15. Old DEF-2/6/7 superseded for psych/functional.

User decisions (2026-10-07):
- **Separate `apps/diagnostics`** — never writes Evaluation/rating/comparison/recommendations.
  **Why:** a psych session would otherwise become the athlete's "latest" evaluation and
  break `rating._latest_ids`; questionnaires don't fit `Measurement`/`NormBand`.
- **Staff transcribe paper forms** (coach/lab_operator/admins); scoping = measurements. No athlete login.
- **Build with what exists:** no band → "daraja belgilanmagan"; Raven not seeded; Milman
  items 18–20 → `self_regulation` (key table prints them under emotional — to confirm).

**How to apply:** one formula `score = Scale.offset + Σ ScaleKey contributions`
(choice: weight if chosen; rating: weight × value) covers all instruments — never add
per-instrument code; client answers become `seed_diagnostics`/admin data changes.
Functional `IndicatorBand` is age×gender×value → label/color, non-monotonic, no clamp.

**Not seen first-hand:** the OPS and Frester documents were never fully read in session —
the auto-mode classifier blocked the extraction agent. Re-read both in full before
BCKND-78 (seed). Milman/Khanin/Raven were extracted in full.

Client questions pending: [[project_open_questions]]. Physical scheme: [[project_physical_readiness]].
