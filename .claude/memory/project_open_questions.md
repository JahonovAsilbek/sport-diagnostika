---
name: project_open_questions
description: SPORT-DIAGNOSTIKA open scope questions — REMIND user about TZ
metadata: 
  node_type: memory
  type: project
  originSessionId: b9ce4b4d-c064-40c7-9573-f3ffc2d7c413
---

**REMINDER for next session:** Ask the user whether they got an answer from the
client about **TZ #13 — "Mashg'ulot yuklamasini nazorat qilish"** (training-load
monitoring: yuklama past/me'yorida/yuqori, tiklanish yetarli emas). It is NOT
yet in the data model / roadmap. The user needs to ask their client how it
should work; decision pending (new block B14, fold into Evaluation, or defer).
Tracked in `docs/ROADMAP.md` → "Scope chegaralari va ochiq savollar".

**Also ask the client next session:** (a) **Personal-data/PII protection** for
minors' health/biometric data — left OPEN, revisit before go-live (legal). (b)
**Report branding** (official letterhead/logo/signature) — format to be confirmed.

**Settled (no work / known limitations):** Device integration (TZ #6/#18) out of
scope — ALL measurements entered **manually**. No athlete unique-ID/de-dup (mitigation:
train moderators). No bulk-norm-import (norms entered manually via admin). No
email/SMS backend (password-reset etc. deferred). No staging env (2-person team).
Initial data migration from the client's Excel = planned later (template/import TBD).

**Incorporated from gap review (in docs):** periods quarter/half/year **derived from
session_date** (calendar, no entity); i18n = **UI strings only**, 4 locales
uz/ru/kk/en (reference content stays Uzbek); athlete transfer history via
`AthleteAssignmentHistory` + ranking dims snapshotted on TestSession/Evaluation;
`TestType.valid_min/valid_max`; login security (throttle + lockout, BCKND-69);
composite ranking index; Excel-import security; QA traceability matrix (DVPS-20).

See [[project_architecture]].
