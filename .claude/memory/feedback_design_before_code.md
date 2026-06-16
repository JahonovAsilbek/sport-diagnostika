---
name: feedback_design_before_code
description: Do not write code until the user explicitly says go — design/architecture phase is separate
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b9ce4b4d-c064-40c7-9573-f3ffc2d7c413
---

On the SPORT-DIAGNOSTIKA project the user runs a strict **design-first** workflow:
architecture is reviewed and agreed in docs BEFORE any code is written. When I
asked "boshlaymizmi?" and then started scaffolding the Django skeleton without
waiting for an explicit "ha"/"go", the user stopped me ("shoshma. men senga hali
kod yoz demadim") and had me delete the whole `backend/` tree.

**Why:** the user wants to fully settle the architecture/data-model/API on paper
first; premature code is noise during that phase.

**How to apply:** During architecture discussion, produce design artifacts
(`docs/*.md`) only. Writing actual project/source code requires an explicit,
unambiguous go for THAT specific build step — a tentative "shall we start?" is a
question, not approval. Matches the CLAUDE.md "Plan and Build Are Separate Steps"
rule. See [[project_architecture]].
