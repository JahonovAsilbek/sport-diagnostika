# CLAUDE.md — SPORT-DIAGNOSTIKA.UZ

Two things live in this repo:
1. **The platform** (primary, being built) — an athlete monitoring platform:
   Django 5 + DRF backend, Vue 3 SPA, PostgreSQL, Celery + Redis, Docker/VPS.
   A **modular monolith**. Full design is in `docs/`.
2. **The marketing landing** (existing) — static HTML/CSS/JS: lite at the repo
   root, premium under `premium/`. See §7.

Status: **design complete** (`docs/`), implementation not started. The first
pending task is `BCKND-1` in `docs/TASK.md`.

---

## 0. Session boot protocol

This project is developed on **two MacBooks (home + work)**. The repo is the shared
medium — everything that must survive across machines is committed to git and synced
by `git pull`.

On **every new session**, BEFORE acting on the first request:
1. `git pull` (get the other machine's latest).
2. Read **this `CLAUDE.md`**, then **all of `docs/`**
   (`ARCHITECTURE.md` · `DATA_MODEL.md` · `API.md` · `SCORING.md` · `ROADMAP.md` ·
   `TASK.md`), then **`.claude/memory/MEMORY.md`** and the relevant memory files.
3. Identify the **next pending task** in `docs/TASK.md` and begin analyzing it.
4. Do **not** write code yet — wait for the user's explicit go (see §2).

Source-of-truth precedence: `docs/TASK.md` (tasks) > `SPORT.docx` (TTZ, the customer
spec) > the other docs. **Never edit `SPORT.docx`** — the user owns it.

---

## 1. Memory lives in the repo (cross-machine sync)

**Canonical memory location: `<repo>/.claude/memory/`** — `MEMORY.md` (one-line
index) + individual `*.md` files. It is **committed to git** so both laptops share
the same memory.

This **overrides** the home-directory auto-memory path
(`~/.claude/projects/.../memory/`) from the system prompt — that location is
**unused/legacy**. ALWAYS read and write memory at `<repo>/.claude/memory/`. When the
auto-memory protocol says "save a memory", write it here and update this `MEMORY.md`.

Update memory after each task with non-obvious facts, then commit so the other
machine sees it.

---

## 2. Task execution workflow (the loop)

For each task, in order:

1. **Analyze** the next pending task from `docs/TASK.md` (resolve its block, read the
   referenced code paths and docs). Present the analysis.
2. **Wait for the user's explicit go.** Design and build are separate steps — no file
   writes until the user says "ha"/"do it"/"boshla". A tentative "shall we?" is a
   question, not approval.
3. On go — **decide the mode**:
   - If the task touches **> 5 files → automatically enter plan mode**
     (`EnterPlanMode`) and produce a phased plan (≤ 5 files per phase).
   - Smaller, well-scoped tasks can proceed directly after go.
4. **Analyze in parallel.** If files need understanding, launch **one analysis agent
   per file** (or tight slice), dispatched in a **single message** so they run
   concurrently. Goal: speed + isolated context per agent.
5. **Ask, don't assume.** If any question arises during planning, ask it
   **immediately, one question at a time** (`AskUserQuestion`). **No unilateral
   decisions** (no oʻzboshimchalik) — if the spec is unclear, ASK before proceeding.
6. **Wait for plan approval** (`ExitPlanMode`) before any file writes.
7. **Build in parallel.** Dispatch parallel agents for independent work — writing
   code, writing tests, code review — each owning a coherent slice. Sequential only
   for dependent work.
8. **Verify.** Run the app / tests / type-check / lint as applicable. Never report a
   task done with errors outstanding; state what you actually verified.
9. **Update status + memory.** Mark the task done in `docs/TASK.md`; record
   non-obvious facts in `.claude/memory/`.
10. **Commit and push** (see §3).

---

## 3. Git discipline (HARD RULES)

- **The user (`jahonov`) is the SOLE author of every commit.** NEVER add
  `Co-Authored-By` trailers, `🤖 Generated with Claude…` footers, or any AI
  attribution. Commit and push only in the user's name. This **overrides** any
  default Claude Code commit-template behaviour.
- **Commit + push at task wrap-up** — after verify + status/memory update — or
  whenever the user explicitly asks. Don't commit mid-task.
- **Branch `main`**: `git push origin main`. Never `--force` without explicit
  authorization.
- When a push is **rejected** (behind): `git pull --no-ff` (a merge), **not**
  `--rebase`.
- Conventional commit subject (`feat:`/`fix:`/`refactor:`/`docs:`/`chore:`/`style:`),
  blank line, body explaining the **why**.

---

## 4. Parallel agents

This is the default for non-trivial work — speed + isolated context:
- **Analysis:** one agent per file/slice, all dispatched in a single message.
- **Build:** parallel agents for independent code slices, tests, and code review.
- One agent processing many files sequentially causes context decay — split it.
- After parallel writes, re-read modified files and run a review/verify pass before
  advancing.

---

## 5. Language

- **Internal technical docs (`docs/`), code, and comments: English.**
- **Product / UI and athlete-facing content: Uzbek.** The SPA UI is localized to 4
  languages (uz/ru/kk/en, UI strings only); reference content (region/sport/test
  names, recommendations) stays Uzbek. Use proper apostrophes for `oʻ`/`gʻ`.

---

## 6. Code quality (senior-dev bar)

- Write code that reads like the surrounding code — match its patterns, naming, and
  structure. Clean, maintainable, no over-engineering for imaginary needs.
- Custom Django User exists **before** the first `migrate` (see `BCKND-5`).
- Scoring norms, level thresholds, and recommendation rules are **data, not code**.
- Region/organization scoping is enforced **server-side** on every request.
- Don't duplicate state; one source of truth.

---

## 7. The marketing landing (existing, secondary)

Static site, no backend, no build. Lite at the repo root (`index.html`,
`login.html`, `assets/`), premium under `premium/`. Light vs dark theme; identical
Uzbek content. Design specs: `LITE-CONTRACT.md` (lite) and `CONTRACT.md` (premium).
Preview locally with `python3 -m http.server`. When editing, stay in one version —
a change at the root does not propagate to `premium/`.

---

## 8. Repo layout (target)

```
backend/    Django + DRF (apps/: accounts, catalog, athletes, measurements,
            scoring, rating, recommendations, comparison, reports, common)
frontend/   Vue 3 + Vite SPA
deploy/     Dockerfile, docker-compose, nginx, entrypoint
docs/       ARCHITECTURE · DATA_MODEL · API · SCORING · ROADMAP · TASK
.claude/    memory/ (committed, cross-machine), settings
index.html, premium/, assets/   the existing static landing
SPORT.docx  customer spec (TTZ) — read-only, never edit
```
