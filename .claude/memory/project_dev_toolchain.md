---
name: project_dev_toolchain
description: Local backend dev toolchain — Python 3.12 + colima Docker runtime; Postgres/Redis via deploy/docker-compose.yml, host venv connects on localhost
metadata:
  node_type: memory
  type: project
---

Agreed local setup for the backend (both laptops), beyond `git pull` (decided 2026-07-07):

- **Python 3.12** — the target (Django 5.2 LTS). The Macs ship 3.14, which is NOT used.
  Install `brew install python@3.12`; make the venv with it:
  `/opt/homebrew/bin/python3.12 -m venv backend/.venv` then
  `backend/.venv/bin/pip install -r backend/requirements-dev.txt`.

- **Docker runtime = colima** (chosen over Docker Desktop; Docker was not installed).
  `brew install colima docker docker-compose`, then `colima start`. Add
  `/opt/homebrew/lib/docker/cli-plugins` to `~/.docker/config.json` `cliPluginsExtraDirs`
  so the `docker compose` subcommand resolves.

- **Services:** `docker compose -f deploy/docker-compose.yml up -d --wait` starts
  Postgres 16 + Redis 7 with published ports (5432 / 6379), so the **host venv** reaches
  them via `localhost` (`DATABASE_URL`/`REDIS_URL` point at localhost). The full stack
  (db · redis · web · worker · beat, DVPS-4/5/6) also runs from that compose; the app
  containers use `db`/`redis` as hosts (compose `environment:` overrides the localhost
  URLs from `.env`). For host-venv dev you only need `up -d db redis`.

- **`backend/.env`** (git-ignored) holds the local `SECRET_KEY` + URLs + `POSTGRES_*`;
  copy from `backend/.env.example`. `SECRET_KEY` is mandatory (no default) — prod refuses
  to start without it.

**Resume on a fresh machine** (after `git pull`), because `.env`, the venv, and the DB
data are per-machine (not committed):
1. `brew install python@3.12 colima docker docker-compose` (once); `colima start`.
2. `/opt/homebrew/bin/python3.12 -m venv backend/.venv` &&
   `backend/.venv/bin/pip install -r backend/requirements-dev.txt`.
3. `cp backend/.env.example backend/.env` and set a real dev `SECRET_KEY`.
4. `docker compose -f deploy/docker-compose.yml up -d db redis` (host-venv dev).
5. `backend/.venv/bin/python backend/manage.py migrate`, then seed:
   `… seed_catalog` · `… seed_exercises` · `… seed_admin --username admin --password <pw>`
   (all idempotent). `seed_physical` (norms + batteries) arrives with B4.
6. Run tests: `backend/.venv/bin/pytest backend -q`.

**Why:** the repo is developed on two Macs; this records the toolchain so the other
machine doesn't re-decide (e.g. re-pick a container runtime). The Bash shell is **zsh** —
`$var` does not word-split, so don't build commands in a shell variable.
See [[project_architecture]] and [[project_physical_readiness]].
