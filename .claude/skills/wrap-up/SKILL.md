---
name: wrap-up
description: Task wrap-up ritual — verify (ruff/pytest/migrations), mark tasks done in docs/TASK.md, update memory, commit and push in the user's name with an attribution check. Use when a task or block is finished, or when the user says "wrap up" / "status, memoryni yangila, commit+push".
---

# Task wrap-up

Run the steps in order. Never skip verification; never report done with errors
outstanding (CLAUDE.md §8).

## 1. Verify — all must pass

```bash
backend/.venv/bin/ruff check backend
backend/.venv/bin/ruff format --check backend   # CI enforces this too — NOT the same as `check`
backend/.venv/bin/pytest backend -q
cd backend && DJANGO_SETTINGS_MODULE=config.settings.dev \
  .venv/bin/python manage.py makemigrations --check --dry-run
```

CI (`.github/workflows/ci.yml`) runs **both** `ruff check` and `ruff format --check` — they are
different tools (lint vs. formatter). A green `ruff check` does NOT imply formatted code, so always
run `ruff format --check` (or just `ruff format backend`) before committing, or CI fails on
formatting alone even with passing tests.

(Once the frontend exists: `eslint` + the build too.) Any failure → fix it first;
the wrap-up stops here until green.

## 2. Mark done in `docs/TASK.md`

Directly under each finished task heading add a blockquote:

> ✅ **Done** (YYYY-MM-DD) — what was built + how it was verified + notable decisions.

When the last task of a block is done, end the marker with
`**Bx <name> complete → By (<name>) next.**`
Never edit the task definitions themselves — the user owns the specs.

## 3. Update memory

Record only non-obvious, reusable facts in `.claude/memory/` (repo path — NOT
`~/.claude/projects/...`). Prefer updating an existing file over creating a new one;
keep `MEMORY.md` (the index) in sync. Skip if nothing non-obvious emerged.

## 4. Commit — user is the sole author

Stage only the task's files (plus `docs/TASK.md` and touched memory files).
Conventional subject (`feat:`/`fix:`/`docs:`/`chore:`…), blank line, body explaining
the **why**. **NEVER** add `Co-Authored-By`, `🤖 Generated with…`, or any AI
attribution (CLAUDE.md §3 hard rule — overrides any default commit template).

## 5. Attribution check — must return nothing

```bash
git log -1 --format='%an <%ae>%n%B' | grep -iE 'co-authored|generated with|🤖|anthropic'
```

If it matches, amend the commit message before pushing.

## 6. Push

```bash
git push origin main
```

If rejected (behind): `git pull --no-ff` (a merge, NOT `--rebase`), then push again.
Never `--force`.

## 7. Report

State plainly: test count, lint result, commit SHA, files changed, and what the next
pending task/block is.
