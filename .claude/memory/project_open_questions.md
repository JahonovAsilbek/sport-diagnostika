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

**NEW — physical-readiness open items (2026-07-07 pivot; also `docs/SCORING.md` §11):**
Ask the client to confirm (1) the exact **TOIFA 4/5 boundary** inside ages 13–17;
(2) **below-worst-band → 0** and **above-best clamp → 10** behaviour; (3) **birth_date
vs birth_year** precision (norms are per single year, so a full birth_date gives correct
age at the session date); (4) whether **"Maxsus talab boʻyicha"** implies a second
(general) norm tier; (5) that `DarajaThreshold` is **constant** across all tables (looks
fixed at 48/38/30). Details: [[project_physical_readiness]].

**Settled (no work / known limitations):** Device integration (TZ #6/#18) out of
scope — ALL measurements entered **manually**. No athlete unique-ID/de-dup (mitigation:
train moderators). No bulk-norm-import (norms entered manually via admin; a
`seed_physical` command loads the tables). No email/SMS backend (password-reset etc.
deferred). No staging env (2-person team). Initial data migration from the client's
Excel = planned later (template/import TBD).

**OBSOLETE after the pivot (do NOT re-raise):** the old **1–5 points → 50 → %** scheme,
the **OTM/OPSTTM two-strategy** eval, and the **sport/block norm fallback**
(`sport+age+gender → age+gender`). Physical norms are **sport- and block-independent**;
scoring is **10/8/6 → I/II/III daraja**. That two-block design is parked in
`docs/DEFERRED.md`, not an open question.

**Incorporated from gap review (in docs):** periods quarter/half/year **derived from
session_date** (calendar, no entity); i18n = **UI strings only**, 4 locales
uz/ru/kk/en (reference content stays Uzbek); athlete transfer history via
`AthleteAssignmentHistory` + ranking dims snapshotted on TestSession/Evaluation;
login security (throttle + lockout); composite ranking index; Excel-import security.

See [[project_architecture]], [[project_physical_readiness]].
