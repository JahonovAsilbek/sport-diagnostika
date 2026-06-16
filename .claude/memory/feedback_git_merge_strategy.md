---
name: Git pull strategy — merge with --no-ff, never rebase
description: When integrating remote changes, use `git pull --no-ff` (explicit merge commit), not `git pull --rebase`
type: feedback
originSessionId: 88e28f80-af71-4306-99ce-935db4fcd38d
---
When the local branch is behind remote and a push is rejected, do **`git pull --no-ff`** (creates an explicit merge commit) — not `--rebase`.

**Why:** User prefers preserving history with merge commits over linear rebased history. They explicitly corrected me when I tried `--rebase`.

**How to apply:** Any time `git push` is rejected with "fetch first" / "non-fast-forward", run `git pull --no-ff origin <branch>` then `git push`. Don't propose rebase as the default. If a fast-forward is possible (no divergent commits), `--no-ff` still forces a merge commit, which is what the user wants.
