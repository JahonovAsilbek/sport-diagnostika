# SPORT-DIAGNOSTIKA.UZ — Tasks

Small, sequential tasks. Source: `ROADMAP.md` (blocks) · `ARCHITECTURE.md` ·
`DATA_MODEL.md` · `API.md` · `SCORING.md`.

Prefixes: **BCKND** (backend) · **DVPS** (devops) · **FRNTND** (frontend).
Each task is one self-contained unit. Block by block: the next block does not
start until the current one is finished.

> Status: **fully split** — all **BCKND (B1–B13)**, all **DVPS (D1–D7)**, and all
> **FRNTND (F1–F10)** blocks are broken into tasks, plus **gap-review additions**
> (BCKND-68/69/70, FRNTND-25/26, DVPS-20) at the end. Tasks are ordered by dependency,
> not by track; cross-track DVPS tasks (7/8/9) sit with the backend blocks that need
> them. Open choices flagged in tasks: TypeScript vs JS (FRNTND-1), UI kit
> (FRNTND-4). Ready to implement on an explicit go, starting BCKND-1.

---

**BLOK B1 — Foundation** (BCKND-1 … BCKND-9) · dependency: none
Goal: a runnable, configured Django+DRF foundation — models, auth config,
Celery, OpenAPI, test infrastructure. No domain logic yet.

---

# BCKND-1 — Repo structure and Python tooling

Create the `backend/` folder and define the dependencies. `requirements.txt`:
Django 5, djangorestframework, djangorestframework-simplejwt, drf-spectacular,
django-environ, psycopg[binary], celery, redis, gunicorn, whitenoise,
django-cors-headers, django-filter. `requirements-dev.txt` (with `-r requirements.txt`):
pytest, pytest-django, factory-boy, Faker, ruff. `pyproject.toml`: ruff
(line-length 100, target-version py312, select E/F/I/UP/B/DJ, isort
known-first-party = apps/config, migrations exclude) + pytest
(`DJANGO_SETTINGS_MODULE=config.settings.dev`, `--reuse-db`). `.gitignore`
(venv, `__pycache__`, `.env`, `staticfiles/`, `media/`, `*.pyc`). `.env.example`
— a sample of all env keys. Versions use compatible-release (`~=`).
Edge case: the local machine is Python 3.14, but the target is 3.12 (Django 5 stable).
Create the venv with 3.12 and set ruff `target-version = "py312"`; do not rely on
3.14-specific syntax. Not an exact pin — a `pip freeze` lock file will be added later.

# BCKND-2 — Django project init + split settings

Create the `config` project. The `config/settings/` package: `base.py`, `dev.py`,
`prod.py` — reads `.env` via django-environ (`BASE_DIR = backend/`). **base**:
INSTALLED_APPS (django.contrib.* + THIRD_PARTY + LOCAL), MIDDLEWARE (security,
whitenoise, corsheaders, sessions, common, csrf, auth, messages, clickjacking),
TEMPLATES, AUTH_PASSWORD_VALIDATORS, i18n (`LANGUAGE_CODE="uz"`,
`TIME_ZONE="Asia/Tashkent"`, `USE_TZ=True`), STATIC/MEDIA (STATIC_ROOT,
MEDIA_ROOT), STORAGES (whitenoise manifest), `DEFAULT_AUTO_FIELD=BigAutoField`.
**dev**: `DEBUG=True`, ALLOWED_HOSTS localhost, `CORS_ALLOW_ALL_ORIGINS=True`.
**prod**: `DEBUG=False`, SECURE_* (SSL redirect, HSTS, secure cookies,
`X_FRAME_OPTIONS=DENY`, `SECURE_PROXY_SSL_HEADER`). `manage.py` default →
`config.settings.dev`; `wsgi.py`/`asgi.py` default → `config.settings.prod`.
Edge case: SECRET_KEY only from env — if absent in prod, the project must not come up
(do not provide a default, let django-environ read it as mandatory). DEBUG must never be True in prod.

# BCKND-3 — PostgreSQL and Redis connection (configuration)

base settings: `DATABASES = {"default": env.db("DATABASE_URL")}` (psycopg v3).
`CACHES` default → `django.core.cache.backends.redis.RedisCache`
(`LOCATION=REDIS_URL`). `REDIS_URL` from env. The services themselves are started later in DVPS-D1
(Docker) — this task is configuration only, it prepares the code wiring.
Edge case: do not connect to Redis at import time (lazy) — the cache should open only when used,
so that even if Redis is down the project still imports / `runserver` comes up.
The DB, however, is required for `migrate`.

# BCKND-4 — common app: base models and mixins

`apps/common` (a manually created minimal app). `models.py`: `TimeStampedModel`
(`created_at` auto_now_add + db_index, `updated_at` auto_now, `Meta.abstract=True`)
— many domain models inherit from it. `pagination.py`: `DefaultPagination`
(page_size 25, `page_size_query_param="page_size"`, max 100). `permissions.py`:
`role_required(*roles)` factory (returns a `BasePermission`, `is_authenticated`
+ `user.role in roles`) and `IsSuperAdmin`. Add `apps.common` to LOCAL_APPS.
Edge case: common has no migrations (only an abstract model) — keep `migrations/__init__.py`
empty. `role_required` relies on the `user.role` string (User is completed in B2/B5)
— no import cycle, just a string comparison.

# BCKND-5 — accounts app + minimal custom User (AUTH_USER_MODEL)

`apps/accounts`. `models.py`: `User(AbstractUser)` — minimal for now (an extra
`phone` field; `role` and region/organization scope are added in B2 and the catalog phase).
`apps.py`: `AccountsConfig(name="apps.accounts")`. In base settings,
`AUTH_USER_MODEL="accounts.User"`. Add to LOCAL_APPS. The sole purpose of this task
— a custom User must exist BEFORE the first `migrate`.
Edge case: ★ The custom User model MUST be created before the first `migrate` —
otherwise Django binds to the default `auth.User` and swapping it later leads
to migration hell. Hence this task sits inside B1, before B2 (roles/JWT).

# BCKND-6 — Celery app wiring

`config/celery.py`: `Celery("sport_diagnostika")`,
`config_from_object("django.conf:settings", namespace="CELERY")`,
`autodiscover_tasks()`, `DJANGO_SETTINGS_MODULE` setdefault. `config/__init__.py`:
`from .celery import app as celery_app`. base settings: `CELERY_BROKER_URL`/
`CELERY_RESULT_BACKEND` (default = REDIS_URL), `CELERY_TASK_TRACK_STARTED=True`,
`CELERY_TIMEZONE="Asia/Tashkent"`. A trivial `debug_task` for a check.
Edge case: the worker must load Django settings — the `DJANGO_SETTINGS_MODULE`
setdefault in `celery.py` is mandatory. `autodiscover_tasks` finds the `tasks.py`
in later apps (used in B7/B11/B12).

# BCKND-7 — DRF + OpenAPI (drf-spectacular) configuration

base settings `REST_FRAMEWORK`: `DEFAULT_AUTHENTICATION_CLASSES`
(JWTAuthentication), `DEFAULT_PERMISSION_CLASSES` (IsAuthenticated),
`DEFAULT_PAGINATION_CLASS` (common.DefaultPagination), `DEFAULT_FILTER_BACKENDS`
(DjangoFilterBackend, SearchFilter, OrderingFilter), `DEFAULT_SCHEMA_CLASS`
(drf_spectacular AutoSchema). `SIMPLE_JWT` (access 30 min, refresh 7 days, rotate +
blacklist) — full login is in B2, but the config is here. `SPECTACULAR_SETTINGS`
(TITLE, VERSION "1.0.0", `SERVE_INCLUDE_SCHEMA=False`). `CORS_ALLOWED_ORIGINS`
from env. `config/urls.py`: `admin/`, `api/v1/` (an empty include list for now),
`api/schema/` (SpectacularAPIView), `api/docs/` (SpectacularSwaggerView).
Edge case: the `rest_framework_simplejwt.token_blacklist` app must be in INSTALLED_APPS
for SIMPLE_JWT BLACKLIST and must be migrated — it is added in this task.
Swagger must not require auth in dev.

# BCKND-8 — Health-check endpoint + URL wiring

A health view in `apps/common`: `GET /api/v1/health/` (AllowAny) →
`{status, db, cache, time}`. It checks the DB with `SELECT 1` and the cache with
`cache.set/get`; if any component is down it returns `503`. It is wired into the
`config` `api_v1` list. This endpoint is later used by DVPS-D3 (nginx) and D7 (monitoring).
Edge case: it should be public (no auth) but lightweight — it must not make a heavy request
(only `SELECT 1`). In a down state, return `503` + show which component failed
(for the load balancer / uptime alert).

# BCKND-9 — Initial migration + test infrastructure + smoke test

`makemigrations` (accounts custom User) + `migrate` (admin, auth, contenttypes,
sessions, token_blacklist, accounts). Root `conftest.py`. The first smoke tests:
(1) settings load, (2) `/api/v1/health/` returns `200`, (3) a superuser is
created (factory-boy + Faker sample factory). `ruff` passes clean. The test DB
is separate; in tests the cache is overridden to locmem. `pytest --reuse-db`.
Edge case: tests must not hit Redis — a fixture/test-settings that switches `CACHES`
to locmem for tests. `--reuse-db` is for speed, but if a migration changes, the test DB
should be recreated. Once this task is finished, B1 is closed — then B2 (auth).

---

**BLOCK B2 — Identity & Access** (BCKND-10 … BCKND-16) · dependency: BCKND-B1
Goal: roles, JWT auth (login/refresh/logout/me), a role-based permission layer,
the region/organization scoping framework, and user management. Note: the
`User.region` / `User.organization` scope **fields** point to catalog models, so
they are added in B3 (catalog); B2 builds the framework that will consume them.

---

# BCKND-10 — Role enum + extend User model

Add `Role(TextChoices)` to `apps/accounts` with: `super_admin`, `region_admin`,
`coach`, `lab_operator`, `ministry`. Add a `role` field to `User`
(`CharField(choices=Role.choices)`), keep `phone` from BCKND-5. Migration.
Region/organization scope FKs are **deferred to B3** (they reference catalog
models); the scoping framework (BCKND-14) is built field-path-driven so it wires
in once those fields exist.
Edge case: pick a least-privilege default (`lab_operator`) so a mis-created user
can't land as admin. Adding `role` to the existing custom User is a simple additive
migration (B1 already made User swappable).

# BCKND-11 — JWT login with user profile

`LoginView` (subclass `TokenObtainPairView`) + `LoginSerializer` that embeds
`UserSerializer` in the token response. `UserSerializer` exposes
`id, username, full_name, role, phone, email, is_active`. Wire
`POST /api/v1/auth/login/`. `SIMPLE_JWT` is already configured (BCKND-7).
Edge case: the login response includes the user's `role` (and later region/org) so
the SPA can build the role-based menu without an extra `/me` call. `UserSerializer`
must never expose the password hash.

# BCKND-12 — Refresh, logout (blacklist), me

`TokenRefreshView` at `/auth/refresh/`. `LogoutView` blacklists the supplied
refresh token (the `token_blacklist` app from BCKND-7). `MeView`
(`GET /auth/me/`) returns the current user's `UserSerializer`.
Edge case: logout must blacklist the refresh token (so it can't mint new access
tokens); access tokens are short-lived (30 min) and not individually revocable —
accept that. A missing/invalid refresh token returns `400`, not `500`.

# BCKND-13 — Role-based permission classes

Flesh out `apps/common/permissions.py` (stubbed in BCKND-4): `role_required(*roles)`
factory, `IsSuperAdmin`, and convenience classes keyed off the `Role` enum.
Encode the role→capability matrix from `API.md` §2. DRF default stays
`IsAuthenticated` (BCKND-7); per-view overrides add the role gates.
Edge case: permission checks compare `user.role` against `Role` values; if `role`
is missing/blank, deny. Keep these classes pure (no DB) so they're cheap per request.

# BCKND-14 — Region/organization scoping framework

A reusable `ScopedQuerysetMixin` / `get_scoped_queryset()` helper in `apps/common`:
given `request.user` (role + region + organization), filter a queryset —
`super_admin`/`ministry` → all; `region_admin` → by region; `coach` → own athletes;
`lab_operator` → by organization. It is **field-path-driven** (the caller passes the
model's region/organization/coach field paths). The `User.region`/`User.organization`
fields are not present yet (added in B3), so this task ships the framework + tests
against a stub; B3/B5 wire the real fields.
Edge case: scoping is enforced server-side in `get_queryset`, never trusting client
filters (API.md §2). Add object-level checks (`has_object_permission`) so a coach
can't fetch an out-of-scope athlete by ID → `403/404`. Mark the User-field wiring as
a follow-up for B3.

# BCKND-15 — User management API (CRUD)

`UserViewSet` (ModelViewSet): list / create / retrieve / update / deactivate.
`UserCreateSerializer` (write-only password via `set_password`). Permissions:
`super_admin` (all) + `region_admin` (own region — enforced once the region field
exists in B3). A `reset-password` action. Routes under `/api/v1/users/`.
Edge case: creating a user must hash the password (`set_password`), never store
plaintext. `region_admin` must not create `super_admin`s or users outside their
region (role+scope check). Deactivate (`is_active=False`) instead of hard delete to
preserve audit/FK integrity.

# BCKND-16 — Auth & permission tests + seed superuser command

pytest tests: login returns tokens+user; refresh works; logout blacklists (a
logged-out refresh can't mint a new access); `/me` returns the profile;
`role_required` allows/denies per role (table-driven); unauthenticated → `401`.
`UserFactory` (factory-boy). A `seed_admin` management command to bootstrap the
first `super_admin` (or document `createsuperuser`).
Edge case: cover each role's allowed/denied matrix explicitly. Once this task is
finished, B2 is closed — then B3 (catalog), which also adds the User region/org
scope fields and wires BCKND-14.

---

**BLOCK B3 — Reference Data** (BCKND-17 … BCKND-25) · dependency: BCKND-B2
Goal: the catalog (Region, District, Organization, SportType, AgeCategory,
WeightCategory, TestType) — models, read APIs, Django admin, and seed data. Also
adds the `User.region`/`User.organization` scope fields and wires the BCKND-14
scoping framework. Norm/NormBand are a separate block (B4).

---

# BCKND-17 — Catalog app + geography models (Region, District)

Create `apps/catalog`. `Region` (`name`, `code` unique) and `District`
(`region` FK, `name`), both on `TimeStampedModel`. Migration. Add `apps.catalog`
to LOCAL_APPS.
Edge case: `District` ordered within its region; unique `(region, name)`.
`Region.code` is a stable identifier used by seeds/imports (don't key on the
display name, which is Uzbek and may vary).

# BCKND-18 — Organization + sport/age/weight reference models

`Organization` (`name`, `type` OTM|OPSTTM as TextChoices, `region` FK,
`district` FK). `SportType` (`name`, `code` unique). `AgeCategory` (`name`,
`min_age`, `max_age` nullable). `WeightCategory` (`sport_type` FK, `gender`,
`name`, `min_kg`, `max_kg`). Migration.
Edge case: `AgeCategory.max_age` is nullable for "22+"; validate that categories
don't overlap. `WeightCategory` belongs to a sport + gender. An athlete's block is
read from `Organization.type` (single source) — never duplicated onto the athlete.

# BCKND-19 — TestType model

`TestType` (`name`, `block` OTM|OPSTTM|both, `category`
physical|functional|morpho|psych, `unit`, `direction` lower|higher_is_better,
`valid_min`, `valid_max`, `order`, `is_active`). Migration. This underpins Norm
(B4), Measurement (B6) and the scoring engine (B7). `valid_min`/`valid_max` bound
acceptable raw input (used by BCKND-40 entry validation).
Edge case: `block=both` means a test is shared by OTM & OPSTTM (the physical /
functional tests); norms still differ per block (Norm has a `block` field).
`category` + `block` together decide which aggregation an indicator feeds (per
SCORING.md). `order` controls UI/seed listing.

# BCKND-20 — User region/organization scope fields + wire scoping

Now that catalog exists, add `region` (FK `Region`, null) and `organization`
(FK `Organization`, null) to `accounts.User`. Migration. Wire the BCKND-14
scoping framework to these real fields. Extend `UserSerializer`/`LoginSerializer`
to include region/organization, and apply region scoping in `UserViewSet`.
Edge case: this resolves the deferred B2 dependency. Validate per role on user
create: `region_admin` must have `region`; `coach`/`lab_operator` must have
`organization`; `super_admin`/`ministry` leave them null. Object-level scope checks
(BCKND-14) now become enforceable.

# BCKND-21 — Catalog serializers + read APIs

DRF serializers + ViewSets for all catalog models. Filters: `districts?region=`,
`organizations?type=&region=`, `weight-categories?sport_type=&gender=`,
`test-types?block=&category=`. Read = any authenticated user; write gated to
`super_admin` (BCKND-13). Routes under `/api/v1/catalog/` per API.md §4.
Edge case: catalog is read-heavy and changes rarely → cache list responses (Redis)
and invalidate on write. Reference lists are NOT region-scoped (everyone sees all
regions/sports); only data entities (athletes/measurements) are scoped.

# BCKND-22 — Django admin for catalog (TZ #16)

Register Region, District, Organization, SportType, AgeCategory, WeightCategory,
TestType in Django admin with `list_display`, search, `list_filter`, and inlines
(District inline under Region; WeightCategory inline under SportType). Satisfies
the reference-data part of the TZ #16 admin panel.
Edge case: admin is for `super_admin` (`is_staff`/`is_superuser`) only and is
distinct from the SPA. Useful filters: `Organization.type`, `TestType.block`/
`category`.

# BCKND-23 — Seed command: geography + categories

Idempotent `seed_catalog` management command (`get_or_create`): 14 regions
(Qoraqalpogʻiston, Toshkent city, 12 regions), their districts, 5 age categories
(12–13, 14–15, 16–17, 18–21, 22+), and the base sport types (30+: gandbol, futbol,
boks, dzyudo, kurash, athletics, swimming, badminton, voleybol, …).
Edge case: idempotent (`get_or_create` by stable `code`) so re-running never
duplicates. Region/sport display `name`s are the real Uzbek values (proper nouns)
even though code/docs are English.

# BCKND-24 — Seed command: test types (OTM + OPSTTM)

Seed `TestType` rows from SCORING.md: OTM 10 (5 physical + 5 functional) and the
OPSTTM-only morpho (7) + psych (6), with correct `block`/`category`/`unit`/
`direction`/`order`. Shared physical & functional tests are seeded once with
`block=both`; morpho/psych are `block=OPSTTM`.
Edge case: `direction` must match SCORING.md (30m sprint = lower_is_better,
pull-ups = higher_is_better, resting heart rate = lower_is_better, …). Because
physical/functional tests are shared (`block=both`), per-block differences live in
the norms (B4), not in duplicate TestType rows.

# BCKND-25 — Catalog tests

pytest: model constraints (unique `code`, age-category non-overlap), API read/write
permissions (`super_admin` writes, others read-only, `ministry` read), filters,
`seed_catalog`/test-type seed idempotency, and the User region/org field +
per-role validation (BCKND-20). Factories for catalog models.
Edge case: assert a non-`super_admin` gets `403` on catalog writes; running the
seed twice yields no duplicates; User scope validation rejects a `region_admin`
without a region. Once this task is finished, B3 is closed — then B4 (norms).

---

**BLOCK B4 — Norms** (BCKND-26 … BCKND-33) · dependency: BCKND-B3
Goal: all data-driven scoring criteria — Norm/NormBand models, the norm
lookup-with-fallback, the raw→score band resolver, percentage→level thresholds,
admin, API, and illustrative seeds. This is the data the scoring engine (B7)
consumes; the engine itself is B7.

---

# BCKND-26 — Norm + NormBand models

`Norm` (header): `test_type` FK, `age_category` FK, `gender`, `sport_type` FK
(null = all sports), `block`, `valid_from`. `NormBand` (line): `norm` FK,
`score` (1–5), `lower_bound`, `upper_bound`. Migration. Both on `TimeStampedModel`.
Edge case: NormBand bounds use the `[lower, upper)` convention; on save validate
that a Norm's 5 bands cover the full range with no gaps/overlaps. `valid_from`
enables versioning (older Evaluations stay reproducible).

# BCKND-27 — Norm lookup with fallback

A selector `get_norm(test_type, age_category, gender, sport_type, block, on_date)`
with precedence: `sport+age+gender` → fall back to `age+gender` (sport_type null);
among matches pick the latest `valid_from <= on_date`. Returns a `Norm` or `None`.
Edge case: most-specific match wins (a sport-specific norm overrides the generic
one). No norm found → return `None`; the caller marks that indicator `unscored`
(SCORING.md §3.6). Version is chosen by the session date, not "now", for
reproducibility.

# BCKND-28 — Band resolution (raw_value → score 1–5)

A pure function `resolve_score(norm, raw_value) → int` in `apps/catalog` domain:
find the band whose `[lower, upper)` contains `raw_value`; clamp out-of-range to
the best (5) / worst (1) band per SCORING.md §3.5. No DB, fully unit-testable.
Edge case: `[lower, upper)` boundaries — no double-counting at band joins. The
resolver is direction-agnostic: `direction` is already baked into how the bands
were entered (SCORING.md §3.4). Below the best / above the worst → clamp, never error.

# BCKND-29 — Norm serializers + nested API

`NormSerializer` with writable nested `NormBand` (per API.md §4). `NormViewSet`:
list + filter (`?test_type=&age_category=&gender=&sport_type=&block=`), CRUD gated
to `super_admin` (`region_admin` read). `GET /catalog/norms/{id}/` returns the
bands. Routes `/api/v1/catalog/norms/`.
Edge case: writable nested bands — creating/updating a norm replaces its band set
atomically (one transaction) and re-runs the gap/overlap validation. Writes are
`super_admin` only.

# BCKND-30 — LevelThreshold config (percentage → level/color)

Model `LevelThreshold` (`block`, `lower_pct`, `level`, `color`) — the
percentage→level cut-offs as DATA, not hardcoded (SCORING.md §5 note). OTM 5
levels (very_high/high/medium/low/very_low), OPSTTM 3 levels (high/normal/low).
Seed defaults. This feeds B7's aggregation → `level`/`color`.
Edge case: keep thresholds data-driven — OPSTTM 75/50 are illustrative and the
specialist confirms them later. Color derives from level per block. Validate the
thresholds partition 0–100 with no gaps.

# BCKND-31 — Django admin for norms + thresholds

Register `Norm` (with `NormBand` inline, 5 rows) and `LevelThreshold` in Django
admin, with `list_filter` by block/test_type/age_category/gender. This is the
primary surface for "baholash mezonlari" (TZ #16) — how the specialist enters real
numbers later.
Edge case: the NormBand inline must run the gap/overlap validation on save.
`super_admin` only.

# BCKND-32 — Seed: illustrative norms + level thresholds

Idempotent seed command: the level thresholds (OTM 5-level, OPSTTM 3-level
defaults) and a small set of **illustrative** norm bands (SCORING.md samples) so
the engine is testable end-to-end before the specialist supplies real values.
Edge case: clearly mark seeded norms as illustrative/placeholder; real values come
from the sport-science specialist (SCORING.md §11). Idempotent (`get_or_create`).

# BCKND-33 — Norm lookup/resolution tests

pytest: lookup precedence (sport-specific beats generic), version selection by
`valid_from`, no-norm → `None`, band resolution (in-range, both boundaries of
`[lower, upper)`, clamp high/low), and the percentage→level mapping. Pure-function
tests need no DB.
Edge case: table-driven tests for band edges (exactly the lower bound, exactly the
upper bound, below min, above max). Verify a sport-specific norm overrides the
generic one. Once this task is finished, B4 is closed — then B5 (athletes).

---

**BLOCK D1 — Containerization** (DVPS-1 … DVPS-6) · dependency: BCKND-B1
Goal: the backend and its dev services (Postgres, Redis, web, worker, beat) run
under Docker Compose; `docker compose up` brings a healthy stack. Nginx, CI,
production deploy come later (D3/D4/D5).

---

# DVPS-1 — Backend Dockerfile

Multi-stage `deploy/Dockerfile` on `python:3.12-slim`. Build stage installs deps
into a venv/wheels; final stage copies them. Set `WORKDIR /app`,
`PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`. Copy `requirements.txt` first,
`pip install`, then copy app code. Create and run as a **non-root** user. Default
`CMD` = `gunicorn config.wsgi` (prod); the dev compose overrides it with
`runserver`.
Edge case: copy `requirements.txt` before the source so the pip layer caches
across code changes. Run as non-root (security). Keep it slim — `psycopg[binary]`
bundles libpq, so no `apt` `libpq-dev`; only add system libs when a later block
(e.g. WeasyPrint for reports, B12) actually needs them.

# DVPS-2 — .dockerignore

`deploy/.dockerignore`: exclude `.git`, `venv`/`.venv`, `__pycache__`, `*.pyc`,
`.env`, `media/`, `staticfiles/`, `node_modules`, `frontend/`, `.pytest_cache`.
Keeps the build context small and prevents artifacts/secrets entering the image.
Edge case: never copy `.env` into the image — secrets are injected at runtime via
compose `env_file`. Excluding it also avoids cache invalidation on local env edits.

# DVPS-3 — Compose: Postgres + Redis services

`deploy/docker-compose.yml`: `db` = `postgres:16` with named volume `pgdata`, env
`POSTGRES_DB/USER/PASSWORD` (from `.env`), healthcheck `pg_isready`; `redis` =
`redis:7-alpine` with a `redis-cli ping` healthcheck. Define a project network.
Compose reads `.env` (from BCKND-1's `.env.example`).
Edge case: give Postgres (`pg_isready`) and Redis (ping) healthchecks so app
services can `depends_on: condition: service_healthy` and not start against a cold
DB. Persist `pgdata` in a named volume so data survives container recreation.

# DVPS-4 — Compose: web (Django) service

`web` service: build from the Dockerfile, `env_file: .env`, `depends_on` db+redis
(`service_healthy`), ports `8000:8000`. Dev `command` =
`python manage.py runserver 0.0.0.0:8000`; bind-mount `../backend:/app` for
hot-reload. `DJANGO_SETTINGS_MODULE=config.settings.dev`.
Edge case: in dev, bind-mount the source for hot-reload; in prod that mount is
removed and gunicorn is used (D5). Keep the dev `command` in compose, not baked
into the image, so prod can override.

# DVPS-5 — Compose: Celery worker + beat services

`worker`: same image, `command: celery -A config worker -l info`, `depends_on`
redis+db, shares `env_file`. `beat`: `command: celery -A config beat -l info`
(default scheduler for now; `django-celery-beat` can be added when scheduled
rating recompute lands in B8/B12). Both reuse the web image (no separate build).
Edge case: worker and beat must wait for redis (broker) and db. Run exactly **one**
beat instance to avoid duplicate scheduled tasks.

# DVPS-6 — Entrypoint + stack bring-up verification

`deploy/entrypoint.sh`: wait-for-db (loop until `pg_isready`/a Python check
passes), run `migrate`, optional `collectstatic`, then `exec` the container
command. Wire the `web` healthcheck to `GET /api/v1/health/` (from BCKND-8).
Verify end-to-end: `docker compose up` brings db/redis/web/worker/beat to healthy
and `/api/v1/health/` returns `200`.
Edge case: `migrate` should run once — for the single dev `web` container the
entrypoint is fine, but for prod (multiple replicas, D5) use a dedicated one-shot
migrate job to avoid concurrent migrations. wait-for-db prevents the app racing a
not-yet-ready Postgres even with healthchecks. Once this task is finished, D1 is
closed.

---

**BLOCK B5 — Athletes** (BCKND-34 … BCKND-38) · dependency: BCKND-B3
Goal: the athlete registry — model, CRUD API with filters, derived age category,
coach linking, and the first real exercise of the BCKND-14 scoping framework
(coach → own athletes is the trickiest scope).

---

# BCKND-34 — Athlete model

`apps/athletes`. `Athlete` (per DATA_MODEL): `last_name`, `first_name`,
`middle_name`, `birth_year`, `gender`, `region` FK, `district` FK, `organization`
FK, `sport_type` FK, `razryad`, `coach` FK→User, `weight_category` FK,
`training_experience`, `main_competitions`, `is_active` (on TimeStampedModel).
Migration. `block` is a property read from `organization.type` (not stored).
Edge case: validate `coach` is a User with `role=coach`, and `district` belongs to
`region`. `age_category` is NOT stored — derived (BCKND-35). `block` derived from
`organization.type` (single source).

# BCKND-35 — Age-category computation

A pure helper `age_category_for(birth_year, on_date)` (athletes domain): age =
`on_date.year - birth_year`, mapped to an `AgeCategory` by `min_age`/`max_age`.
Used at session/evaluation time, not stored.
Edge case: the category depends on the measurement date (compute at session time).
Handle "22+" (`max_age` null). Age below the lowest category → flag as out-of-range,
don't silently bucket it.

# BCKND-36 — Athlete serializers + CRUD API + filters

`AthleteSerializer` (+ computed `age_category`, `block`, `full_name`).
`AthleteViewSet` (CRUD). Filters: `region/district/organization/sport_type/gender/
age_category/block/coach/is_active/search`. Routes `/api/v1/athletes/`. Stub
sub-routes `/athletes/{id}/sessions/`, `/evaluations/`, `/latest-evaluation/`,
`/recommendations/` (filled by B6/B7/B10).
Edge case: the `age_category` filter is computed → translate it to a `birth_year`
range in the SQL query (don't compute per-row in Python at scale).

# BCKND-37 — Athlete scoping (wire BCKND-14)

Wire the BCKND-14 scoping framework to athletes — the canonical scoped entity:
`super_admin`/`ministry` → all; `region_admin` → by `region`; `coach` → `coach=self`;
`lab_operator` → by `organization`. Enforce in `get_queryset` AND object-level
(`has_object_permission`).
Edge case: an out-of-scope athlete fetched by ID must return `403/404`, not the
object. A `coach` creating an athlete is limited to their own organization. This is
where BCKND-14's framework first runs against real `User.region`/`organization`
fields (added in BCKND-20).

# BCKND-38 — Athlete tests + factory

pytest: CRUD, scoping per role (coach sees only own, region_admin only region),
age-category derivation (boundaries, 22+), filters, validation (coach role,
district ∈ region). `AthleteFactory`.
Edge case: scope-leakage tests (out-of-scope athlete by id → 403/404); age-boundary
tests at category edges. Once this task is finished, B5 is closed.

---

**BLOCK B6 — Measurements** (BCKND-39 … BCKND-42) · dependency: BCKND-B4, BCKND-B5
Goal: test sessions and raw measurements, manual entry only (device integration is
out of scope — ROADMAP), with a `finalize` action that triggers scoring (B7).

---

# BCKND-39 — TestSession + Measurement models

`apps/measurements`. `TestSession` (`athlete` FK, `date`, `height_cm`, `weight_kg`,
`block` snapshot, `region`/`organization`/`sport_type` snapshots, `entered_by`
FK→User, `source` manual|excel, `import_batch` FK null, `status` draft|finalized).
`Measurement` (`session` FK, `test_type` FK, `raw_value`). Migration.
Edge case: `block`, `region`, `organization`, `sport_type` are snapshotted from the
athlete at creation, so a later transfer (BCKND-68) doesn't rewrite historical/period
rankings. `source` defaults to `manual` (no device work). `height`/`weight` live on
the session (for BMI), not on the athlete. The period (quarter/half/year) is derived
from `date`.

# BCKND-40 — Session + measurement entry API

`TestSessionViewSet` (CRUD; only `draft` editable). `POST /sessions/{id}/measurements/`
bulk raw values. Filter by athlete. Scoping (`lab_operator` → own org, `coach` →
own athletes). Validate `raw_value` against the TestType min/max.
Edge case: only `draft` sessions are editable; `finalized` are read-only. Reject
absurd/negative values per test. `entered_by = request.user`. Manual entry only.

# BCKND-41 — finalize endpoint + scoring trigger

`POST /sessions/{id}/finalize/`: validate that all required block tests are present
(OTM 10 / OPSTTM 23) — missing → `400` with the missing list — then trigger scoring
(B7) → `Evaluation`, set `status=finalized`, return the evaluation id. Scoring for a
single athlete is computed synchronously.
Edge case: finalize requires the complete required set for the block. Idempotent:
re-finalize recomputes/replaces the Evaluation. The scoring logic itself is B7; this
task wires the trigger + validation.

# BCKND-42 — Measurements tests

pytest: session CRUD, bulk entry, validation (ranges, required set), finalize
success + failure (missing tests), scoping. Factories.
Edge case: finalize with an incomplete set → `400`; draft vs finalized editability;
scope. Once this task is finished, B6 is closed (the engine is B7).

---

**BLOCK B7 — Scoring engine ★** (BCKND-43 … BCKND-48) · dependency: BCKND-B4, BCKND-B6
Goal: the pure scoring domain — BMI, norm→score, OTM/OPSTTM strategies, aggregation,
level/color, the Evaluation snapshot, and the recompute task. The heart of the system.

---

# BCKND-43 — Evaluation + IndicatorScore models

`apps/scoring`. `Evaluation` (`session` 1:1, `athlete` denorm, `block`, **denorm
ranking dims** `region`/`sport_type`/`age_category`/`gender`/`session_date`,
`bmi_value`, `bmi_category`, `physical_pct`, `functional_pct`, `morpho_pct`,
`psych_pct`, `total_points`, `percentage`, `level`, `color`, `ranking_score`,
`computed_at`). `IndicatorScore` (`evaluation` FK, `test_type` FK, `category`,
`raw_value`, `score` 1–5). Migration with a **composite index** on
`(region, sport_type, age_category, gender, block, ranking_score)`.
Edge case: Evaluation is a snapshot (cheap, reproducible rating reads). `session`
1:1 unique. `ranking_score = percentage`. Ranking dims are denormalized/snapshotted
so `RANK()` (B8) scans one indexed table without joining a possibly-transferred
athlete; `age_category` is the snapshot computed at `session_date`.

# BCKND-44 — BMI computation + category (domain)

Pure functions `scoring/domain/bmi.py`: `bmi(weight_kg, height_cm)` and
`bmi_category(value)` per SCORING.md §6 (6 categories). No DB.
Edge case: guard against missing/zero height-weight (no divide-by-zero).
Informational for OTM; scored in OPSTTM morpho via a dedicated BMI norm.

# BCKND-45 — Evaluation strategies (OTM / OPSTTM) (domain)

`scoring/domain/strategies.py`: a strategy interface +
`OtmEvaluationStrategy` (10 tests → 50 → % → 5 levels; BMI informational) and
`OpsttmEvaluationStrategy` (4 categories, **equal-weighted average** → % → 3
levels; BMI inside morpho). Each takes scored indicators + level thresholds and
returns the category %s, percentage, level, color. Pure, unit-testable.
Edge case: OPSTTM categories are equally weighted (avg of the 4 category %s), NOT a
flat sum (DATA_MODEL decision). level/color come from `LevelThreshold` (data, B4).
Strategy is picked by block. Fully testable without a DB.

# BCKND-46 — Scoring service (orchestration) + finalize wiring

`scoring/services.py` `evaluate_session(session)`: for each measurement →
`get_norm` + `resolve_score` (B4) → `IndicatorScore`; compute BMI; run the block
strategy → `Evaluation` snapshot; trigger recommendation generation (B10 hook).
Wire BCKND-41's finalize to call this.
Edge case: an unscored required indicator (no norm) is surfaced, not silently
treated as 0. Wrap Evaluation + IndicatorScores in one transaction. Re-finalize
replaces the prior Evaluation.

# BCKND-47 — Recompute task (Celery)

A Celery task `recompute_evaluations(filter)` for when norms change
(`POST /evaluations/recompute/`, API.md §14). Runs in the worker (D1). Pairs with
DVPS-7 for any scheduled/periodic recompute.
Edge case: recompute can be large — chunk it and run in the worker, never the web
process. The norm version is pinned by session date, so recompute uses the correct
historical norms. It invalidates the rating cache (B8) for the affected partitions.

# BCKND-48 — Scoring engine tests

pytest: BMI calc + categories (boundaries); band-resolution integration; the OTM
worked example from SCORING.md §9 (→ 82% / high); the OPSTTM worked example (§9 →
82% / high); unscored handling; finalize → Evaluation end-to-end.
Edge case: reproduce the SCORING.md §9 worked examples exactly; assert OPSTTM
equal-weighting. Once this task is finished, B7 is closed.

---

**BLOCK B8 — Rating & Ranking** (BCKND-49 … BCKND-52 + DVPS-7) · dependency: BCKND-B7
Goal: rankings via Postgres `RANK()`, the "Top Athletes" feature, region ranking,
and Redis caching + invalidation. Needs Celery Beat (DVPS-7) for periodic refresh.

---

# BCKND-49 — Ranking selectors (RANK() over Evaluation)

Selectors using Postgres window functions: rank athletes within
`(region, sport_type, age_category, gender, block)` by `ranking_score DESC`;
"Top athletes" (limit N); region ranking (count of high-level per region + avg).
Only the latest Evaluation per athlete counts.
Edge case: ties share a rank (`RANK()`); secondary display order = latest
evaluation date, then name. The `age_category` filter → `birth_year` range.
Historical evaluations are excluded (latest per athlete only).

# BCKND-50 — Rating API (top / athletes / regions)

`apps/rating` endpoints per API.md §7: `GET /rating/top/`, `/rating/athletes/`,
`/rating/regions/`, with filters + scoping. Each row returns `rank`, `ranking_score`,
`level`, `color`.
Edge case: scoping applies (a `region_admin` sees only their region's ranking).
Athletes without an Evaluation are excluded.

# BCKND-51 — Redis caching + invalidation

Cache rating responses in Redis keyed by the normalized filter set; invalidate the
affected partition when a new Evaluation is computed (BCKND-46) or recompute runs
(BCKND-47). TTL as a safety net.
Edge case: invalidate on Evaluation write for the matching
`(region, sport, age, gender, block)` so rankings never go stale; TTL is only a
backstop.

# DVPS-7 — Celery Beat database scheduler (django-celery-beat) — needed by B8

Add `django-celery-beat` to requirements; add to INSTALLED_APPS; migrate; switch the
`beat` service command (from DVPS-5) to
`--scheduler django_celery_beat.schedulers:DatabaseScheduler` so periodic jobs
(rating cache refresh / scheduled recompute) are DB-backed and editable from Django
admin (`PeriodicTask`).
Edge case: this replaces the file-based beat schedule from DVPS-5. Exactly ONE beat
instance to avoid duplicate periodic runs. This is the cross-track task B8 (and later
B12) depend on.

# BCKND-52 — Rating tests

pytest: ranking order (desc, ties), top-N, region ranking counts, cache hit +
invalidation, scoping.
Edge case: invalidation test (a new Evaluation changes the cached top); tie-break
order. Once this task is finished, B8 is closed.

---

**BLOCK B9 — Comparison** (BCKND-53 … BCKND-54) · dependency: BCKND-B7
Goal: a side-by-side endpoint for 2–3 athletes.

---

# BCKND-53 — Comparison endpoint

`GET /comparison/?athletes=1,2,3` → side-by-side: each athlete's latest Evaluation
(block, `ranking_score`, level, category %s, indicator scores) plus the `leader`.
`apps/comparison` is thin — it reads the scoring selectors. Scoping applies.
Edge case: 2–3 athletes only (validate count); all must be in scope (else `403`);
athletes without an Evaluation are shown as no-data. Cross-block comparison (OTM vs
OPSTTM) — `ranking_score` is comparable (% for both) but indicator sets differ, so
surface per-category where available.

# BCKND-54 — Comparison tests

pytest: 2 and 3 athletes, leader detection, scope enforcement, missing-evaluation
handling, count validation.
Edge case: `>3` or `<2` athletes → `400`; out-of-scope athlete → `403`. Once this
task is finished, B9 is closed.

---

**BLOCK B10 — Recommendations** (BCKND-55 … BCKND-57) · dependency: BCKND-B7
Goal: rule-based recommendations generated on `finalize`, with admin-managed rules.

---

# BCKND-55 — RecommendationRule + Recommendation models

`RecommendationRule` (`test_type`/`category`, `condition` (level/score threshold),
`template_text`, `is_active`). `Recommendation` (`evaluation` FK, `rule` FK, `text`,
`category`, `created_at`). Migration. Django admin for rules (TZ #16).
Edge case: rules are DATA (admin-editable), not hardcoded. `condition` is a simple
declarative shape (indicator/category, operator, threshold). Keep it evaluable
without code changes.

# BCKND-56 — Recommendation generation (on finalize)

A service `generate_recommendations(evaluation)`: evaluate active rules against the
evaluation's indicator scores / category %s and create `Recommendation` rows. Hook
into BCKND-46 (scoring service). Expose `GET /athletes/{id}/recommendations/`
(latest evaluation) + `/recommendation-rules/` CRUD (`super_admin`).
Edge case: regenerate on re-finalize (clear old, create new). Empty if nothing
matches. Rule evaluation is pure/declarative → unit-testable.

# BCKND-57 — Recommendation tests

pytest: rule matching (threshold met / not met), generation on finalize,
regeneration, rules CRUD permissions.
Edge case: a rule firing exactly at the threshold boundary; rules CRUD gated to
`super_admin`. Once this task is finished, B10 is closed.

---

**BLOCK B11 — Excel import/export** (BCKND-58 … BCKND-61 + DVPS-8) · dependency: BCKND-B5, BCKND-B6
Goal: bulk Excel upload pipeline (staging → validation → commit) + template. Needs a
shared media volume (DVPS-8).

---

# BCKND-58 — ImportBatch + ImportRow models + template download

`ImportBatch` (`uploaded_by`, `file`, `status`, `row_count`, `error_count`,
`created_at`). `ImportRow` (`batch` FK, `row_number`, `raw_data` json, `status`,
`errors` json). `GET /imports/template/?block=` → an Excel template (openpyxl).
Edge case: template columns match the block's required fields + test set. The
uploaded file is stored in MEDIA (needs the DVPS-8 media volume).

# BCKND-59 — Import upload + async validation (Celery)

`POST /imports/` (multipart) → `ImportBatch` (status `uploaded`) + launch a Celery
task to parse + validate rows into `ImportRow` (`validated`/`error`).
`GET /imports/{id}/` → status + rows + errors. openpyxl parse.
Edge case: validation runs in the worker (large files); each row is validated
independently (athlete match, value ranges, required tests); errors are collected
per row — the batch is not aborted on the first error. **Upload security:** validate
file type/extension + size limit + max row count; sanitize against CSV/Excel formula
injection (cells starting with `= + - @` neutralized); never trust client-supplied
values.

# BCKND-60 — Import commit

`POST /imports/{id}/commit/` → create athletes/sessions/measurements from the
`validated` rows (skip `error` rows) in a transaction; status `committed`. Shares
the same validation/finalize rules as manual entry.
Edge case: only validated rows commit; partial commit is allowed (error rows skipped
+ reported). Guard against re-commit (don't double-insert).

# DVPS-8 — Media volume in compose — needed by B11/B12

Add a named `media` volume mounted at MEDIA_ROOT on BOTH the `web` and `worker`
services (the worker writes/reads files, the web serves downloads). Ensures uploaded
imports (B11) and generated reports (B12) persist and are shared.
Edge case: web and worker MUST share the same media volume. For prod, large uploads
also need Nginx `client_max_body_size` (handled in D3). Persist across container
recreation.

# BCKND-61 — Import tests

pytest: template generation, upload → validation (valid + error rows), commit (skips
errors), permissions/scoping.
Edge case: a file with mixed valid/invalid rows → partial commit + error report;
re-commit guard. Once this task is finished, B11 is closed.

---

**BLOCK B12 — Reports** (BCKND-62 … BCKND-64 + DVPS-9) · dependency: BCKND-B8
Goal: async PDF/Word/Excel report generation with status/download. Needs WeasyPrint
system libs (DVPS-9) and the shared media volume (DVPS-8).

---

# BCKND-62 — Report model + request API

`Report` (`type` athlete|region|sport|opsttm|otm|republic, `format` pdf|word|excel,
`params` json, `requested_by`, `status` pending|processing|done|failed, `file`,
`created_at`, `completed_at`). `POST /reports/` → `202` + id; `GET /reports/`,
`/reports/{id}/`, `/reports/{id}/download/`. `apps/reports`.
Edge case: scope the `params` (a `region_admin` can only request their region).
Status lifecycle pending → processing → done|failed. Download only when `done`.

# BCKND-63 — Report generators (Excel/Word/PDF) + Celery task

Celery task `generate_report(report_id)`: build the dataset (rating/scoring/athlete
selectors), render to the chosen format — openpyxl (Excel), python-docx (Word),
WeasyPrint (PDF) — save to MEDIA, set status.
Edge case: runs in the worker (heavy); WeasyPrint needs system libs (DVPS-9); files
saved to the shared media volume (DVPS-8). On failure set `status=failed` + error;
never leave a report `pending` forever (timeout).

# DVPS-9 — WeasyPrint system libraries in backend image — needed by B12

Add WeasyPrint's native deps to the backend Dockerfile (apt): libcairo2,
libpango-1.0-0, libpangocairo-1.0-0, libgdk-pixbuf-2.0-0, libffi, plus a font
package for Uzbek glyphs. Add `weasyprint`, `openpyxl`, `python-docx` to
requirements.
Edge case: these libs grow the image — install only in the final stage and clean apt
lists. Without them WeasyPrint imports but fails at render. A font package is
required for non-Latin / Uzbek glyphs in PDFs.

# BCKND-64 — Report tests

pytest: request → `202`, status transitions, download when `done`, each format
generates, scoping on `params`.
Edge case: requesting a report outside scope → `403`; download before `done` →
`409`; a failed generation → `status=failed`. Once this task is finished, B12 is closed.

---

**BLOCK B13 — Audit & Stats** (BCKND-65 … BCKND-67) · dependency: BCKND-B2
Goal: an audit log of mutations and the role-scoped dashboard/stats endpoint.

---

# BCKND-65 — AuditLog model + signals

`AuditLog` (`user`, `action`, `entity_type`, `entity_id`, `changes` json,
`created_at`, `ip`). Capture create/update/delete on key models (athletes,
measurements, evaluations, users, norms) via signals or a mixin.
Edge case: capture who/what/when + IP (from `X-Forwarded-For` behind Nginx). Log
mutations only, never reads. Don't recursively log AuditLog itself.

# BCKND-66 — Dashboard / stats endpoint

`GET /stats/overview/` → role-scoped counts (`athletes_total`, `by_block`,
`by_level`, `regions`, `recent_sessions`) per API.md §12.
Edge case: numbers are limited to the user's scope (region/org). Use DB-side
aggregate queries and cache the result.

# BCKND-67 — Audit & stats tests

pytest: audit entries on create/update/delete, IP capture, stats scoping +
correctness.
Edge case: stats respect scope (a `region_admin` sees only their region's counts);
audit captures the acting user. Once this task is finished, B13 is closed — all
BCKND blocks are now split.

---

**BLOCK D2 — Local dev environment** (DVPS-10 … DVPS-11) · dependency: DVPS-D1
Goal: a frictionless local workflow — a Makefile, a bootstrap script, seed targets,
and dev docs.

---

# DVPS-10 — Makefile + dev scripts

`Makefile` targets wrapping `docker compose`: `up`, `down`, `logs`, `migrate`,
`makemigrations`, `shell`, `test`, `lint`, `format`, `seed`, `createsuperuser`,
`psql`. A `bootstrap` script: copy `.env.example`→`.env`, build, up, migrate, seed.
`seed` runs all idempotent seeders in order (catalog → test types → norms).
Edge case: targets run from the repo root; `seed` must be idempotent (re-runnable).
Document targets in the README.

# DVPS-11 — Dev docs + .env workflow

README / dev docs: prerequisites (Docker; Python 3.12 for non-container tooling),
first-run steps, how to run tests/lint/format, how dev vs prod settings differ. The
`.env` workflow: never commit `.env`; `.env.example` is the template.
Edge case: confirm `.env` is gitignored (BCKND-1) and keep `.env.example` current —
every env key documented with a sane sample.

---

**BLOCK D3 — Nginx + static** (DVPS-12 … DVPS-13) · dependency: DVPS-D1
Goal: Nginx reverse proxy serving the Vue SPA + proxying the API, with a prod
compose profile.

---

# DVPS-12 — Nginx reverse proxy config

`deploy/nginx.conf`: serve the Vue SPA build (history-mode fallback), proxy `/api/`
and `/admin/` to gunicorn (`web`), serve `/static/` and `/media/`, gzip,
`client_max_body_size` for Excel imports (B11), security headers, and forward
`X-Forwarded-Proto`/`X-Forwarded-For`.
Edge case: SPA history fallback (`try_files $uri /index.html`);
`client_max_body_size` large enough for imports; `/media` served read-only; forward
`X-Forwarded-*` for `SECURE_PROXY_SSL_HEADER` (BCKND-2) and audit IP (BCKND-65).

# DVPS-13 — Nginx service + prod compose override

Add an `nginx` service and a `docker-compose.prod.yml` override: gunicorn `web`
command (not runserver), nginx serving SPA + static/media volumes, no source
bind-mount. `collectstatic` runs before nginx serves.
Edge case: dev (runserver, no nginx) vs prod (gunicorn + nginx) via compose
profiles/override files. `collectstatic` into the shared static volume first.

---

**BLOCK D4 — CI pipeline** (DVPS-14) · dependency: DVPS-D1
Goal: automated lint + test + build on every push/PR.

---

# DVPS-14 — CI pipeline (lint + test + build)

CI workflow (GitHub Actions): on push/PR run `ruff check`, `ruff format --check`,
`pytest` (with Postgres + Redis service containers), and a `docker build` check.
Cache pip.
Edge case: spin up Postgres + Redis service containers for tests; unit tests use
locmem cache (BCKND-9) so they don't strictly need Redis, but integration tests may.
Fail the pipeline on any lint or test failure; keep the build check fast.

---

**BLOCK D5 — Production deploy** (DVPS-15 … DVPS-16) · dependency: DVPS-D3
Goal: deploy to the VPS with gunicorn, managed secrets, and TLS.

---

# DVPS-15 — VPS provisioning + deploy

Provision the VPS (Docker + compose), deploy via the prod compose, manage
env/secrets on the server (not in the image/repo), size gunicorn workers, run a
one-shot `migrate` job before `web` starts, `collectstatic`. A deploy script/runbook.
Edge case: secrets live only on the server (`.env`, restrictive perms); `migrate`
runs as a dedicated one-shot job (avoid concurrent migrations across replicas);
gunicorn worker count tuned to cores.

# DVPS-16 — TLS (Let's Encrypt)

TLS termination at Nginx via Let's Encrypt (certbot / acme companion) with
auto-renewal and an HTTP→HTTPS redirect (matches prod `SECURE_SSL_REDIRECT`). Domain
`sport-diagnostika.uz`.
Edge case: automate cert renewal; redirect all HTTP→HTTPS; HSTS is already set in
prod settings (BCKND-2). Use staging certs first to avoid Let's Encrypt rate limits.

---

**BLOCK D6 — Backup & restore** (DVPS-17) · dependency: DVPS-D5
Goal: automated, tested database + media backups.

---

# DVPS-17 — Backup & restore

Automated PostgreSQL backups (`pg_dump` on a schedule via host cron or Celery Beat),
media backups, a retention policy, an off-server copy, and a documented + tested
restore procedure.
Edge case: store backups off the app server; the restore procedure MUST be tested (a
backup you can't restore is useless); include the media volume; schedule via Celery
Beat (DVPS-7) or host cron.

---

**BLOCK D7 — Monitoring & logging** (DVPS-18 … DVPS-19) · dependency: DVPS-D5
Goal: uptime/health monitoring and centralized logging + error tracking.

---

# DVPS-18 — Health checks + uptime monitoring

Wire `/api/v1/health/` (BCKND-8) to an uptime monitor and container healthchecks
(partly from D1). Alert on down. Basic resource monitoring (CPU/mem/disk).
Edge case: the health endpoint returns `503` when db/cache are down (BCKND-8) so the
monitor/LB reacts; route alerts (email/Telegram).

# DVPS-19 — Centralized logging + error tracking

Structured Django `LOGGING` config, log aggregation/rotation, and error tracking
(e.g. Sentry) for both the backend and the Celery worker.
Edge case: never log secrets/PII; rotate logs; capture worker (Celery) errors too,
not just web; correlate request IDs. Once this task is finished, the DVPS track is
fully split.

---

**BLOCK F1 — Frontend foundation** (FRNTND-1 … FRNTND-4) · dependency: none
Goal: the Vue 3 SPA scaffold — tooling, API client with token refresh, auth store,
and the UI kit.

---

# FRNTND-1 — Vite + Vue 3 project scaffold

Create `frontend/` with Vite + Vue 3 (`<script setup>`), Vue Router, Pinia, ESLint +
Prettier. Folder structure: `views`, `components`, `stores`, `api`, `router`,
`composables`, `assets`. Vite dev proxy `/api` → backend.
Edge case: ESLint + Prettier from day one to match backend cleanliness. **Decision
to confirm: TypeScript vs plain JS** — TS recommended for maintainability. Dev proxy
avoids CORS locally.

# FRNTND-2 — API client (axios) + interceptors

An axios instance (`baseURL=/api/v1`): request interceptor attaches the access
token; response interceptor on `401` refreshes the token and retries, and on refresh
failure logs out. Centralized error mapping to Uzbek messages (API.md §1 format).
Edge case: single-flight refresh lock (no parallel refresh storms); on refresh
failure clear auth + redirect to login.

# FRNTND-3 — Auth store (Pinia)

`auth` store: `login` (POST `/auth/login` → store tokens + user), `logout`
(blacklist refresh + clear), `me`, token persistence (localStorage), `isAuthenticated`
and `role` getters. Restore the session on app load via `/me`.
Edge case: expose `role` for guards/menu; restore + validate session on reload;
accept the localStorage tradeoff for tokens.

# FRNTND-4 — UI kit + base layout primitives

Configure a UI library (PrimeVue or Naive UI), base components (button, table, form
inputs, modal, toast), theme, and the **English-enum → Uzbek-label** map (levels,
categories) so the UI reads in Uzbek. Responsive base (TZ #15 "mobile-friendly").
Edge case: pick ONE UI kit and stick to it. The product UI is Uzbek-facing — this is
where English enum keys (high/normal/low, etc.) map to Uzbek display labels.

---

**BLOCK F2 — Auth & layout** (FRNTND-5 … FRNTND-7) · dependency: BCKND-B2, FRNTND-F1
Goal: login, route guards, and the role-aware app shell.

---

# FRNTND-5 — Login page

Login view (username/password, validation, error display, "remember me") wired to
the auth store. Visual language consistent with the existing landing.
Edge case: show server errors (invalid credentials) in Uzbek; disable submit while
pending; redirect to the intended route after login.

# FRNTND-6 — Route guards + role-based routing

Router guards: require auth for app routes (redirect to login otherwise); role-based
route access (e.g. user management only for super_admin/region_admin); per-role
landing.
Edge case: guard runs before each navigation; an unauthorized role → 403 view;
preserve the intended destination through login.

# FRNTND-7 — App shell (navbar/sidebar) + role-based menu

App layout: top navbar, sidebar with a role-filtered menu, user dropdown
(profile/logout), and the user's region/org context. Responsive (collapsible on
mobile).
Edge case: menu items filtered by role (match API.md §2 matrix); show the user's
scope; mobile-collapsible sidebar.

---

**BLOCK F3 — Catalog UI** (FRNTND-8 … FRNTND-9) · dependency: BCKND-B3, BCKND-B4
Goal: reference-data views + reusable pickers, plus norm management for super_admin.

---

# FRNTND-8 — Catalog browse views + reusable pickers

Read views for reference data (regions, sport types, age categories, test types) and
reusable select components (region/district cascade, sport picker, etc.) used across
forms and filters. Cache catalog in a Pinia store.
Edge case: catalog rarely changes → cache it; the reusable pickers are shared by
athlete forms (F4) and rating filters (F7).

# FRNTND-9 — Norms & catalog management (super_admin)

Admin UI the SPA owns: a Norm + bands editor and any catalog CRUD not left to Django
admin. Gated to super_admin.
Edge case: the band editor enforces 5-band coverage client-side (mirror BCKND-26);
super_admin only; pure reference CRUD can stay in Django admin if simpler.

---

**BLOCK F4 — Athletes UI** (FRNTND-10 … FRNTND-12) · dependency: BCKND-B5
Goal: athlete list, card, and create/edit form.

---

# FRNTND-10 — Athlete list + filters

A paginated athlete table with filters
(region/district/org/sport/gender/age/block/coach/search); the server enforces
scope. Row → athlete card.
Edge case: filters map to query params (API.md §5); don't duplicate scope logic
client-side; debounce search; loading/empty states.

# FRNTND-11 — Athlete card page

Athlete detail: personal data, BMI, session history, latest evaluation summary,
recommendations, and a link to comparison. Tabbed.
Edge case: handle athletes with no evaluation yet (no-data states); show derived age
category + block.

# FRNTND-12 — Athlete create/edit form

Form with reference pickers (region→district cascade, org, sport, weight category,
coach), validation, role-gated writes.
Edge case: district depends on region (cascade); client validation mirrors the
server (coach role, district ∈ region); only write-allowed roles see the form.

---

**BLOCK F5 — Measurements UI** (FRNTND-13 … FRNTND-15) · dependency: BCKND-B6, BCKND-B11
Goal: session + measurement entry, finalize, and the Excel import UI.

---

# FRNTND-13 — Session + measurement entry

Create a session (date, height, weight) and enter raw values via a form generated
from the block's TestType set (OTM 10 / OPSTTM 23); save as draft.
Edge case: the form is data-driven from TestType; validate ranges client-side; only
draft is editable.

# FRNTND-14 — Finalize + result display

Finalize action (server validates the required set); on success show the computed
evaluation (score, %, level, color). Handle the missing-tests `400`.
Edge case: show which tests are missing on `400`; finalized → read-only; show the
color indicator immediately.

# FRNTND-15 — Excel import UI

Template download, upload, per-row validation progress/errors, commit of valid rows;
polls `/imports/{id}`.
Edge case: show per-row errors; allow partial commit; poll async status; large-file
upload feedback.

---

**BLOCK F6 — Results UI** (FRNTND-16 … FRNTND-17) · dependency: BCKND-B7
Goal: the evaluation result view and history/trend.

---

# FRNTND-16 — Evaluation result view

Detailed evaluation: per-category breakdown (physical/functional/morpho/psych %s),
per-indicator scores, BMI + category, overall level + color, recommendations.
Edge case: render OTM (5-level, 2 categories) vs OPSTTM (3-level, 4 categories)
layouts; color-coded; Uzbek level labels.

# FRNTND-17 — Evaluation history + trend

An athlete's evaluations over time (table + a simple trend chart of `ranking_score`).
Edge case: the chart handles 1 vs many points; this is the coach's monitoring view
(progress over time).

---

**BLOCK F7 — Rating UI** (FRNTND-18 … FRNTND-19) · dependency: BCKND-B8
Goal: the rating table, the headline "Top Athletes" feature, and region ranking.

---

# FRNTND-18 — Rating table + Top Athletes

Rating views: filters (sport/region/age/gender/block), a ranked table
(rank/score/level/color), with "Top Athletes" prominent — the headline feature (TZ).
Edge case: the "Top Athletes" filter set (sport+region+age+gender) is the headline
feature; color indicators; scoped by role.

# FRNTND-19 — Region ranking view

A region-ranking table (high-count per region, average) for ministry/super_admin.
Edge case: visible to ministry/super_admin (region_admin sees own); optional
chart/map.

---

**BLOCK F8 — Comparison UI** (FRNTND-20) · dependency: BCKND-B9
Goal: the side-by-side comparison view.

---

# FRNTND-20 — Comparison view

Pick 2–3 athletes and show them side-by-side: scores, category %s,
indicator-by-indicator, with the leader highlighted.
Edge case: 2–3 only; highlight the leader and the per-indicator winner; handle
cross-block comparison gracefully.

---

**BLOCK F9 — Recommendation & Report UI** (FRNTND-21 … FRNTND-22) · dependency: BCKND-B10, BCKND-B12
Goal: recommendations display and the report request/download flow.

---

# FRNTND-21 — Recommendations view

Show generated recommendations on the athlete/evaluation; (admin) manage
recommendation rules.
Edge case: recommendations come from the latest evaluation; rules management gated to
super_admin.

# FRNTND-22 — Reports UI (request + download)

Request a report (type, format, params), see its status
(pending/processing/done/failed), and download when ready; polls `/reports/{id}`.
Edge case: async status polling; download enabled only when `done`; scope params to
the user.

---

**BLOCK F10 — Dashboard UI** (FRNTND-23 … FRNTND-24) · dependency: BCKND-B13
Goal: the role-scoped dashboard with stats and charts.

---

# FRNTND-23 — Dashboard / home

A role-scoped dashboard: key counts (athletes, by block, by level), recent activity,
quick links; fed by `/stats/overview`.
Edge case: role-scoped numbers; different emphasis per role (ministry → national,
coach → own athletes).

# FRNTND-24 — Charts + polish

Charts (level distribution, by region), responsive polish, and consistent
loading/empty/error states + Uzbek i18n across the app.
Edge case: charts degrade gracefully with little data; consistent Uzbek labels
(English enum → Uzbek map); mobile responsiveness (TZ #15). Once this task is
finished, the FRNTND track — and the whole task breakdown — is complete.

---

**GAP-REVIEW ADDITIONS** — extra tasks from the post-breakdown gap analysis. Each
extends an existing block (noted inline). Numbering continues; they are NOT a new
block.

---

# BCKND-68 — Athlete transfer history (extends B5)

`AthleteAssignmentHistory` model (`athlete`, `organization`, `region`, `district`,
`sport_type`, `coach`, `valid_from`, `valid_to` null=current, `changed_by`,
`reason`). A transactional transfer service: on any change to an athlete's
org/region/district/sport/coach, close the open record (`valid_to`) and open a new
one, keeping the athlete's current denormalized fields in sync. Endpoints:
`GET /athletes/{id}/history/` and a transfer action.
Edge case: exactly ONE open (`valid_to=null`) record per athlete; the transfer is
atomic; record `changed_by` + `reason`. New TestSessions snapshot the current
assignment (BCKND-39), so past evaluations/rankings are unaffected by transfers.

# BCKND-69 — Login security: throttling + brute-force lockout (extends B2)

DRF throttling (a hard scoped throttle on the login endpoint + a general API rate
limit), brute-force protection (track failed logins, temporary account/IP lockout
after N failures within a window), `429` responses.
Edge case: lock after N failed attempts then cool-down; don't reveal whether a
username exists; throttle login harder than the general API; behind Nginx use
`X-Forwarded-For` for the real client IP (consistent with audit). Security is a
priority (per the owner).

# BCKND-70 — Period filter (backend) — rating/comparison/history/reports (extends B8, B12)

Add an optional `period_type` (quarter|half|year) + value to the rating, comparison,
evaluation-history and report endpoints; translate it to a `session_date` range
(calendar boundaries); when absent, use the latest Evaluation per athlete.
Edge case: "latest per athlete within the period"; region ranking and reports honor
the period; combine with role scope; no period entity (derived from `session_date`).

# FRNTND-25 — i18n (vue-i18n, 4 locales) (extends F1)

Set up vue-i18n with 4 locales — **uz, ru, kk, en** — for UI strings only. A locale
switcher in the app shell; persist the choice; default `uz`. The
English-enum → localized-label maps (levels, categories, BMI) live in the locale files.
Edge case: reference/content data (region/sport/test names, recommendation texts)
stays Uzbek (decision #13) — only UI chrome + enum labels are translated; fall back
to `uz` for missing keys.

# FRNTND-26 — Period filter UI + locale switcher (extends F6/F7/F9)

A period selector (quarter/half/year + value) on the rating, evaluation-history,
comparison and reports views, wired to the backend period filter (BCKND-70). Plus the
locale switcher from FRNTND-25.
Edge case: default to "latest" (no period); consistent across views; reflected in the
URL/query for shareable links.

# DVPS-20 — QA: TZ → task traceability matrix + UAT checklist (QA/process)

Create `docs/TRACEABILITY.md` mapping every TZ requirement (the 18 sections + the
two-block scoring rules + the "Top Athletes" feature) to the implementing task(s) and
an acceptance check; plus a UAT checklist for client sign-off.
Edge case: every TZ requirement must map to ≥1 task (coverage gaps surface here);
keep it updated as tasks change; this is the QA acceptance basis.
