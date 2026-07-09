# SPORT-DIAGNOSTIKA.UZ

An athlete monitoring platform for Uzbek student-athletes (physical-readiness first) —
Django 5 + DRF backend, Vue 3 SPA, PostgreSQL, Celery + Redis, Docker. A modular monolith.

```
backend/    Django + DRF (apps/: accounts, catalog, athletes, measurements, scoring,
            rating, comparison, recommendations, reports, audit, stats, common)
frontend/   Vue 3 + Vite SPA
deploy/     Dockerfile, docker-compose, entrypoint
docs/       ARCHITECTURE · DATA_MODEL · API · SCORING · ROADMAP · TASK
index.html, premium/   the static marketing landing (no build)
```

Full design lives in `docs/`; per-task progress in `docs/TASK.md`.

## Prerequisites

- **Docker** with Compose. On macOS this project uses **colima** (not Docker Desktop):
  `brew install colima docker docker-compose && colima start`.
- **Python 3.12** — only for the non-container dev tooling (tests, lint, format).

## First run

```bash
make bootstrap
```

This copies `backend/.env.example → backend/.env`, builds the image, starts the stack
(the `web` container migrates on startup), seeds the reference data, and creates the
`super_admin`. When it finishes:

- API — http://localhost:8000/api/v1/
- Admin — http://localhost:8000/admin/ (`admin` / `DJANGO_SUPERUSER_PASSWORD`)
- API docs — http://localhost:8000/api/docs/

Re-running `make bootstrap` is safe — every seeder is idempotent.

## Everyday commands

`make help` lists them all. The common ones:

| Command | What it does |
|---|---|
| `make up` / `make down` | start / stop the stack (db, redis, web, worker, beat) |
| `make logs s=web` | tail logs (optionally one service) |
| `make migrate` / `make makemigrations` | run migrations |
| `make seed` | reload reference data (catalog → exercises → physical norms) |
| `make createsuperuser` | create the `super_admin` (idempotent) |
| `make shell` / `make psql` | Django shell / psql into the db |
| `make test` / `make lint` / `make format` | test / lint / format (local venv) |

## Tests, lint, format

These run on a **local virtualenv** (the dev tools aren't in the runtime image). One-time
setup, then run against the running stack's Postgres:

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cd ..
make up      # Postgres must be running for the tests
make test    # pytest (config.settings.test, --reuse-db)
make lint    # ruff check
make format  # ruff format + --fix
```

## Settings & the `.env` workflow

Settings are split under `backend/config/settings/`: `base.py` (shared) → `dev.py`
(local, `DEBUG=True`) / `test.py` (Postgres test DB, locmem cache, eager Celery) /
`prod.py` (`DEBUG=False`, HTTPS/HSTS, trusted-proxy IP for the audit log).

`backend/.env` is **git-ignored** — never commit it. `backend/.env.example` is the
committed template; keep it current, with a sane sample for every key (Django secret,
Postgres + Redis URLs, CORS origin, the `super_admin` bootstrap password).

## Production profile

`deploy/docker-compose.prod.yml` overlays the base stack with the production topology:
**nginx** on `:80` reverse-proxying a **gunicorn** `web` (no source bind-mount — the baked
image is shipped), serving the Vue SPA build and `/static/` + `/media/` from volumes.

```bash
make prod-build && make prod-up      # or: docker compose -f deploy/docker-compose.yml \
                                     #        -f deploy/docker-compose.prod.yml up -d --build
make prod-logs s=nginx
make prod-down
```

Notes:
- **HTTP-only for now** — TLS (Let's Encrypt) lands in D5. The overlay sets
  `SECURE_SSL_REDIRECT=False` so the pre-TLS stack doesn't 301-loop; `config.settings.prod`
  re-enables HTTPS hardening by default once certs exist.
- `ALLOWED_HOSTS` in the prod `.env` **must** keep `127.0.0.1` (the container healthcheck
  sends `Host: 127.0.0.1`; `DEBUG=False` rejects unlisted hosts) alongside the real domain.
- The SPA isn't built yet (F-blocks), so `/` returns 404 until `frontend/dist` exists — the
  API (`/api/`), admin (`/admin/`), `/static/`, and `/media/` all work meanwhile.

## Marketing landing

The static landing site is separate from the platform (no backend, no build): the lite
version at the repo root (`index.html`), the premium version under `premium/`. Preview
with `python3 -m http.server`.
