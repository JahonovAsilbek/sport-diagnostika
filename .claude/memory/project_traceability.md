---
name: project_traceability
description: docs/TRACEABILITY.md is the QA acceptance basis (TZ→task matrix + UAT) — keep it in sync when tasks change; build is physical-scope complete
metadata:
  type: reference
---

`docs/TRACEABILITY.md` (DVPS-20) is the **QA acceptance basis**: a matrix mapping every
`SPORT.docx` TZ requirement (the 18 bo'limlar + the main technical task + the "Eng kuchli
sportchilarni aniqlash" / Top-Athletes button) → implementing task IDs → a concrete acceptance
check, plus a role-by-role UAT checklist. It is **hand-maintained, not generated** — when a task's
scope changes, update the matching row (source-of-truth precedence: `docs/TASK.md` > `SPORT.docx` >
other docs).

**Project state (2026-07-13):** the full ledger is complete for the **physical-first** scope —
115/116 non-deferred tasks done before DVPS-20, which closed the last. Remaining work is entirely
**client-criteria-gated** and parked in `docs/DEFERRED.md`: functional readiness (TZ #6), training
load (TZ #13), morphofunctional fields (weight/BMI/height/staj — TZ #1), the percentage scoring
scheme (TZ #7), OPSTTM/OTM report types (TZ #15), device/Polar-H10 integration (TZ #18). See
[[project_open_questions]], [[project_physical_readiness]].
