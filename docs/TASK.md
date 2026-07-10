# SPORT-DIAGNOSTIKA.UZ — Tasks

Small, sequential tasks. Source: `ROADMAP.md` (blocks) · `ARCHITECTURE.md` ·
`DATA_MODEL.md` · `API.md` · `SCORING.md`. Parked scope: `DEFERRED.md`.

Prefixes: **BCKND** (backend) · **DVPS** (devops) · **FRNTND** (frontend).
Each task is one self-contained unit. Block by block: the next block does not
start until the current one is finished.

> Status: **fully split — physical-readiness scope.** All **BCKND (B1–B13)**, all
> **DVPS (D1–D7)**, and all **FRNTND (F1–F10)** blocks are broken into tasks, plus the
> **gap-review additions** (BCKND-68/69/70, FRNTND-25/26, DVPS-20). The physical-first
> re-scope rewrote **B3** (Exercise pool / TestBattery / TOIFA), **B4** (Norm/NormBand
> 10/8/6 + DarajaThreshold + `seed_physical`), **B6** (5-exercise battery entry), **B7**
> (single scheme: raw → points → physical_total → daraja), and **B8–B12** (physical). The
> parked tasks (functional/morpho/psych/BMI, OTM/OPSTTM strategies, weight categories,
> sport/block norms) are collected — **not deleted** — in the **DEFERRED** section at the
> end (+ `docs/DEFERRED.md`). B1/B2 and the DVPS/JWT/Celery/OpenAPI plumbing are unchanged.
> Open choices flagged in tasks: TypeScript vs JS (FRNTND-1), UI kit (FRNTND-4). Ready to
> implement on an explicit go, starting BCKND-1.

---

**BLOK B1 — Foundation** (BCKND-1 … BCKND-9) · dependency: none
Goal: a runnable, configured Django+DRF foundation — models, auth config,
Celery, OpenAPI, test infrastructure. No domain logic yet.

---

# BCKND-1 — Repo structure and Python tooling
> ✅ **Done** (2026-07-07) — `backend/`: requirements(.txt/-dev.txt), pyproject.toml (ruff+pytest), .gitignore, .env.example. venv deferred (needs local Python 3.12).

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
> ✅ **Done** (2026-07-07) — `config/` project, split `settings/{base,dev,prod}` (env-driven, `SECRET_KEY` mandatory), `manage.py`→dev, `wsgi/asgi`→prod. Verified: ruff, `check`, `makemigrations --check`, prod `DEBUG=False` + refuses to start without `SECRET_KEY`.

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
> ✅ **Done** (2026-07-07) — base: `DATABASES = env.db("DATABASE_URL")` (psycopg v3), `CACHES` RedisCache with lazy connection. Verified: `check` passes with Redis down; DATABASES parses to the postgresql engine.

base settings: `DATABASES = {"default": env.db("DATABASE_URL")}` (psycopg v3).
`CACHES` default → `django.core.cache.backends.redis.RedisCache`
(`LOCATION=REDIS_URL`). `REDIS_URL` from env. The services themselves are started later in DVPS-D1
(Docker) — this task is configuration only, it prepares the code wiring.
Edge case: do not connect to Redis at import time (lazy) — the cache should open only when used,
so that even if Redis is down the project still imports / `runserver` comes up.
The DB, however, is required for `migrate`.

# BCKND-4 — common app: base models and mixins
> ✅ **Done** (2026-07-07) — `apps/common`: `TimeStampedModel` (abstract), `DefaultPagination` (25/max 100), `role_required()`/`IsSuperAdmin`. Empty `migrations/` (abstract-only). Verified: ruff, `check`, `makemigrations --check` (no changes).

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
> ✅ **Done** (2026-07-07) — `apps/accounts`: `User(AbstractUser)` + `phone`, `AUTH_USER_MODEL="accounts.User"`. Initial migration deferred to BCKND-9. Verified: ruff, `check`, `get_user_model()` resolves, model valid (dry-run "Create model User").

`apps/accounts`. `models.py`: `User(AbstractUser)` — minimal for now (an extra
`phone` field; `role` and region/organization scope are added in B2 and the catalog phase).
`apps.py`: `AccountsConfig(name="apps.accounts")`. In base settings,
`AUTH_USER_MODEL="accounts.User"`. Add to LOCAL_APPS. The sole purpose of this task
— a custom User must exist BEFORE the first `migrate`.
Edge case: ★ The custom User model MUST be created before the first `migrate` —
otherwise Django binds to the default `auth.User` and swapping it later leads
to migration hell. Hence this task sits inside B1, before B2 (roles/JWT).

# BCKND-6 — Celery app wiring
> ✅ **Done** (2026-07-07) — `config/celery.py` (app `sport_diagnostika`, `DJANGO_SETTINGS_MODULE` setdefault, `autodiscover_tasks`, `debug_task`), `config/__init__` exports `celery_app`, base `CELERY_*` → REDIS_URL. Verified: broker connects to Redis, `debug_task` registered.

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
> ✅ **Done** (2026-07-07) — `REST_FRAMEWORK` (JWTAuth, IsAuthenticated, DefaultPagination, filter backends, spectacular AutoSchema), `SIMPLE_JWT` (30 min / 7 d, rotate+blacklist), `SPECTACULAR_SETTINGS`, `token_blacklist` app, `CORS_ALLOWED_ORIGINS`, urls `api/v1/` + `api/schema/` + `api/docs/`. Verified: schema generates+validates; `/api/schema/` and `/api/docs/` are public 200.

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
> ✅ **Done** (2026-07-07) — `apps/common/views.health`: `GET /api/v1/health/` (AllowAny) → `{status, db, cache, time}`; `SELECT 1` + cache round-trip; 503 when a component is down. Verified: 200 when up; 503 (cache=down, db=ok) when cache unreachable.

A health view in `apps/common`: `GET /api/v1/health/` (AllowAny) →
`{status, db, cache, time}`. It checks the DB with `SELECT 1` and the cache with
`cache.set/get`; if any component is down it returns `503`. It is wired into the
`config` `api_v1` list. This endpoint is later used by DVPS-D3 (nginx) and D7 (monitoring).
Edge case: it should be public (no auth) but lightweight — it must not make a heavy request
(only `SELECT 1`). In a down state, return `503` + show which component failed
(for the load balancer / uptime alert).

# BCKND-9 — Initial migration + test infrastructure + smoke test
> ✅ **Done** (2026-07-07) — `accounts.0001_initial` + `migrate` (admin/auth/contenttypes/sessions/token_blacklist/accounts) applied to Postgres. `conftest.py`, `config.settings.test` (locmem cache — no Redis, fast hashing, plain static storage), `UserFactory` (factory-boy+Faker). 3 smoke tests pass (settings load, `/api/v1/health/` 200, superuser). ruff clean, pytest `--reuse-db`. **B1 Foundation complete → B2 next.**

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
> ✅ **Done** (2026-07-07) — `Role` TextChoices (super_admin/region_admin/coach/lab_operator/ministry, Uzbek labels) + `User.role` (default `lab_operator`). Migration `0002_user_role` applied. Verified: ruff, check, `makemigrations --check` clean, enum + default.

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
> ✅ **Done** (2026-07-07) — `LoginView` (TokenObtainPairView + `LoginSerializer` embedding `UserSerializer`), `UserSerializer` (id/username/full_name/role/phone/email/is_active — no password), `POST /api/v1/auth/login/`. Verified: 200 with token pair + embedded profile (role, full_name).

`LoginView` (subclass `TokenObtainPairView`) + `LoginSerializer` that embeds
`UserSerializer` in the token response. `UserSerializer` exposes
`id, username, full_name, role, phone, email, is_active`. Wire
`POST /api/v1/auth/login/`. `SIMPLE_JWT` is already configured (BCKND-7).
Edge case: the login response includes the user's `role` (and later region/org) so
the SPA can build the role-based menu without an extra `/me` call. `UserSerializer`
must never expose the password hash.

# BCKND-12 — Refresh, logout (blacklist), me
> ✅ **Done** (2026-07-07) — `/auth/refresh/` (TokenRefreshView), `LogoutView` (blacklists the refresh; 400 if missing/invalid), `MeView` `GET /auth/me/`. Verified: refresh 200; me 200 (401 unauthenticated); logout 204 then reusing that refresh → 401 (blacklisted).

`TokenRefreshView` at `/auth/refresh/`. `LogoutView` blacklists the supplied
refresh token (the `token_blacklist` app from BCKND-7). `MeView`
(`GET /auth/me/`) returns the current user's `UserSerializer`.
Edge case: logout must blacklist the refresh token (so it can't mint new access
tokens); access tokens are short-lived (30 min) and not individually revocable —
accept that. A missing/invalid refresh token returns `400`, not `500`.

# BCKND-13 — Role-based permission classes
> ✅ **Done** (2026-07-07) — `permissions.py`: `role_required` factory + role constants + convenience classes (`IsSuperAdmin`/`IsRegionAdmin`/`IsCoach`/`IsLabOperator`/`IsMinistry`/`IsUserAdmin`), string-based so `common` stays dependency-free. Verified: allow/deny matrix; blank role and unauthenticated denied.

Flesh out `apps/common/permissions.py` (stubbed in BCKND-4): `role_required(*roles)`
factory, `IsSuperAdmin`, and convenience classes keyed off the `Role` enum.
Encode the role→capability matrix from `API.md` §2. DRF default stays
`IsAuthenticated` (BCKND-7); per-view overrides add the role gates.
Edge case: permission checks compare `user.role` against `Role` values; if `role`
is missing/blank, deny. Keep these classes pure (no DB) so they're cheap per request.

# BCKND-14 — Region/organization scoping framework
> ✅ **Done** (2026-07-07) — `scoping.py`: `scope_queryset()` + `ScopedQuerysetMixin` (field-path-driven — super/ministry→all, region_admin→region, coach→own, lab_operator→org; unassigned/unauth → empty scope; object-level 404 via scoped `get_object`). `User.region`/`organization` fields wired in B3. Verified: branching logic against a stub user.

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
> ✅ **Done** (2026-07-07) — `UserViewSet` (ModelViewSet, `IsSuperAdmin`; region_admin/own-region deferred to B3), `UserWriteSerializer` (write-only always-hashed password, Django validators, Uzbek errors), soft-delete (`is_active=False`), `reset-password` action, `/api/v1/users/` (filter role/is_active, search). Verified: CRUD, hashed password not echoed, weak password → 400, non-super → 403, delete → soft-deactivate.

`UserViewSet` (ModelViewSet): list / create / retrieve / update / deactivate.
`UserCreateSerializer` (write-only password via `set_password`). Permissions:
`super_admin` (all) + `region_admin` (own region — enforced once the region field
exists in B3). A `reset-password` action. Routes under `/api/v1/users/`.
Edge case: creating a user must hash the password (`set_password`), never store
plaintext. `region_admin` must not create `super_admin`s or users outside their
region (role+scope check). Deactivate (`is_active=False`) instead of hard delete to
preserve audit/FK integrity.

# BCKND-16 — Auth & permission tests + seed superuser command
> ✅ **Done** (2026-07-07) — pytest: login (tokens+profile), refresh, logout-blacklist, `/me` (+401), `role_required` matrix (table-driven), unauthenticated. `UserFactory` gains `role` + a `super_admin` trait; `seed_admin` management command (idempotent, requires a password). **22 tests pass**, ruff clean, `makemigrations --check` clean. **B2 Identity & Access complete → B3 next.**

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
Goal: the catalog (Region, District, Organization, SportType, **AgeCategory (TOIFA)**,
the **Exercise pool**, **TestBattery + BatteryItem**) — models, read APIs, Django admin,
and seed data. Also adds the `User.region`/`User.organization` scope fields and wires the
BCKND-14 scoping framework. Norm/NormBand are a separate block (B4).

---

# BCKND-17 — Catalog app + geography models (Region, District)
> ✅ **Done** (2026-07-07) — `apps/catalog` + `Region` (unique `code`), `District` (region FK, unique `(region, name)`). In catalog migration `0001`.

Create `apps/catalog`. `Region` (`name`, `code` unique) and `District`
(`region` FK, `name`), both on `TimeStampedModel`. Migration. Add `apps.catalog`
to LOCAL_APPS.
Edge case: `District` ordered within its region; unique `(region, name)`.
`Region.code` is a stable identifier used by seeds/imports (don't key on the
display name, which is Uzbek and may vary).

# BCKND-18 — Organization + SportType + AgeCategory (TOIFA) models
> ✅ **Done** (2026-07-07) — `Organization` (`type` OTM|OPSTTM classification-only, region/district FK), `SportType` (unique `code`), `AgeCategory` (TOIFA `ordinal` 1–6 unique, `age_min`/`age_max`). In `0001`.

`Organization` (`name`, `type` OTM|OPSTTM as TextChoices, `region` FK,
`district` FK). `SportType` (`name`, `code` unique). `AgeCategory` (TOIFA)
(`ordinal` 1–6 unique, `name`, `age_min`, `age_max`). Migration.
Edge case: `AgeCategory` is the **TOIFA** grouping — six ordinals: `1: 7–8 · 2: 9–10 ·
3: 11–12 · 4/5: 13–17 (split TBC) · 6: 18–29`; validate the ranges don't overlap.
`Organization.type` (OTM|OPSTTM) is a **classification / filter** attribute only ("which
athletes are OPSTTM") — it does **not** affect physical scoring and is never duplicated
onto the athlete. `weight_category` is **deferred** (morpho) — see the DEFERRED section.

# BCKND-19 — Exercise pool + TestBattery + BatteryItem models
> ✅ **Done** (2026-07-07) — `Exercise` (unit/value_type/direction/order/is_active), `TestBattery` (unique `(age_category, gender)`), `BatteryItem` (unique order + unique exercise per battery). Shared `Gender` enum in `common`. In `0001`. Verified: models create + constraints (dup battery, dup code, PROTECT FKs) enforced.

`Exercise` (the exercise pool; replaces the old `TestType` — now deferred, see DEFERRED):
`name` (Uzbek), `unit`, `value_type` (`seconds`|`minsec`|`count`|`cm_signed`),
`direction` (`higher`|`lower_is_better`), `order`, `is_active`. `TestBattery`
(`age_category` FK, `gender`, `is_active`). `BatteryItem` (`battery` FK, `exercise` FK,
`order`) — exactly 5 per battery. Migration.
Edge case: `value_type` tells the SPA how to render/store the input (mm:ss → seconds;
signed cm for flexibility). A `TestBattery` is one per `(age_category, gender)` and defines
the ordered 5 exercises the athlete performs — the entry form (B6) is built from it. #4/#5
differ **by gender** (boys turnikda tortilish ↔ girls skameykaga tayanib qoʻl bukish) and
running distances differ **by age** (30 m → 100 m). `unit`/`value_type` bound how raw input
is validated (BCKND-40). The battery **rows** are seeded together with the norm tables by
`seed_physical` (BCKND-32).

# BCKND-20 — User region/organization scope fields + wire scoping
> ✅ **Done** (2026-07-07) — `User.region`/`organization` FKs (nullable, PROTECT) + migration `0003`. Wired BCKND-14 scoping into `UserViewSet` (`ScopedQuerysetMixin`, region_admin → own region); `UserSerializer`/`LoginSerializer` now embed region/organization `{id,name}`; per-role validation (region_admin needs region; coach/lab_operator need organization); region_admin guard (no super_admin, no cross-region/org). Verified: scoping (super sees all, region_admin only own), 403 guards, 400 validation, profile embeds region, 22-test regression green.

Now that catalog exists, add `region` (FK `Region`, null) and `organization`
(FK `Organization`, null) to `accounts.User`. Migration. Wire the BCKND-14
scoping framework to these real fields. Extend `UserSerializer`/`LoginSerializer`
to include region/organization, and apply region scoping in `UserViewSet`.
Edge case: this resolves the deferred B2 dependency. Validate per role on user
create: `region_admin` must have `region`; `coach`/`lab_operator` must have
`organization`; `super_admin`/`ministry` leave them null. Object-level scope checks
(BCKND-14) now become enforceable.

# BCKND-21 — Catalog serializers + read APIs
> ✅ **Done** (2026-07-07) — `catalog/serializers.py` (a ModelSerializer per model; `TestBattery` nests ordered `items → exercise`), `catalog/api.py` (`CatalogViewSet` + `ReadOnlyOrSuperAdmin`: read = any authenticated, write = `super_admin`), `catalog/urls.py` (`SimpleRouter`: regions/districts/organizations/sport-types/age-categories/exercises/batteries) wired under `/api/v1/catalog/`. Filters: `districts?region=`, `organizations?type=&region=`, `exercises?is_active=`, `batteries?age_category=&gender=` (returns the ordered 5 items). Reference lists are NOT region-scoped. Redis list caching skipped as a follow-up (noted in `api.py`). Verified: ruff, `check`, pytest.

DRF serializers + ViewSets for all catalog models. Filters: `districts?region=`, Filters: `districts?region=`,
`organizations?type=&region=`, `exercises?is_active=`,
`batteries?age_category=&gender=`. Read = any authenticated user; write gated to
`super_admin` (BCKND-13). Routes under `/api/v1/catalog/` per API.md §4.
Edge case: catalog is read-heavy and changes rarely → cache list responses (Redis)
and invalidate on write. Reference lists are NOT region-scoped (everyone sees all
regions/sports/exercises); only data entities (athletes/measurements) are scoped.
`GET /catalog/batteries/?age_category=&gender=` returns the ordered 5 exercises that
drive the entry form (B6).

# BCKND-22 — Django admin for catalog (TZ #16)
> ✅ **Done** (2026-07-07) — `catalog/admin.py` registers all 7 models with `list_display`/`search_fields`/`list_filter`; District inline under Region, BatteryItem inline (ordered) under TestBattery; filters on `Organization.type` and `Exercise.value_type`/`direction`. Verified: ruff, `check`.

Register Region, District, Organization, SportType, AgeCategory, Exercise,
TestBattery in Django admin with `list_display`, search, `list_filter`, and inlines
(District inline under Region; BatteryItem inline under TestBattery). Satisfies the
reference-data part of the TZ #16 admin panel.
Edge case: admin is for `super_admin` (`is_staff`/`is_superuser`) only and is
distinct from the SPA. The BatteryItem inline enforces the ordered 5-exercise
selection per `(age_category, gender)`. Useful filters: `Organization.type`,
`Exercise.value_type`/`direction`.

# BCKND-23 — Seed command: geography + TOIFA categories + sport types
> ✅ **Done** (2026-07-07) — idempotent `seed_catalog` (`get_or_create` by stable code/ordinal): 14 regions (real Uzbek names, proper apostrophes), 174 real tumanlar (representative, extendable subset per region), 6 TOIFA age categories (4:13–15 / 5:16–17 best-effort split — open item, easy to adjust), 32 sport types. Verified: ran twice against dev DB → +0 on second run; ruff, pytest idempotency test.

Idempotent `seed_catalog` management command (`get_or_create`): 14 regions
(Qoraqalpogʻiston, Toshkent city, 12 regions), their districts, the **6 TOIFA age
categories** (`1: 7–8 · 2: 9–10 · 3: 11–12 · 4/5: 13–17 (split TBC) · 6: 18–29`), and
the base sport types (30+: gandbol, futbol, boks, dzyudo, kurash, athletics, swimming,
badminton, voleybol, …).
Edge case: idempotent (`get_or_create` by stable `code`/`ordinal`) so re-running never
duplicates. Region/sport display `name`s are the real Uzbek values (proper nouns) even
though code/docs are English. The 13–17 → 4th/5th toifa split is an open item
(SCORING.md §11) — seed a best-effort split, easy to adjust.

# BCKND-24 — Seed command: exercise pool
> ✅ **Done** (2026-07-07) — idempotent `seed_exercises` (`get_or_create` by name): the 9 Exercise rows from SCORING.md §2 with correct unit/value_type/direction/order (30/100 m = seconds·lower, 400 m = minsec·lower, uzunlikka sakrash = count·higher, oldinga egilish = cm_signed·higher, argʻimchoq/push-ups/turnik = count·higher). TestBattery/BatteryItem rows deferred to `seed_physical` (BCKND-32). Verified: ran twice → +0 on second run; ruff, pytest.

Seed the ~9 `Exercise` rows (the pool) from SCORING.md §2 with correct
`unit`/`value_type`/`direction`/`order`: 30 m · 100 m · 400 m ga yugurish (lower);
turgan joydan uzunlikka sakrash · gimnastika oʻrindigʻida oldinga egilish (signed) ·
argʻimchoqda sakrash · yerga tayanib qoʻllarni bukish · skameykaga tayanib qoʻllarni
bukish · turnikda tortilish (higher). Idempotent.
Edge case: `direction` must match SCORING.md (running = lower_is_better; jumps / counts =
higher_is_better; flexibility is **signed cm**, higher_is_better). The **TestBattery/
BatteryItem rows** (which 5 per age×gender) are seeded together with the norm tables by
`seed_physical` (BCKND-32), since both derive from the same source tables. Idempotent by
exercise name/order.

# BCKND-25 — Catalog tests
> ✅ **Done** (2026-07-07) — `catalog/factories.py` (factory-boy for all models) + `catalog/tests/` (24 tests): model constraints (unique code/ordinal, unique district-per-region, unique battery-per-group), API read/write permissions (super_admin writes, coach/region_admin 403, coach/ministry read, unauth 401), filters (districts by region, organizations by type/region, exercises by is_active, batteries by age_category/gender → ordered items), seed idempotency + direction/value_type checks, and User per-role scope validation (region_admin without region → 400, coach without organization → 400). B3 closed. Verified: full suite 46 passed (22 pre-existing green), ruff, `check`, `makemigrations --check` clean.

pytest: model constraints (unique `code`, unique TOIFA `ordinal`, age-category
non-overlap), API read/write permissions (`super_admin` writes, others read-only,
`ministry` read), filters (batteries by `age_category`/`gender`, exercises),
`seed_catalog` + exercise-pool seed idempotency, and the User region/org field +
per-role validation (BCKND-20). Factories for catalog models.
Edge case: assert a non-`super_admin` gets `403` on catalog writes; running the
seed twice yields no duplicates; User scope validation rejects a `region_admin`
without a region. Once this task is finished, B3 is closed — then B4 (norms).

---

**BLOCK B4 — Norms** (BCKND-26 … BCKND-33) · dependency: BCKND-B3
Goal: all data-driven physical scoring criteria — Norm/NormBand models, the
numeric-age norm lookup, the total→daraja thresholds, admin, API, coverage
validation, and the `seed_physical` command that loads the ~24 client tables +
batteries. This is the data the scoring engine (B7) consumes; the engine itself is B7.

---

# BCKND-26 — Norm + NormBand models
> ✅ **Done** (2026-07-07) — `Norm` (exercise/age_min/age_max/gender/valid_from/is_active, unique version constraint) + `NormBand` (points 10/8/6, `[lower, upper)` DecimalField, signed OK) on TimeStampedModel; `assert_bands_no_overlap` in `catalog/validators.py`. Migration `0002`. Verified: create + overlap raises.

`Norm` (header): `exercise` FK, `age_min`, `age_max`, `gender`, `valid_from`,
`is_active`. **No sport_type, no block.** `NormBand` (line): `norm` FK,
`points` (10|8|6), `lower_bound`, `upper_bound`. Migration. Both on `TimeStampedModel`.
Edge case: NormBand bounds use the `[lower, upper)` convention (lower inclusive, upper
exclusive); `direction` is already baked into the ordering of bounds (SCORING.md §3.4).
For 7–17 a norm has `age_min = age_max = year`; for adults `age_min = 18, age_max = 29`.
On save validate the bands don't overlap. `valid_from` enables versioning (older
Evaluations stay reproducible). Bounds are numeric: time in **seconds** (mm:ss
converted), counts as integers, flexibility as **signed cm**.

# BCKND-27 — Norm lookup selector (get_norm)
> ✅ **Done** (2026-07-07) — `catalog/selectors.get_norm(exercise, gender, age, on_date)` — exact `age ∈ [age_min, age_max]`, latest `valid_from ≤ on_date`, no fallback → `None`. Verified: version-by-date, single-year vs 18–29 bucket, no-match → None.

A selector `get_norm(exercise, gender, age, on_date)`: match
`exercise + gender + age ∈ [age_min, age_max]`, among matches pick the latest
`valid_from <= on_date`. Returns a `Norm` or `None`. **No sport/block, no fallback** —
the lookup is exact (physical norms are sport- and block-independent).
Edge case: `age` is the athlete's age at the session date (numeric), not a category FK.
7–17 resolve to a single-year norm; 18–29 to the adult norm. No norm found → return
`None`; the caller marks that indicator `unscored` (SCORING.md §3.6). Version is chosen
by the session date, not "now", for reproducibility.

# BCKND-28 — DarajaThreshold model
> ✅ **Done** (2026-07-07) — `DarajaThreshold` (level I/II/III unique, total_min/total_max) in `0002`; color derives from the level in B7. Verified: 3 rows + ranges.

Model `DarajaThreshold` (`level` I|II|III, `total_min`, `total_max`) — the total→daraja
cut-offs as DATA, not hardcoded (SCORING.md §5). Defaults `I: 48–50 · II: 38–46 ·
III: 30–36 · <30: none`. Feeds B7's daraja resolver. (This slot previously held the
raw→score band-resolution, which is now the scoring domain's `points.py`, BCKND-44.)
Edge case: keep the cut-offs data-driven so the client can adjust without a code change.
`color` derives from the daraja (I→green, II→yellow, III/none→red). Confirm the thresholds
are constant across all tables (open item, SCORING.md §11). Validate the ranges don't overlap.

# BCKND-29 — Norm serializers + nested API
> ✅ **Done** (2026-07-07) — `catalog/serializers.py`: `NormBandSerializer` + writable-nested `NormSerializer` (exercise nested on read / PK on write) that atomically replaces the band set and maps a django `ValidationError` from `assert_bands_no_overlap` to a DRF 400. `catalog/api.py`: `NormViewSet` (`ReadOnlyOrSuperAdmin`, filter by exercise/age_min/age_max/gender) + read-only `DarajaThresholdViewSet`; routes `norms` + `daraja-thresholds`. Verified: super_admin create/update 201/200, overlap→400 (atomic rollback), coach write→403, filters, nested-band reads; ruff clean, `check` OK.

`NormSerializer` with writable nested `NormBand` (per API.md §4). `NormViewSet`:
list + filter (`?exercise=&age_min=&age_max=&gender=`), CRUD gated to `super_admin`
(`region_admin` read). `GET /catalog/norms/{id}/` returns the bands. A `DarajaThreshold`
read endpoint. Routes `/api/v1/catalog/norms/`.
Edge case: writable nested bands — creating/updating a norm replaces its band set
atomically (one transaction) and re-runs the overlap validation. Writes are
`super_admin` only. The SPA norm editor (F9) and results view (F6) consume these reads.

# BCKND-30 — Physical-norm coverage validation command
> ✅ **Done** (2026-07-07) — `catalog/management/commands/check_physical_norms.py` (read-only): iterates every `BatteryItem`, and for each single year of its battery's TOIFA `[age_min, age_max]` × gender calls `get_norm(on_date=today)`; reports each gap and `raise CommandError` (exit 1) if any. Verified by factory tests (full coverage→exit 0, one norm missing→CommandError, per-single-year gap detected) and a dev-DB smoke run (exit 0).

A `check_physical_norms` management command: for every `BatteryItem` exercise, assert a
`Norm` exists (active, current `valid_from`) covering each single year in the battery's
TOIFA `[age_min, age_max]` for that gender. Report gaps. Run after `seed_physical` and
before go-live.
Edge case: this pre-flights the "no norm for exercise × age × gender" case (SCORING.md §7)
so `finalize` never hits an unexpected `unscored` indicator in production. Read-only
(reports, never writes). A gap for any battery exercise means the physical form for that
group can't fully score.

# BCKND-31 — Django admin for norms + thresholds
> ✅ **Done** (2026-07-07) — `catalog/admin.py`: `NormAdmin` with a `NormBand` `TabularInline` (list_display exercise/gender/age_min/age_max/valid_from/is_active; list_filter exercise/gender/is_active) and `DarajaThresholdAdmin`. The inline's `BaseInlineFormSet.clean()` runs `assert_bands_no_overlap` on the submitted bands, surfacing overlaps as an inline form error. Verified: `manage.py check` 0 issues.

Register `Norm` (with `NormBand` inline) and `DarajaThreshold` in Django admin, with
`list_filter` by `exercise`/`gender`/`age`. This is the primary surface for "baholash
mezonlari" (TZ #16) — how the specialist edits the real numbers.
Edge case: the NormBand inline runs the overlap validation on save. `super_admin` only.
`DarajaThreshold` is editable so the client can adjust the 48/38/30 cut-offs.

# BCKND-32 — Seed command: seed_physical (norm tables + batteries + thresholds)
> ✅ **Done** (2026-07-07) — the 24 client tables were **parsed** (not hand-typed) into `backend/apps/catalog/data/physical_norms.json`; table→(age × gender) is deterministic (document order + exercise variant floor/pullup=male, bench=female), spot-checked against source + SCORING.md §9. `seed_physical` builds contiguous `[lower, upper)` bands, and seeds Norm/NormBand + TestBattery/BatteryItem + DarajaThreshold (48/38/30). Verified: +120 norms/+360 bands/+12 batteries/+60 items on run 1, **+0 on run 2** (idempotent); `check_physical_norms` passes; 14-yo male 100 m 14.4 → 8 pts (SCORING §9). 3 tests. **B4 Norms complete → B5 (athletes) next.** (TOIFA 4/5 split follows seed_catalog's best-effort; norms are per single year, independent of the split.)

Idempotent `seed_physical` command (SCORING.md §10): load the **~24 client tables**
(11 single years × 2 genders + 18–29 × 2 genders) from
`resources/Jismoniy tayyorgarlik mezonlari …` into `Norm`/`NormBand`, create the
`TestBattery`/`BatteryItem` rows (the ordered 5 per age×gender) from the same tables, and
the `DarajaThreshold` defaults (48/38/30).
Edge case: idempotent (`get_or_create`, keyed on exercise+age+gender+valid_from for norms,
age_category+gender for batteries). mm:ss table cells are normalized to seconds; signed
flexibility kept signed. Versioned by `valid_from` so re-seeding a new edition preserves old
Evaluation snapshots. Depends on the Exercise pool (BCKND-24).

# BCKND-33 — Norm lookup + band + threshold tests
> ✅ **Done** (2026-07-07) — `catalog/factories.py`: `NormFactory`/`NormBandFactory`/`DarajaThresholdFactory`. Tests: `test_bands.py` (pure overlap validation), `test_norms.py` (`get_norm` exact/adult-bucket 18&29/version-by-session-date/inactive→None, DarajaThreshold ordering+uniqueness, `check_physical_norms` coverage on factory data), `test_norm_api.py` (nested create 201, overlap 400 + atomic rollback, update replaces band set, coach write 403, exercise/gender filter, daraja read-only 405). Suite 46→66 green; ruff clean. NOTE: the `seed_physical` idempotency test is pending BCKND-32 (that command is not built yet).

pytest: `get_norm` (exact age match, single-year vs 18–29 bucket, version selection by
`valid_from`, no-norm → `None`), NormBand overlap validation, `DarajaThreshold` ranges, and
`seed_physical`/`check_physical_norms` idempotency + coverage. Pure-function tests need no DB.
Edge case: table-driven tests for band edges (exactly the lower bound, exactly the upper
bound); assert the adult 18–29 norm resolves for ages 18 and 29; version chosen by session
date. Once this task is finished, B4 is closed — then B5 (athletes).

---

**BLOCK D1 — Containerization** (DVPS-1 … DVPS-6) · dependency: BCKND-B1
Goal: the backend and its dev services (Postgres, Redis, web, worker, beat) run
under Docker Compose; `docker compose up` brings a healthy stack. Nginx, CI,
production deploy come later (D3/D4/D5).

---

# DVPS-1 — Backend Dockerfile
> ✅ **Done** (2026-07-07) — `deploy/Dockerfile`: multi-stage `python:3.12-slim`, deps in a venv, non-root `app` user, gunicorn CMD. Built & smoke-tested (354 MB; Django 5.2.15 importable; runs as `app`).

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
> ✅ **Done** (2026-07-07) — `.dockerignore` at the **repo root** (honoured for the repo-root build context; the task's `deploy/.dockerignore` is not auto-applied there — noted in-file). Excludes `.git`/venv/`__pycache__`/`.env`/media/static/frontend/docs/etc, keeping the context lean.

`deploy/.dockerignore`: exclude `.git`, `venv`/`.venv`, `__pycache__`, `*.pyc`,
`.env`, `media/`, `staticfiles/`, `node_modules`, `frontend/`, `.pytest_cache`.
Keeps the build context small and prevents artifacts/secrets entering the image.
Edge case: never copy `.env` into the image — secrets are injected at runtime via
compose `env_file`. Excluding it also avoids cache invalidation on local env edits.

# DVPS-3 — Compose: Postgres + Redis services
> ✅ **Done** (2026-07-07) — `deploy/docker-compose.yml`: `postgres:16` (named `pgdata` volume, `pg_isready` healthcheck) + `redis:7-alpine` (ping), ports published, project network. Verified: `up -d --wait` → both **healthy**; host venv connects (PostgreSQL 16.14 + Redis PING). Runtime: **colima** (Docker not installed → chosen this session). DVPS-4/5/6 (web/worker/beat/entrypoint) pending BCKND-6/8.

`deploy/docker-compose.yml`: `db` = `postgres:16` with named volume `pgdata`, env
`POSTGRES_DB/USER/PASSWORD` (from `.env`), healthcheck `pg_isready`; `redis` =
`redis:7-alpine` with a `redis-cli ping` healthcheck. Define a project network.
Compose reads `.env` (from BCKND-1's `.env.example`).
Edge case: give Postgres (`pg_isready`) and Redis (ping) healthchecks so app
services can `depends_on: condition: service_healthy` and not start against a cold
DB. Persist `pgdata` in a named volume so data survives container recreation.

# DVPS-4 — Compose: web (Django) service
> ✅ **Done** (2026-07-07) — `web` service: build from the Dockerfile, dev `runserver`, `../backend:/app` bind-mount for hot-reload, `:8000`, env overridden to the `db`/`redis` compose hosts, `depends_on` db+redis healthy, healthcheck → `/api/v1/health/`. Verified: container healthy; host `GET /health/` returns 200.

`web` service: build from the Dockerfile, `env_file: .env`, `depends_on` db+redis
(`service_healthy`), ports `8000:8000`. Dev `command` =
`python manage.py runserver 0.0.0.0:8000`; bind-mount `../backend:/app` for
hot-reload. `DJANGO_SETTINGS_MODULE=config.settings.dev`.
Edge case: in dev, bind-mount the source for hot-reload; in prod that mount is
removed and gunicorn is used (D5). Keep the dev `command` in compose, not baked
into the image, so prod can override.

# DVPS-5 — Compose: Celery worker + beat services
> ✅ **Done** (2026-07-07) — `worker` (`celery -A config worker`) + `beat` (`celery -A config beat`, single instance, `--schedule /tmp/celerybeat-schedule` since `/app` is a read-only mount for the non-root user), both reuse the web image, `depends_on` db+redis healthy. Verified: worker `celery@… ready`; beat PersistentScheduler started, stable.

`worker`: same image, `command: celery -A config worker -l info`, `depends_on`
redis+db, shares `env_file`. `beat`: `command: celery -A config beat -l info`
(default scheduler for now; `django-celery-beat` can be added when scheduled
rating recompute lands in B8/B12). Both reuse the web image (no separate build).
Edge case: worker and beat must wait for redis (broker) and db. Run exactly **one**
beat instance to avoid duplicate scheduled tasks.

# DVPS-6 — Entrypoint + stack bring-up verification
> ✅ **Done** (2026-07-07) — `deploy/entrypoint.sh` (wait-for-db → `migrate` → optional `collectstatic` (env-gated) → `exec`), COPYed to `/entrypoint.sh` (outside `/app` so the dev bind-mount doesn't hide it), used by `web`; its healthcheck hits `/api/v1/health/`. Verified end-to-end: `docker compose up --wait` brings db/redis/web/worker/beat to healthy and `/health/` returns 200. **D1 closed.**

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
Goal: the athlete registry — model, CRUD API with filters, derived TOIFA age
category, coach linking, and the first real exercise of the BCKND-14 scoping
framework (coach → own athletes is the trickiest scope).

---

# BCKND-34 — Athlete model
> ✅ **Done** (2026-07-07) — new app `apps/athletes`. `Athlete` model (last/first/middle name, `birth_year`, `gender`, region/district(null)/organization/sport_type FKs `PROTECT`, `coach` `SET_NULL` with `limit_choices_to` role=coach, razryad/training_experience/main_competitions, is_active). `block` property = `organization.type` (classification only). `clean()` validates district ∈ region. `birth_year` indexed (feeds the age_category filter). Migration `0001_initial` applied; `makemigrations --check` clean.

`apps/athletes`. `Athlete` (per DATA_MODEL): `last_name`, `first_name`,
`middle_name`, `birth_year`, `gender`, `region` FK, `district` FK, `organization`
FK, `sport_type` FK, `razryad`, `coach` FK→User, `training_experience`,
`main_competitions`, `is_active` (on TimeStampedModel). Migration. `block` is a
property read from `organization.type` (classification only).
Edge case: validate `coach` is a User with `role=coach`, and `district` belongs to
`region`. `age_category` (TOIFA) is NOT stored — derived at session time (BCKND-35).
`weight_category` is **deferred** (morpho) — not on the athlete (see DEFERRED).
**Open item:** `birth_year` vs `birth_date` — norms are per single year, so a full
`birth_date` gives the correct age at the session date; confirm precision with the client.

# BCKND-35 — Age-category (TOIFA) computation
> ✅ **Done** (2026-07-07) — `athletes/selectors.py`: `age_category_for(birth_year, on_date)` (age = `on_date.year − birth_year` → the matching TOIFA), `match_age_category(categories, age)` (the shared matching rule, so the list serializer maps from a cached TOIFA list — no N+1), and `age_at`. Raises `AgeOutOfRange` (with `.age`) when the age falls outside every category — never silently buckets. Verified against the seeded TOIFA: 7/8→ordinal 1, 18/29→ordinal 6, ages 6 & 30 raise.

A pure helper `age_category_for(birth_year, on_date)` (athletes domain): age =
`on_date.year - birth_year`, mapped to a TOIFA `AgeCategory` by `age_min`/`age_max`.
Used at session/evaluation time (it drives the `TestBattery` selection), not stored.
Edge case: the category depends on the measurement date (compute at session time).
Age above 29 or below 7 → flag as out-of-range, don't silently bucket it. The 13–17 →
4th/5th toifa split is the open item (SCORING.md §11).

# BCKND-36 — Athlete serializers + CRUD API + filters
> ✅ **Done** (2026-07-07) — `AthleteSerializer` (computed read-only `full_name`, `block`, `age_category` — best-effort at today's date, `null` when out of range; writable FKs; validates district∈region + coach role). `AthleteViewSet` CRUD at `/api/v1/athletes/`; `AthleteFilterSet` (region/district/organization/sport_type/gender/coach/is_active + `search` on names + `age_category` **translated to a birth_year range in SQL**, not per-row). Stub sub-routes `sessions`/`evaluations`/`recommendations` → `[]`, `latest-evaluation` → 204 (each `get_object()`-scoped; bodies land in B6/B7/B10). Delete is a soft `is_active=False`.

`AthleteSerializer` (+ computed `age_category`, `block`, `full_name`).
`AthleteViewSet` (CRUD). Filters: `region/district/organization/sport_type/gender/
age_category/coach/is_active/search`. Routes `/api/v1/athletes/`. Stub
sub-routes `/athletes/{id}/sessions/`, `/evaluations/`, `/latest-evaluation/`,
`/recommendations/` (filled by B6/B7/B10).
Edge case: the `age_category` filter is computed → translate it to a `birth_year`
range in the SQL query (don't compute per-row in Python at scale). `block` (from
`organization.type`) is a classification filter, not a scoring axis.

# BCKND-37 — Athlete scoping (wire BCKND-14)
> ✅ **Done** (2026-07-07) — `AthleteViewSet(ScopedQuerysetMixin)` with `scope_region_field`/`scope_organization_field`/`scope_coach_field` → super_admin/ministry all · region_admin by region · lab_operator by org · coach by `coach=self`. Object-level via the scoped `get_queryset` (out-of-scope pk → 404) + a defensive `has_object_permission`. `perform_create/update` `_guard_scope` (mirrors accounts `_guard_region_admin`): coach → forces `coach=self`, org must be own else 403; lab_operator → org must be own; region_admin → region/org must be in-region. `AthletePermission`: read for any authenticated, write for super_admin/region_admin/coach/lab_operator (ministry read-only). First real run of the BCKND-14 framework against `User.region`/`organization`.

Wire the BCKND-14 scoping framework to athletes — the canonical scoped entity:
`super_admin`/`ministry` → all; `region_admin` → by `region`; `coach` → `coach=self`;
`lab_operator` → by `organization`. Enforce in `get_queryset` AND object-level
(`has_object_permission`).
Edge case: an out-of-scope athlete fetched by ID must return `403/404`, not the
object. A `coach` creating an athlete is limited to their own organization. This is
where BCKND-14's framework first runs against real `User.region`/`organization`
fields (added in BCKND-20).

# BCKND-38 — Athlete tests + factory
> ✅ **Done** (2026-07-07) — `AthleteFactory` (org kept in the athlete's region) + **40 tests** across 5 files (test_models/age_category/filters/api/scoping): full_name/block/`clean()`; TOIFA boundaries (7/8/18/29, out-of-range raises); age_category→birth_year filter (both boundaries) + gender/is_active/coach filters; CRUD + computed fields + soft-delete + the 4 sub-route stubs; per-role visibility, out-of-scope detail/sub-route → 404, coach-create forces `coach=self`, org/region create guards → 403. Full suite **109 passed**, ruff clean, `makemigrations --check` clean. **B5 Athletes complete → B6 (measurements) next.**

pytest: CRUD, scoping per role (coach sees only own, region_admin only region),
TOIFA age-category derivation (boundaries, 18–29, out-of-range), filters, validation
(coach role, district ∈ region). `AthleteFactory`.
Edge case: scope-leakage tests (out-of-scope athlete by id → 403/404); age-boundary
tests at TOIFA edges. Once this task is finished, B5 is closed.

---

**BLOCK B6 — Measurements** (BCKND-39 … BCKND-42) · dependency: BCKND-B4, BCKND-B5
Goal: test sessions and raw measurements for the **physical battery**, manual entry
only (device integration is out of scope — ROADMAP), with a `finalize` action that
triggers scoring (B7).

---

# BCKND-39 — TestSession + Measurement models
> ✅ **Done** (2026-07-07) — new app `apps/measurements`. `TestSession` (athlete, date, entered_by PROTECT, source manual|excel, status draft|finalized + **snapshot dims** age_category/gender/region/organization/sport_type frozen at open + nullable height/weight) and `Measurement` (session, exercise, raw_value; unique per session×exercise). `import_batch` FK **deferred to B11** (ImportBatch not built yet); `source` distinguishes manual/excel meanwhile. No `block` snapshot (block-independent). Migration applied; `--check` clean.

`apps/measurements`. `TestSession` (`athlete` FK, `date`, `entered_by` FK→User,
`source` manual|excel, `import_batch` FK null, `status` draft|finalized) + **snapshot
dims** (`age_category`, `gender`, `region`, `organization`, `sport_type`) + optional
`height_cm`/`weight_kg` (nullable, future morpho). `Measurement` (`session` FK,
`exercise` FK, `raw_value`). Migration.
Edge case: the snapshot dims freeze where the athlete was at session time, so a later
transfer (BCKND-68) doesn't rewrite historical/period rankings. **No `block` snapshot** —
physical is block-independent (`Organization.type` stays classification only). `source`
defaults to `manual` (no device work). `height`/`weight` are nullable placeholders for
future morpho (BMI is deferred), not on the athlete. The period (quarter/half/year) is
derived from `date`.

# BCKND-40 — Session + battery-driven entry API
> ✅ **Done** (2026-07-07) — `TestSessionViewSet` CRUD (`ScopedQuerysetMixin` region/org/`athlete__coach`; **draft-only** mutation). `open_session` snapshots the athlete's dims + computes `age_category` at the session date (`AgeOutOfRange`→400). `GET /sessions/{id}/battery/` → the ordered 5 (reuses catalog `TestBatterySerializer`); no battery → 400. `POST /sessions/{id}/measurements/` bulk upsert with `parse_raw_value` per value_type (mm:ss→seconds, signed cm, non-negative counts / positive times; no magic bounds — thresholds are data). Scoped-create guard: a coach/operator/region_admin can only open a session for an in-scope athlete (else 403). `DataEntryOrReadOnly` **extracted to `common/permissions.py`** and adopted by athletes too (one source).

`TestSessionViewSet` (CRUD; only `draft` editable). The entry form is driven by the
athlete's battery: `GET /sessions/{id}/battery/` (or on session open) returns the ordered
5 exercises for the athlete's `(age_category, gender)`. `POST /sessions/{id}/measurements/`
bulk raw values keyed by `exercise`. Filter by athlete. Scoping (`lab_operator` → own org,
`coach` → own athletes). Validate `raw_value` per the `Exercise` `unit`/`value_type`.
Edge case: only `draft` sessions are editable; `finalized` are read-only. Validate by
`value_type`: `minsec` mm:ss → seconds, `cm_signed` allows negatives, counts are
non-negative integers, times are positive. Reject absurd values. `entered_by =
request.user`. Manual entry only. If the group's `TestBattery` is undefined, the form
can't open (admin must define it first — SCORING.md §7).

# BCKND-41 — finalize endpoint + scoring trigger
> ✅ **Done** (2026-07-07) — `POST /sessions/{id}/finalize/`: validates all 5 battery exercises present (missing → `400` + `missing` list; battery undefined → 400; already finalized → 400), transitions draft→finalized, returns the session. Per the roadmap the **scoring→Evaluation trigger is wired in B7/BCKND-46** ("Wire BCKND-41's finalize to call `evaluate_session`"); B6 does validation + transition only, so no B7 blocker.

`POST /sessions/{id}/finalize/`: validate that all **5 battery exercises** are present —
missing → `400` with the missing list — then trigger scoring (B7) → `Evaluation`, set
`status=finalized`, return the evaluation id. Scoring for a single athlete is computed
synchronously.
Edge case: finalize requires the complete 5-exercise battery for the athlete's group.
Idempotent: re-finalize recomputes/replaces the Evaluation. If any exercise has no matching
norm the indicator is `unscored` and finalize is blocked with an admin signal
(SCORING.md §7). The scoring logic itself is B7; this task wires the trigger + validation.

# BCKND-42 — Measurements tests
> ✅ **Done** (2026-07-07) — `TestSessionFactory`/`MeasurementFactory` + **57 tests** across 5 files (models/selectors/services/api/scoping): `parse_raw_value` matrix (mm:ss/seconds/count/signed-cm + error cases), `open_session` snapshot + AgeOutOfRange, `save_measurements`, `finalize_session`; session CRUD + snapshot dims, battery action (ordered 5), bulk entry (`"1:22"`→82.00), finalize success + missing→400, draft-only guards; per-role scoping, out-of-scope 404, scoped-create guard (coach foreign athlete→403). Full suite **166 passed**, ruff clean, `makemigrations --check` clean. **B6 Measurements complete → B7 (scoring engine ★) next.**

pytest: session CRUD, battery-driven entry (returns the correct 5 per age×gender), bulk
entry, validation (`value_type` ranges, mm:ss, signed flexibility, required 5), finalize
success + failure (missing exercises), scoping. Factories.
Edge case: finalize with an incomplete battery → `400`; draft vs finalized editability;
scope. Once this task is finished, B6 is closed (the engine is B7).

---

**BLOCK B7 — Scoring engine ★** (BCKND-43 … BCKND-48) · dependency: BCKND-B4, BCKND-B6
Goal: the pure **single-scheme** scoring domain — raw → points (10/8/6) via bands +
clamp, the battery resolver, the total → daraja mapping, the Evaluation snapshot, and
the recompute task. The heart of the system. (The OTM/OPSTTM two-strategy model is
parked — DEFERRED.)

---

# BCKND-43 — Evaluation + IndicatorScore models

> ✅ **Done** (2026-07-08) — new `apps/scoring`: `Evaluation` (session 1:1 CASCADE, athlete denorm PROTECT, snapshot dims `age_category`/`gender`/`region`/`sport_type`/`session_date`, `physical_total` 0–50, `daraja` I|II|III|none + `color` green|yellow|red as `TextChoices`, `ranking_score`=physical_total, explicit `computed_at`) + `IndicatorScore` (evaluation CASCADE, exercise PROTECT, raw_value, points; unique per exercise). Migration `0001` carries the **composite index** `eval_ranking_idx (region, sport_type, age_category, gender, ranking_score)`. `migrate` OK, `makemigrations --check` clean.

`apps/scoring`. `Evaluation` (`session` 1:1, `athlete` denorm, **denorm ranking dims**
`age_category`(snapshot)/`gender`/`region`/`sport_type`/`session_date`, `physical_total`
0–50, `daraja` I|II|III|none, `color` green|yellow|red, `ranking_score` (= physical_total),
`computed_at`). `IndicatorScore` (`evaluation` FK, `exercise` FK, `raw_value`, `points`).
Migration with a **composite index** on `(region, sport_type, age_category, gender,
ranking_score)` — no block.
Edge case: Evaluation is a snapshot (cheap, reproducible rating reads). `session` 1:1
unique. `ranking_score = physical_total`. Ranking dims are denormalized/snapshotted so
`RANK()` (B8) scans one indexed table without joining a possibly-transferred athlete;
`age_category` is the snapshot computed at `session_date`.

# BCKND-44 — points.py: raw → points (10/8/6) via bands + clamp

> ✅ **Done** (2026-07-08) — `scoring/domain/points.py resolve_points(norm, raw_value)`: half-open `[lower, upper)` containment, then **direction-agnostic clamp** — materialize+sort bands by `lower_bound` (required: `NormBand` default ordering is `-points`), `top = max(points)`; past an outer edge whose band is the top-points band → top, else → 0. Direction is inferred from which end the top band sits on (no `Exercise.direction` read). 10 unit tests: in-range, both boundaries, clamp high→10/low→0 for **both** directions, unsorted input, single-band, no-bands.

A pure function `resolve_points(norm, raw_value) → int` in `scoring/domain/points.py`:
find the `NormBand` whose `[lower, upper)` contains `raw_value` → its `points` (10/8/6);
clamp out-of-range per SCORING.md §3.5 — better than the best band → 10, worse than the
worst band → 0. No DB, fully unit-testable.
Edge case: `[lower, upper)` boundaries — no double-counting at band joins. The resolver is
direction-agnostic: `direction` is already baked into how the bands were entered
(SCORING.md §3.4). mm:ss values are normalized to seconds before comparison; signed
flexibility compared as signed cm. Below the worst → 0 (below norm, never an error); above
the best → 10.

# BCKND-45 — battery.py + daraja.py (domain resolvers)

> ✅ **Done** (2026-07-08) — `scoring/domain/battery.py battery_for(age_category, gender)` → ordered `Exercise`s (active `TestBattery`, prefetch `items__exercise`) or `None`; `scoring/domain/daraja.py daraja_for(total)` → `(level, color)` from `DarajaThreshold`, `("none","red")` below all (points ∈ {0,6,8,10} ⇒ even totals ⇒ 37/47 gaps unreachable). 6 tests: battery ordering, gender difference, undefined→None, inactive ignored; daraja full map incl. none.

`scoring/domain/battery.py`: `battery_for(age_category, gender)` → the ordered 5
`Exercise`s the athlete performs. `scoring/domain/daraja.py`: `daraja_for(physical_total)`
→ `(level, color)` via `DarajaThreshold` (I: 48–50 · II: 38–46 · III: 30–36 · <30: none;
color green/yellow/red). Pure, unit-testable.
Edge case: the battery differs by group — young (toifa 1–3): 30 m + argʻimchoq; older
(toifa 4–5): 100 m + 400 m; #4/#5 differ by gender (SCORING.md §2). daraja bounds come from
`DarajaThreshold` (data, B4), not hardcoded. `≥48` may flag "special-requirement direct" and
`=50` "gʻoliblik" as optional display flags derived from the total.

# BCKND-46 — Scoring service (orchestration) + finalize wiring

> ✅ **Done** (2026-07-08) — `scoring/services.evaluate_session(session)` `@transaction.atomic`: battery → per-exercise `get_norm`(pinned to session.date)+`resolve_points` → `IndicatorScore`; a missing norm → `ValidationError({"unscored":[...]})` (blocks finalize, never scored 0, SCORING §7); Σ → daraja/color; **idempotent** (deletes prior Evaluation, recreates) so re-finalize/recompute replace cleanly. Finalize wired in `measurements/api.py`: `finalize_session` + `evaluate_session` share **one `transaction.atomic()`** (crit — `ATOMIC_REQUESTS=False`; an unscored failure rolls status back to draft), returns **200** `{evaluation_id, status:"computed", physical_total, daraja, color, ranking_score, indicators}`. Athlete `evaluations`/`latest-evaluation` sub-routes populated. Decision: finalize is **200** (sync compute), not API.md's 202 (self-contradicting label). Rollback verified end-to-end (finalize-without-norms → 400 → session stays draft, no Evaluation).

`scoring/services.py` `evaluate_session(session)`: resolve the battery; for each
measurement → `get_norm` (B4) + `resolve_points` (BCKND-44) → `IndicatorScore`; Σ points →
`physical_total`; `daraja_for(total)` → daraja/color; write the `Evaluation` snapshot;
trigger recommendation generation (B10 hook). Wire BCKND-41's finalize to call this.
Edge case: an unscored indicator (no norm) is surfaced, not silently treated as 0 —
finalize is blocked (SCORING.md §7). Wrap Evaluation + IndicatorScores in one transaction.
Re-finalize replaces the prior Evaluation. `ranking_score = physical_total`.

# BCKND-47 — Recompute task (Celery)

> ✅ **Done** (2026-07-08) — `scoring/tasks.recompute_evaluations(filter_kwargs)` `@shared_task`: streams finalized `TestSession`s (`.iterator(chunk_size=200)`), re-`evaluate_session` each; a now-unscorable session is skipped (its prior Evaluation kept), not fatal — returns `{recomputed, skipped}`. `POST /evaluations/recompute/` (`scoring/api.RecomputeView`, **super_admin only**): the slice comes from an **allowlist** `RecomputeFilterSerializer` (region/sport_type/age_category/gender/date-range → primitive kwargs; raw `request.data` never hits `.filter()`) → `202 {task_id}`. Tests run Celery eager (Redis-free). Rating-cache invalidation (B8) left as a hook.

A Celery task `recompute_evaluations(filter)` for when norms change
(`POST /evaluations/recompute/`, API.md §14). Runs in the worker (D1). Pairs with
DVPS-7 for any scheduled/periodic recompute.
Edge case: recompute can be large — chunk it and run in the worker, never the web
process. The norm version is pinned by session date, so recompute uses the correct
historical norms. It invalidates the rating cache (B8) for the affected partitions.

# BCKND-48 — Scoring engine tests

> ✅ **Done** (2026-07-08) — **34 scoring tests** across `test_points`/`test_domain`/`test_services`/`test_api` + a shared `scenarios.py` (the §9 boy battery). Reproduces SCORING §9 **exactly** (14-yosh oʻgʻil 8+8+10+8+8 = **42 → II daraja 🟡**); band resolution + both clamp ends + both directions; battery per age×gender (boys turnik ↔ girls skameyka); daraja map incl. none; unscored→ValidationError (writes nothing); single-year vs 18–29 bucket; idempotent re-evaluate (replaces); recompute endpoint auth (super_admin 202 / others 403) + eager refresh; athlete evaluations/latest-evaluation. The B6 complete-battery finalize test was updated to seed norms (finalize now scores). Full suite **200 passed**, ruff clean, `makemigrations --check` clean. **B7 scoring engine complete → B8 (rating & ranking) next.**

pytest: band resolution (in-range, both `[lower, upper)` boundaries, clamp high→10 /
low→0); battery resolution per age×gender; the SCORING.md §9 worked examples exactly
(14-yosh oʻgʻil bola → total 42 → II daraja; the 7-yosh 30 m/argʻimchoq battery; the qiz
#5 = skameyka); total → daraja mapping; unscored handling; finalize → Evaluation end-to-end.
Edge case: reproduce the SCORING.md §9 worked examples exactly (42 → II daraja 🟡). Assert
the clamp behavior and the single-year vs 18–29 norm. Once this task is finished, B7 is closed.

---

**BLOCK B8 — Rating & Ranking** (BCKND-49 … BCKND-52 + DVPS-7) · dependency: BCKND-B7
Goal: rankings via Postgres `RANK()` over `(region, sport_type, age_category, gender)` —
**no block** — the "Top Athletes" feature, region ranking, and Redis caching +
invalidation. Needs Celery Beat (DVPS-7) for periodic refresh.

---

# BCKND-49 — Ranking selectors (RANK() over Evaluation)

> ✅ **Done** (2026-07-08) — `apps/rating/selectors.py`: `_latest_ids()` (Postgres `DISTINCT ON (athlete_id)` → latest Evaluation per athlete) as a subquery, then a separate windowed outer query (the two can't share one query). `ranked_athletes(filters, user)` = scope-filtered set + `Window(Rank(), partition_by=[region,sport_type,age_category,gender], order_by=ranking_score DESC)` → ties share rank; display order `rank, -session_date, last_name, first_name`. `top_athletes(...limit=10)`; `region_rating(...)` aggregates `Count(filter=Q(daraja="I"))` + `Avg(ranking_score)`, **ranked in Python** (window over GROUP BY is fragile). Scope applied *before* the window (region_admin correct, coach among own). Verified read-only SQL smoke on PG16 + tests.

Selectors using Postgres window functions: rank athletes within
`(region, sport_type, age_category, gender)` by `ranking_score DESC` — **no block** in
the partition (physical is block-independent; `sport_type` stays a partition/filter dim
from the athlete so "top athletes in a sport" is answerable). "Top athletes" (limit N);
region ranking (count of high-daraja per region + avg). Only the latest Evaluation per
athlete counts.
Edge case: ties share a rank (`RANK()`); secondary display order = latest evaluation date,
then name. The `age_category` filter → `birth_year` range. Historical evaluations are
excluded (latest per athlete only).

# BCKND-50 — Rating API (top / athletes / regions)

> ✅ **Done** (2026-07-08) — three views (matching the non-CRUD `APIView` convention of `RecomputeView`): `TopRatingView` (`{filters, results}` envelope, limit N), `AthletesRatingView(ListAPIView)` (paginated — LIMIT/OFFSET after the window keeps page-2 ranks continuous), `RegionsRatingView`. `RatingFilterSerializer` validates query params (region/sport_type/age_category PK + gender + limit; `age_category` = **direct snapshot FK**, not a birth_year range; `period_type` deferred to B12, unknown params ignored). Row shape per API.md §7 (`rank`, nested `athlete{id,full_name}`, `ranking_score`, `daraja`, `color`). `IsAuthenticated`; scoping enforced in the selectors. Mounted at `/api/v1/rating/`.

`apps/rating` endpoints per API.md §7: `GET /rating/top/`, `/rating/athletes/`,
`/rating/regions/`, with filters + scoping. Each row returns `rank`, `ranking_score`
(= physical_total), `daraja`, `color`.
Edge case: scoping applies (a `region_admin` sees only their region's ranking). Athletes
without an Evaluation are excluded. Filters: sport/region/age/gender (no block).

# BCKND-51 — Redis caching + invalidation

> ✅ **Done** (2026-07-08) — `apps/rating/cache.py`: `cached_response(endpoint, user, filters, build)` keyed `rating:{endpoint}:{scope_token}:{filters}:{gen}`. **Scope token is mandatory** (super/ministry→`all`, region_admin→`r{id}`, coach→`c{id}`, lab→`o{id}`) — without it two region_admins with identical filters would share a key and leak rankings (tested). Invalidation = a **global generation counter** bumped on any Evaluation write (never stale; TTL 300s backstop); persistent (`timeout=None`). Wired from `rating/apps.py ready()` via `post_save`/`post_delete` on `Evaluation` → `transaction.on_commit(bump_generation)` (rating→scoring; scoring stays unaware; recompute covered for free). All cache access is best-effort — a Redis outage can't break a write or a read. `top`/`regions` cached; `/athletes/` uncached (paginated, indexed). Cached values unwrapped to plain lists (DRF `ReturnList` isn't picklable).

Cache rating responses in Redis keyed by the normalized filter set; invalidate the
affected partition when a new Evaluation is computed (BCKND-46) or recompute runs
(BCKND-47). TTL as a safety net.
Edge case: invalidate on Evaluation write for the matching
`(region, sport, age, gender)` — no block — so rankings never go stale; TTL is only a
backstop.

# DVPS-7 — Celery Beat database scheduler (django-celery-beat) — needed by B8

> ✅ **Done** (2026-07-08) — `django-celery-beat~=2.9.0` added to requirements + installed into `backend/.venv`; `"django_celery_beat"` in THIRD_PARTY_APPS; `migrate` applied its tables (`--check` clean). Compose `beat` command → `--scheduler django_celery_beat.schedulers:DatabaseScheduler` (dropped the file `--schedule`), and `beat.depends_on` now also waits on `web` **healthy** so migrations run before the DatabaseScheduler needs its tables (else crash-loop). `docker compose config` valid. No `PeriodicTask` defined yet — pure scheduler infra (B8 invalidation is event-driven; periodic jobs land in B12).

Add `django-celery-beat` to requirements; add to INSTALLED_APPS; migrate; switch the
`beat` service command (from DVPS-5) to
`--scheduler django_celery_beat.schedulers:DatabaseScheduler` so periodic jobs
(rating cache refresh / scheduled recompute) are DB-backed and editable from Django
admin (`PeriodicTask`).
Edge case: this replaces the file-based beat schedule from DVPS-5. Exactly ONE beat
instance to avoid duplicate periodic runs. This is the cross-track task B8 (and later
B12) depend on.

# BCKND-52 — Rating tests

> ✅ **Done** (2026-07-08) — **18 tests** across `test_selectors`/`test_api`/`test_cache` + a `helpers.py` (partition-scoped Evaluation builder). Ranking desc + **tie-share-rank** + latest-per-athlete-only + top-N + independent partitions + region daraja-I counts/avg; endpoint shapes/filters/pagination + per-role scoping (region_admin sees own region) + bad-PK 400; cache hit (queryset.update bypasses the signal → stale-cached proves the hit), **invalidation on Evaluation write** (`django_capture_on_commit_callbacks` to fire the on_commit bump), scope-token isolation + cross-region leak prevention. Full suite **218 passed**, ruff clean, `makemigrations --check` clean, `docker compose config` valid. **B8 rating & ranking complete → B9 (comparison) next.**

pytest: ranking order (desc, ties), top-N, region ranking counts (by daraja), cache hit +
invalidation, scoping.
Edge case: invalidation test (a new Evaluation changes the cached top); tie-break
order. Once this task is finished, B8 is closed.

---

**BLOCK B9 — Comparison** (BCKND-53 … BCKND-54) · dependency: BCKND-B7
Goal: a side-by-side endpoint for 2–3 athletes (physical results).

---

# BCKND-53 — Comparison endpoint

> ✅ **Done** (2026-07-09) — thin `apps/comparison` (no model): `GET /comparison/?athletes=1,2,3` → `ComparisonView(APIView)` reads `scoring.selectors.latest_evaluation` per athlete → `{athletes:[{id, full_name, physical_total, ranking_score, daraja, color, indicators:[{exercise(name), raw_value, points}]}], leader}`. Validates 2–3 distinct ids (else 400); every id must be in the caller's scoped athlete set (`scope_queryset` region/org/coach) else **403** (missing/non-existent id counts as out-of-scope — no existence leak); no-evaluation athlete → no-data row (null totals, `[]` indicators), never the leader; `leader` = highest `physical_total`, request order breaks ties, null if none. Response preserves request order.

`GET /comparison/?athletes=1,2,3` → side-by-side: each athlete's latest Evaluation
(`physical_total`, `daraja`, `color`, per-exercise `IndicatorScore` points) plus the
`leader`. `apps/comparison` is thin — it reads the scoring selectors. Scoping applies.
Edge case: 2–3 athletes only (validate count); all must be in scope (else `403`);
athletes without an Evaluation are shown as no-data. Compare `physical_total` (0–50) and
per-exercise points; batteries differ by age×gender, so surface per-exercise where the
exercise matches.

# BCKND-54 — Comparison tests

> ✅ **Done** (2026-07-09) — **11 tests** (`apps/comparison/tests/test_api.py`): 2- and 3-athlete side-by-side, leader = highest total, no-data athlete (null totals + empty indicators, never leads), leader null when nobody's evaluated, count validation (<2 / >3 / non-integer → 400), out-of-scope athlete → 403, coach compares own athletes, non-existent id → 403, 401 unauth. Full suite **229 passed**, ruff clean, `makemigrations --check` clean (no model). **B9 comparison complete → B10 (recommendations) next.**

pytest: 2 and 3 athletes, leader detection (highest `physical_total`), scope enforcement,
missing-evaluation handling, count validation.
Edge case: `>3` or `<2` athletes → `400`; out-of-scope athlete → `403`. Once this
task is finished, B9 is closed.

---

**BLOCK B10 — Recommendations** (BCKND-55 … BCKND-57) · dependency: BCKND-B7
Goal: rule-based recommendations generated on `finalize`, with admin-managed rules.

---

# BCKND-55 — RecommendationRule + Recommendation models

> ✅ **Done** (2026-07-09) — new `apps/recommendations`: `RecommendationRule` (declarative condition — `exercise` FK PROTECT nullable [null → targets `physical_total`, set → that exercise's points], `comparator` lte/lt/gte/gt, `threshold`, `template_text`, `is_active`) + `Recommendation` (`evaluation` FK CASCADE, `rule` FK **SET_NULL** so an admin can delete an obsolete rule while the rec keeps its snapshotted `text`, `text`). Migration + Django admin (rules editable, recommendations read-only). `migrate` OK, `--check` clean.

`RecommendationRule` (`exercise` FK / category, `condition` (points/total threshold),
`template_text`, `is_active`). `Recommendation` (`evaluation` FK, `rule` FK, `text`,
`created_at`). Migration. Django admin for rules (TZ #16).
Edge case: rules are DATA (admin-editable), not hardcoded. `condition` is a simple
declarative shape (exercise/total, operator, threshold) — e.g. "turnikda tortilish
points ≤ 6" or "physical_total < 30". Keep it evaluable without code changes.

# BCKND-56 — Recommendation generation (on finalize)

> ✅ **Done** (2026-07-09) — `services.py`: pure `_rule_fires(rule, total, points_by_exercise)` (comparator map; exercise-not-in-battery → never fires) + `generate_recommendations(evaluation)` `@atomic` (clears old → `bulk_create` firing rules; idempotent). **Wired by signal** (`recommendations/apps.py ready()` connects `post_save` on `Evaluation`, **`created`-guard**, → `transaction.on_commit(generate for the new pk)`): on_commit runs when finalize's outer `atomic()` commits — *after* `IndicatorScore.bulk_create` and in-request before the response; scoring never imports recommendations. Entry point is **best-effort** (try/except + `logger.exception`) so a rule bug can't 500 a committed finalize; re-finalize/recompute regenerate (old eval CASCADEs its recs, new eval → fresh generation). API: `GET /athletes/{id}/recommendations/` (latest eval, un-paginated, select_related to avoid N+1) + `/recommendation-rules/` CRUD gated to **super_admin** (all methods; serializer `validate()` rejects threshold >10 exercise / >50 total).

A service `generate_recommendations(evaluation)`: evaluate active rules against the
evaluation's per-exercise points / `physical_total` and create `Recommendation` rows.
Hook into BCKND-46 (scoring service). Expose `GET /athletes/{id}/recommendations/`
(latest evaluation) + `/recommendation-rules/` CRUD (`super_admin`).
Edge case: regenerate on re-finalize (clear old, create new). Empty if nothing
matches. Rule evaluation is pure/declarative → unit-testable. Samples from SCORING.md §8
(turnikda tortilish ≤ 6 → strength low; physical_total < 30 → below badge norm).

# BCKND-57 — Recommendation tests

> ✅ **Done** (2026-07-09) — **20 tests** (`test_services` 11 + `test_api` 9). Pure `_rule_fires`: total below/at threshold (strict `lt` boundary), exercise `lte` **boundary fires at exactly 6**, above-threshold no-fire, exercise-absent skip, gte/gt; `generate_recommendations`: total/exercise rules fire + snapshot text, not-met/inactive → nothing, **regeneration idempotent** (no dupes). API: **finalize→recs via the signal** (`django_capture_on_commit_callbacks(execute=True)`), athlete recs sub-route + `[]` when no eval, rule CRUD super_admin full cycle, non-super (incl. GET) → 403, 401 unauth, threshold >10/>50 → 400. Full suite **249 passed**, ruff clean, `makemigrations --check` clean. **B10 recommendations complete → B11 (Excel import/export) next.**

pytest: rule matching (threshold met / not met on points/total), generation on finalize,
regeneration, rules CRUD permissions.
Edge case: a rule firing exactly at the threshold boundary; rules CRUD gated to
`super_admin`. Once this task is finished, B10 is closed.

---

**BLOCK B11 — Excel import/export** (BCKND-58 … BCKND-61 + DVPS-8) · dependency: BCKND-B5, BCKND-B6
Goal: bulk Excel upload pipeline for **physical** measurements (staging → validation →
commit) + template. Needs a shared media volume (DVPS-8).

---

# BCKND-58 — ImportBatch + ImportRow models + template download

> ✅ **Done** (2026-07-09) — in `apps/measurements` (commit creates measurements; a separate app would circular-dep). `ImportBatch` (uploaded_by, file, age_category+gender template group, date, status uploaded/validating/validated/failed/committed, row_count/error_count, `error` for file-level reason) + `ImportRow` (batch, row_number, raw_data JSON, status pending/valid/error, errors JSON, `athlete` matched, `created_session` set at commit). **Provenance is one-way** (`ImportRow.created_session`) — no `import_batch` FK on TestSession. `GET /imports/template/?age_category=&gender=` → openpyxl `.xlsx` (columns = identifying fields + the group's 5 battery exercises via `battery_for`; 400 if no battery). Admin registered.

`ImportBatch` (`uploaded_by`, `file`, `status`, `row_count`, `error_count`,
`created_at`). `ImportRow` (`batch` FK, `row_number`, `raw_data` json, `status`,
`errors` json). `GET /imports/template/?age_category=&gender=` → an Excel template
(openpyxl) with the group's 5 battery exercises as columns.
Edge case: template columns match the athlete-identifying fields + the 5 battery
exercises for the requested age×gender. The uploaded file is stored in MEDIA (needs the
DVPS-8 media volume).

# BCKND-59 — Import upload + async validation (Celery)

> ✅ **Done** (2026-07-09) — `POST /imports/` (multipart) → `ImportBatch(uploaded)` + `validate_import_batch` Celery task via `transaction.on_commit` (no worker race). Task (`tasks.py`): openpyxl `read_only,data_only` parse, header check, per-row `validate_row` (athlete **match-only** by natural key within uploader scope [0→not-found, >1→ambiguous]; age_category+gender reconciliation vs the group, catching `AgeOutOfRange`; all-5-present; `parse_raw_value` per value_type) → `ImportRow` valid/error; per-row errors don't fail the batch (only file-level → `failed`). **Idempotent** (clears prior rows on retry). **Security**: `.xlsx`-only + 5 MB cap (serializer) + 2000-row cap (task); openpyxl has no formula engine (no RCE) — `sanitize_cell` neutralizes text cells starting `= + - @` for the re-export vector; every cell re-validated server-side.

`POST /imports/` (multipart) → `ImportBatch` (status `uploaded`) + launch a Celery
task to parse + validate rows into `ImportRow` (`validated`/`error`).
`GET /imports/{id}/` → status + rows + errors. openpyxl parse.
Edge case: validation runs in the worker (large files); each row is validated
independently (athlete match, `value_type` ranges, all 5 battery exercises present);
errors are collected per row — the batch is not aborted on the first error. **Upload
security:** validate file type/extension + size limit + max row count; sanitize against
CSV/Excel formula injection (cells starting with `= + - @` neutralized); never trust
client-supplied values.

# BCKND-60 — Import commit

> ✅ **Done** (2026-07-09) — `POST /imports/{id}/commit/` → `commit_batch`: per valid row (own savepoint → **partial commit**) `open_session(source=excel)` → `save_measurements` → `finalize_session` → **`evaluate_session`** (there is **no** finalize signal — scoring is imperative, so commit calls it explicitly like the finalize action) → set `created_session`; skips error/already-committed rows. **Match-only** (user decision) — no athletes created; unmatched rows stay errors. Re-commit guard: `409 Conflict` if `status != validated`. `open_session` gained a `source=` kwarg.

`POST /imports/{id}/commit/` → create athletes/sessions/measurements from the
`validated` rows (skip `error` rows) in a transaction; status `committed`. Shares
the same validation/finalize rules as manual entry (the 5-exercise battery).
Edge case: only validated rows commit; partial commit is allowed (error rows skipped
+ reported). Guard against re-commit (don't double-insert).

# DVPS-8 — Media volume in compose — needed by B11/B12

> ✅ **Done** (2026-07-09) — named `media` volume declared and mounted `media:/app/media` (= `MEDIA_ROOT`) on **both** `web` and `worker` so uploaded imports (B11) + reports (B12) persist and are shared (`MEDIA_ROOT`/`MEDIA_URL` were already set). `beat` doesn't need it. `docker compose config` valid.

Add a named `media` volume mounted at MEDIA_ROOT on BOTH the `web` and `worker`
services (the worker writes/reads files, the web serves downloads). Ensures uploaded
imports (B11) and generated reports (B12) persist and are shared.
Edge case: web and worker MUST share the same media volume. For prod, large uploads
also need Nginx `client_max_body_size` (handled in D3). Persist across container
recreation.

# BCKND-61 — Import tests

> ✅ **Done** (2026-07-09) — **20 tests** across `test_import_template`/`test_import_upload`/`test_import_commit` + an `import_helpers.py` (in-memory `.xlsx` builder, battery/norm/athlete setup) + a `conftest.py` (tmp `MEDIA_ROOT`). Template header = ident + 5 battery names / 400 no battery / 401; upload → validation (matching row, mixed valid+error, **age×gender mismatch → error**), `.xlsx`-only + oversize reject, `sanitize_cell` formula-injection (parametrized), idempotent re-validate, uploader-only scoping (list + 404); commit creates session+measurements+**evaluation**, skips error rows, re-commit → 409, unmatched-only commits nothing. openpyxl-under-eager + `django_capture_on_commit_callbacks`. Full suite **269 passed**, ruff clean, `makemigrations --check` clean, `docker compose config` valid. **B11 Excel import/export complete → B12 (reports) next.**

pytest: template generation (per age×gender battery), upload → validation (valid + error
rows), commit (skips errors), permissions/scoping.
Edge case: a file with mixed valid/invalid rows → partial commit + error report;
re-commit guard. Once this task is finished, B11 is closed.

---

**BLOCK B12 — Reports** (BCKND-62 … BCKND-64 + DVPS-9) · dependency: BCKND-B8
Goal: async PDF/Word/Excel report generation for **physical** results with
status/download. Needs WeasyPrint system libs (DVPS-9) and the shared media volume (DVPS-8).

---

# BCKND-62 — Report model + request API

> ✅ **Done** (2026-07-09) — new `apps/reports`: `Report` (requested_by, type athlete|region|sport|republic, format pdf|word|excel, params JSON, status pending|processing|done|failed, file, error, completed_at) + read-only admin. `ReportViewSet`: `POST /reports/` → **202** + pending, **any authenticated** (matrix: Reports ✓ for all roles incl. ministry; read-generating), params **scoped server-side** (`assert_params_in_scope` → 403 for another region / out-of-scope athlete); `GET /reports/` + `/reports/{id}/` (own reports; super_admin/ministry all); `GET /reports/{id}/download/` → `FileResponse` when done, **409** otherwise. Enqueues `generate_report` via `on_commit`.

`Report` (`type` athlete|region|sport|republic, `format` pdf|word|excel,
`params` json, `requested_by`, `status` pending|processing|done|failed, `file`,
`created_at`, `completed_at`). `POST /reports/` → `202` + id; `GET /reports/`,
`/reports/{id}/`, `/reports/{id}/download/`. `apps/reports`.
Edge case: scope the `params` (a `region_admin` can only request their region).
Status lifecycle pending → processing → done|failed. Download only when `done`. Report
content is physical (physical_total, daraja, per-exercise points, rankings).

# BCKND-63 — Report generators (Excel/Word/PDF) + Celery task

> ✅ **Done** (2026-07-09) — **generic dataset + renderers** (not 4×3): `datasets.build_dataset` → a `ReportDataset(title, subtitle, columns, rows)` per type (athlete → latest Evaluation per-exercise table; region/sport → `ranked_athletes`; republic → `region_rating`), each **scoped to the requester**. `renderers.py`: `render_excel` (openpyxl), `render_word` (python-docx), `build_report_html` (pure, escaped) + `render_pdf` (**lazy** `import weasyprint` — Docker-only libs). `tasks.generate_report`: processing → build → render → `file.save(ContentFile)` → done; **any exception → failed + error + completed_at** (never left pending). Saved to the shared media volume (DVPS-8).

Celery task `generate_report(report_id)`: build the dataset (rating/scoring/athlete
selectors — physical), render to the chosen format — openpyxl (Excel), python-docx (Word),
WeasyPrint (PDF) — save to MEDIA, set status.
Edge case: runs in the worker (heavy); WeasyPrint needs system libs (DVPS-9); files
saved to the shared media volume (DVPS-8). On failure set `status=failed` + error;
never leave a report `pending` forever (timeout).

# DVPS-9 — WeasyPrint system libraries in backend image — needed by B12

> ✅ **Done** (2026-07-09) — Dockerfile **final stage** `apt-get install --no-install-recommends` `libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf-2.0-0 libcairo2 libffi8` + `fonts-dejavu` (Latin+Cyrillic Uzbek glyphs); apt lists cleaned. `requirements.txt` += `weasyprint~=66.0`, `python-docx~=1.2.0` (openpyxl already present). Package names verified to resolve in `python:3.12-slim` (bookworm). WeasyPrint is **lazy-imported** so the app + Excel/Word work locally without the libs; PDF render is Docker-only (the local PDF test skips on ImportError/OSError). Image rebuild deferred to CI/deploy (heavy).

Add WeasyPrint's native deps to the backend Dockerfile (apt): libcairo2,
libpango-1.0-0, libpangocairo-1.0-0, libgdk-pixbuf-2.0-0, libffi, plus a font
package for Uzbek glyphs. Add `weasyprint`, `openpyxl`, `python-docx` to
requirements.
Edge case: these libs grow the image — install only in the final stage and clean apt
lists. Without them WeasyPrint imports but fails at render. A font package is
required for non-Latin / Uzbek glyphs in PDFs.

# BCKND-64 — Report tests

> ✅ **Done** (2026-07-09) — **12 tests** (`test_reports.py`, tmp `MEDIA_ROOT` conftest): request→202+pending, ministry may request, excel athlete report generates + downloads (A1 = athlete name), word generates, region report lists the ranking, PDF **skipped when weasyprint/libs absent** (Docker-only), download-before-done → 409, region_admin→other region 403, athlete-out-of-scope 403, requester-only visibility (list 0 + detail 404), failed generation (monkeypatched build) → status=failed + error + completed_at. Full suite **280 passed, 1 skipped**, ruff clean, `makemigrations --check` clean, `docker compose config` valid. **B12 reports complete → B13 (audit & stats) next.**

pytest: request → `202`, status transitions, download when `done`, each format
generates, scoping on `params`.
Edge case: requesting a report outside scope → `403`; download before `done` →
`409`; a failed generation → `status=failed`. Once this task is finished, B12 is closed.

---

**BLOCK B13 — Audit & Stats** (BCKND-65 … BCKND-67) · dependency: BCKND-B2
Goal: an audit log of mutations and the role-scoped dashboard/stats endpoint.

---

# BCKND-65 — AuditLog model + signals

> ✅ **Done** (2026-07-09) — new `apps/audit`: append-only `AuditLog` (user SET_NULL, action, entity_type, entity_id, `changes` JSONField(DjangoJSONEncoder), ip, indexed created_at + composite indexes). **CRUX**: this API is JWT/DRF, so `request.user` is Anonymous at middleware time (DRF resolves it in the view) → `AuditContextMiddleware` binds the **request** (+ IP eagerly) in a `contextvars.ContextVar`, and `current_actor()` reads the user **lazily at signal-fire time**. Per-sender `pre_save`/`post_save`/`post_delete` on **Athlete, TestSession, User, Norm** (not Measurement/Evaluation — volume/derived); diff by `field.attname` (FK→`_id`), `password`/`last_login` never SELECTed; written synchronously in-transaction. IP from XFF gated behind `AUDIT_TRUST_X_FORWARDED_FOR` (prod-only). No recursion (AuditLog not audited; never `sender=None`).

`AuditLog` (`user`, `action`, `entity_type`, `entity_id`, `changes` json,
`created_at`, `ip`). Capture create/update/delete on key models (athletes,
measurements, evaluations, users, norms) via signals or a mixin.
Edge case: capture who/what/when + IP (from `X-Forwarded-For` behind Nginx). Log
mutations only, never reads. Don't recursively log AuditLog itself.

# BCKND-66 — Dashboard / stats endpoint

> ✅ **Done** (2026-07-09) — new `apps/stats` (no model): `GET /stats/overview/` → API §12 shape `{athletes_total, by_organization_type{OTM,OPSTTM}, by_daraja{I,II,III,none}, regions, recent_sessions}`, all **scoped** via `scope_queryset` (athletes region/org/coach; evaluations region/session__org/athlete__coach; sessions region/org/athlete__coach). `by_daraja` over latest-per-athlete (DISTINCT ON); `regions` = all for super_admin/ministry else distinct-in-scope; `recent_sessions` = last 30 days. `cache.get_or_set` keyed by a per-user **scope_token** (avoids cross-scope leakage), 60s TTL, best-effort.

`GET /stats/overview/` → role-scoped counts (`athletes_total`, `by_daraja`
(I/II/III/none), `by_region`, `by_sport`, `recent_sessions`) per API.md §12.
Edge case: numbers are limited to the user's scope (region/org). Use DB-side
aggregate queries and cache the result.

# BCKND-67 — Audit & stats tests

> ✅ **Done** (2026-07-09) — **14 tests**. Audit: create-snapshot + update-diff (changed-only) + off-request→user=None + `set_actor` unit path; **password/last_login never logged, is_staff IS**; not-self-audited; **actor+IP via the real middleware** (JWT force_authenticate + `HTTP_X_FORWARDED_FOR` under the trust flag — validates the lazy-user crux fix); `/audit/` super_admin-only + entity_type filter. Stats: region_admin scope isolation + `regions` distinct-in-scope; super_admin sees all regions; by_organization_type OTM/OPSTTM split; by_daraja latest-per-athlete incl. none; recent_sessions (cache cleared per test). Full suite **294 passed, 1 skipped**, ruff clean, `makemigrations --check` clean. **B13 audit & stats complete — backend B-blocks (B1–B13) done.**

pytest: audit entries on create/update/delete, IP capture, stats scoping +
correctness (by_daraja).
Edge case: stats respect scope (a `region_admin` sees only their region's counts);
audit captures the acting user. Once this task is finished, B13 is closed — all
BCKND blocks are now split.

---

**BLOCK D2 — Local dev environment** (DVPS-10 … DVPS-11) · dependency: DVPS-D1
Goal: a frictionless local workflow — a Makefile, a bootstrap script, seed targets,
and dev docs.

---

# DVPS-10 — Makefile + dev scripts

> ✅ **Done** (2026-07-09) — repo-root `Makefile` (self-documenting `make help`): `up`/`down`/`logs`/`ps`/`build`/`migrate`/`makemigrations`/`shell`/`seed`/`createsuperuser`/`psql` via `docker compose exec web` (+ `psql` via the db container's own `$POSTGRES_USER`/`$POSTGRES_DB`); `test`/`lint`/`format` via the local venv (dev tools aren't in the runtime image). `seed` = `seed_catalog` → `seed_exercises` → `seed_physical` (idempotent). `scripts/bootstrap.sh`: `.env` from template → build → `up --wait` (web's entrypoint migrates) → seed → `seed_admin`, all idempotent + re-runnable. Verified: `make help`/`ps`/`lint` run, compose targets dry-run well-formed, **`make test` → 294 passed**, `sh -n` clean. (Full `make bootstrap` is construction-verified — a real run builds the WeasyPrint image, deferred.)

`Makefile` targets wrapping `docker compose`: `up`, `down`, `logs`, `migrate`,
`makemigrations`, `shell`, `test`, `lint`, `format`, `seed`, `createsuperuser`,
`psql`. A `bootstrap` script: copy `.env.example`→`.env`, build, up, migrate, seed.
`seed` runs all idempotent seeders in order (catalog → exercises → `seed_physical`).
Edge case: targets run from the repo root; `seed` must be idempotent (re-runnable).
Document targets in the README.

# DVPS-11 — Dev docs + .env workflow

> ✅ **Done** (2026-07-09) — repo-root `README.md`: repo layout, prerequisites (Docker/colima on macOS; Python 3.12 for the non-container tooling), first-run (`make bootstrap`), the command table, the venv setup for `test`/`lint`/`format`, the settings split (base/dev/test/prod), and the `.env` workflow. `.env` is git-ignored (BCKND-1, confirmed); `.env.example` is the committed template — refreshed with `DJANGO_SUPERUSER_PASSWORD` (used by `seed_admin`), every key documented. Dev deps already declared in `backend/requirements-dev.txt`. **D2 local dev env complete.**

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

> ✅ **Done** (2026-07-09) — `deploy/nginx.conf`: `upstream web:8000`; `/api/` + `/admin/`
> proxied with `X-Forwarded-Proto $scheme` and **`X-Forwarded-For $remote_addr`** (overwrite,
> not `$proxy_add_...` — apps/audit reads the FIRST hop, so append would let a client spoof
> the audit IP); `/static/` (alias, `gzip_static`) + `/media/` (read-only, `nosniff`);
> `try_files $uri $uri/ /index.html` SPA fallback; `client_max_body_size 8m` (B11 5 MB +
> headroom); gzip; security headers with `proxy_hide_header` on the proxied locations so
> Django's copies don't duplicate. Verified: `nginx -t` (with a `web` host alias — `-t`
> resolves upstreams, so `--no-deps` alone fails on DNS, not syntax).

`deploy/nginx.conf`: serve the Vue SPA build (history-mode fallback), proxy `/api/`
and `/admin/` to gunicorn (`web`), serve `/static/` and `/media/`, gzip,
`client_max_body_size` for Excel imports (B11), security headers, and forward
`X-Forwarded-Proto`/`X-Forwarded-For`.
Edge case: SPA history fallback (`try_files $uri /index.html`);
`client_max_body_size` large enough for imports; `/media` served read-only; forward
`X-Forwarded-*` for `SECURE_PROXY_SSL_HEADER` (BCKND-2) and audit IP (BCKND-65).

# DVPS-13 — Nginx service + prod compose override

> ✅ **Done** (2026-07-09) — `deploy/docker-compose.prod.yml` overlay (`-f base -f prod`):
> `web` → gunicorn (3 workers), `DJANGO_SETTINGS_MODULE=config.settings.prod`,
> `COLLECTSTATIC=1`, `SECURE_SSL_REDIRECT=False` (HTTP-only until D5); `volumes: !override`
> drops the `../backend:/app` source mount (an additive override can't remove it — Compose
> 5.x supports the tag) and adds the `static` volume; `ports: !reset []`. `worker`/`beat`
> get prod settings too. `nginx` service (`nginx:1.27-alpine`, `depends_on web healthy`,
> `:80`, static/media/SPA mounts read-only). **`deploy/Dockerfile`**: `mkdir -p /app/{staticfiles,media}
> && chown app:app` before `USER app` — else the first-init named volume is root-owned and
> `collectstatic` fails for the non-root user. `prod.py`: HTTPS hardening gated behind
> `env.bool("SECURE_SSL_REDIRECT", default=True)` (redirect/cookies/HSTS follow it) so the
> pre-TLS profile doesn't 301-loop; `CSRF_TRUSTED_ORIGINS` env-added. `entrypoint.sh` already
> ran `collectstatic` on `COLLECTSTATIC=1` (unchanged). Makefile `prod-*` targets + README
> section. Verified: merged `compose config` (no source mount, gunicorn, no ports, prod
> settings on web/worker/beat, `static` volume), `nginx -t`, prod-settings import both flag
> paths, ruff clean, 294 passed, `makemigrations --check` clean. Full image build + live
> curl deferred (offered, ~mins — like D2). **D3 nginx + static complete → D4 (CI) next.**

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

> ✅ **Done** (2026-07-09) — `.github/workflows/ci.yml`, on push→main + all PRs.
> **`test`** job (Python 3.12, pip cached via `setup-python cache: pip`): `postgres:16` +
> `redis:7-alpine` service containers (health-gated, mirroring the compose stack) → `ruff
> check .` → `ruff format --check .` → `pytest -q`, run from `backend/` with
> `DATABASE_URL`/`REDIS_URL`/`SECRET_KEY` env (`REDIS_URL` needed at settings import even
> though tests use locmem). **`build`** job (parallel): `docker/build-push-action` on
> `deploy/Dockerfile` (context = repo root, no push) with `type=gha` layer cache to keep the
> WeasyPrint image fast on re-runs. `concurrency` cancels superseded runs; any lint/test/build
> failure fails the pipeline (default). **Prereq:** `ruff format --check` required a one-time
> `ruff format` of the backend (82 files, committed separately as `style:` — behaviour
> unchanged). Verified locally: `ruff check`/`ruff format --check` clean, 294 passed, workflow
> passes `actionlint` (exit 0), `docker build -f deploy/Dockerfile .` succeeds.
> **D4 CI pipeline complete → D5 (production deploy) next.**

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

> ✅ **Done** (2026-07-09) — `scripts/deploy.sh` (git pull → build → **one-shot migrate** in a
> throwaway container `run --rm -e MIGRATE_ON_START=0 -e COLLECTSTATIC=0 web … migrate` → `up -d`
> → prune) + `docs/DEPLOY.md` runbook (VPS provisioning, ufw 22/80/443, DNS, server `.env`
> chmod 600, seed, verify, ops, troubleshooting). `deploy/entrypoint.sh` gains a
> `MIGRATE_ON_START` gate (default "1" → dev/D3 self-migrate; prod web set to "0" so replicas
> can't race the schema). Worker sizing: `deploy/gunicorn.conf.py` (mounted, `gunicorn -c`) sizes
> to `(2*cores)+1`, `WEB_CONCURRENCY` override — dropping the hardcoded `--workers 3` alone would
> silently fall to 1 worker. **Security fix found:** the base compose published Postgres/Redis on
> the host; `prod.yml` now `!reset []`s `db.ports` + `redis.ports` (VPS would else expose the
> datastores). Secrets only in server `backend/.env` (git-ignored + `.dockerignore`d). Verified:
> 3-file `compose config` (datastore ports gone, `gunicorn -c /gunicorn.conf.py`, no `--workers`),
> entrypoint gate logic, `gunicorn.conf.py` cores-sizing + override, `sh -n`/shellcheck clean.

Provision the VPS (Docker + compose), deploy via the prod compose, manage
env/secrets on the server (not in the image/repo), size gunicorn workers, run a
one-shot `migrate` job before `web` starts, `collectstatic`. A deploy script/runbook.
Edge case: secrets live only on the server (`.env`, restrictive perms); `migrate`
runs as a dedicated one-shot job (avoid concurrent migrations across replicas);
gunicorn worker count tuned to cores.

# DVPS-16 — TLS (Let's Encrypt)

> ✅ **Done** (2026-07-09) — **certbot + webroot** (preserves the D3 hand-written nginx, not
> acme-companion). `deploy/nginx.tls.conf`: `:80` serves `/.well-known/acme-challenge/` (webroot)
> + 301→https for everything else; `:443 ssl` + `http2 on` (nginx 1.27 directive) apex server with
> the D3 app locations, TLS1.2/1.3 Mozilla-intermediate ciphers, no OCSP (LE retired it 2025), and
> **HSTS set at the nginx server level** (Django only covers `/api`+`/admin`; the SPA/static/media
> roots need it for preload) with `proxy_hide_header Strict-Transport-Security` on proxied
> locations; a `www→apex` 301 server. `deploy/docker-compose.tls.yml` (3rd overlay `-f base -f prod
> -f tls`): web `SECURE_SSL_REDIRECT=True` + `MIGRATE_ON_START=0`; nginx `!override` swaps to
> `nginx.tls.conf` + mounts `letsencrypt`/`certbot_www`, appends `:443`, 6h `nginx -s reload` loop;
> `certbot` service renew loop (12h). `scripts/init-letsencrypt.sh`: dummy self-signed cert → nginx
> up → certbot `certonly --webroot` (**STAGING=1 default** → 0), all one-shots via
> `run --rm --entrypoint …` (the service's entrypoint is the renew loop; `run` overrides command
> not entrypoint) → reload. `prod.py`: `SECURE_REDIRECT_EXEMPT=[r"^api/v1/health/$"]` so the
> internal healthcheck (no X-Forwarded-Proto) isn't 301-looped. Verified locally: `nginx -t` **and
> a real boot** (Up — proves `listen [::]:443` binds + `http2 on;`), redirect-exempt `Client` test
> (health 200, `/api/v1/` 301→https), `check --deploy` **zero security.* warnings**, ruff/format
> clean, 294 passed. Cert issuance + live handshake are runbook steps (no VPS/domain yet; SPA
> pending F-blocks → `/` 404). **D5 production deploy complete → D6 (backup & restore) next.**

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

> ✅ **Done** (2026-07-10) — **host cron + scripts** (chosen over Celery Beat: `pg_dump` runs in
> the db container so it matches the server v16 — a worker-side task would need postgresql-client-16
> in the image). `scripts/backup.sh`: `pg_dump -Fc` (custom format) via `compose exec -T db` +
> media volume tarred via a throwaway alpine, both streamed to host stdout; retention
> (`BACKUP_RETENTION_DAYS`, default 14, `find -mtime`); optional off-server `rsync` if
> `BACKUP_RSYNC_TARGET` set. `scripts/restore.sh <db-dump> [media-tgz]`: guarded (confirm / `FORCE=1`),
> `compose cp` the dump into the container → `pg_restore --clean --if-exists --no-owner`; `RESTORE_DB`
> overrides the target DB for the drill. `docs/BACKUP.md` runbook (cron line, off-server, restore,
> **restore drill**). `backups/` git-ignored. **Restore actually tested** locally: backed up the dev
> DB (62 migrations, 40 tables), restored into a throwaway `sport_restore_test` via the real script,
> verified 62 migrations / 40 tables, dropped the scratch DB — the live DB was never touched.
> Verified: `sh -n` + shellcheck clean (SC2016 on the in-container `sh -c` blocks disabled with
> intent), ruff/pytest unchanged (no Python touched). **D6 backup & restore complete → D7
> (monitoring & logging) next.**

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

> ✅ **Done** (2026-07-10) — health endpoint already returns 200/503 (BCKND-8, unchanged).
> Added a **worker** container healthcheck (`celery -A config inspect ping --timeout 10`);
> **beat** gets none (no control API + slim image has no ps) — its liveness is a `heartbeat`
> Celery task (`apps/common/tasks.py`, scheduled every 5 min via `CELERY_BEAT_SCHEDULE`) pinging
> a dead-man switch (`HEALTHCHECK_PING_URL`, opt-in). Bumped the web healthcheck interval 10s→30s
> (each probe logs). **`restart: unless-stopped`** on all 6 prod services (a single VPS has no
> orchestrator to reschedule a crash). `scripts/disk-alert.sh` (df threshold → opt-in Telegram,
> else non-zero for cron-mail). `docs/MONITORING.md` runbook wires an external uptime monitor +
> resource monitoring + alert routing. Verified: merged compose config (worker healthcheck,
> restart×6, 30s interval), `sh -n`/shellcheck clean.

Wire `/api/v1/health/` (BCKND-8) to an uptime monitor and container healthchecks
(partly from D1). Alert on down. Basic resource monitoring (CPU/mem/disk).
Edge case: the health endpoint returns `503` when db/cache are down (BCKND-8) so the
monitor/LB reacts; route alerts (email/Telegram).

# DVPS-19 — Centralized logging + error tracking

> ✅ **Done** (2026-07-10) — structured Django `LOGGING` (base): one console handler on `root`
> → stdout, plain in dev / **JSON in prod** (a ~12-line stdlib `JsonFormatter`, no new dep);
> `django.db.backends`=WARNING so SQL/params never log. **Request-id correlation**:
> `apps/common/middleware.py` `RequestIDMiddleware` (registered FIRST) sanitizes/generates an
> `X-Request-ID`, echoes it, and stores it in a `ContextVar` (mirrors `apps/audit/context.py`); a
> `RequestIDFilter` on the handler stamps every line; `task_prerun/postrun` signals reuse the same
> id for worker logs. **`CELERY_WORKER_HIJACK_ROOT_LOGGER=False`** — else the worker replaces the
> dictConfig at boot. **Sentry** (`sentry-sdk~=2.20`) init in prod.py, opt-in via `SENTRY_DSN`
> (inert otherwise), Django+Celery integrations, `send_default_pii=False` **and
> `max_request_body_size="never"`** (the latter is what actually stops login-body/password capture).
> Docker **log rotation** via a `json-file` anchor (10 MB×5) on web/worker/beat. `.env.example` +
> `docs/MONITORING.md`. Verified: `manage.py check` dev+prod, dictConfig valid, **301 passed** (+7
> request-id/filter/JSON tests: generated/echoed/sanitized/truncated), Sentry init with a dummy DSN
> doesn't raise, ruff/format clean. **D7 monitoring & logging complete — DVPS track split; F-blocks
> (frontend) next.**

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

> ✅ **Done** (2026-07-10) — `frontend/` scaffolded: Vite 6 + Vue 3.5 (`<script setup>`) +
> **TypeScript** (confirmed) + Vue Router + Pinia + ESLint 9 (flat config) + Prettier. Folders
> views/components/stores/api/router/composables/constants/types/assets. Vite dev proxy `/api` →
> `http://localhost:8000` (override with `VITE_API_TARGET`). Verified: `eslint` + `vue-tsc --noEmit`
> + `vite build` all clean (247 modules, code-split).

Create `frontend/` with Vite + Vue 3 (`<script setup>`), Vue Router, Pinia, ESLint +
Prettier. Folder structure: `views`, `components`, `stores`, `api`, `router`,
`composables`, `assets`. Vite dev proxy `/api` → backend.
Edge case: ESLint + Prettier from day one to match backend cleanliness. **Decision
to confirm: TypeScript vs plain JS** — TS recommended for maintainability. Dev proxy
avoids CORS locally.

# FRNTND-2 — API client (axios) + interceptors

> ✅ **Done** (2026-07-10) — `src/api/client.ts`: axios `baseURL=/api/v1`; request interceptor
> attaches the access token; response interceptor refreshes on 401 with a **single-flight lock**
> (concurrent 401s await one refresh) via a bare axios instance (no recursion) then retries; on
> refresh failure clears tokens + redirects to /login. `toMessage()` maps errors to Uzbek (API.md
> §1: `detail` / DRF field errors / status fallback). Tokens live in `src/api/tokens.ts`
> (localStorage) — one source both the interceptor and the store read, so no import cycle.

An axios instance (`baseURL=/api/v1`): request interceptor attaches the access
token; response interceptor on `401` refreshes the token and retries, and on refresh
failure logs out. Centralized error mapping to Uzbek messages (API.md §1 format).
Edge case: single-flight refresh lock (no parallel refresh storms); on refresh
failure clear auth + redirect to login.

# FRNTND-3 — Auth store (Pinia)

> ✅ **Done** (2026-07-10) — `src/stores/auth.ts` (Pinia setup store): `login` (POST /auth/login →
> the backend returns tokens **+ the user profile in one response**, so no extra /me), `logout`
> (best-effort refresh blacklist + clear), `restore` (validate the stored session via /me on app
> load; the interceptor transparently refreshes an expired access token), getters
> `isAuthenticated`/`role`. Session restored before mount in `main.ts` so guards see auth on first paint.

`auth` store: `login` (POST `/auth/login` → store tokens + user), `logout`
(blacklist refresh + clear), `me`, token persistence (localStorage), `isAuthenticated`
and `role` getters. Restore the session on app load via `/me`.
Edge case: expose `role` for guards/menu; restore + validate session on reload;
accept the localStorage tradeoff for tokens.

# FRNTND-4 — UI kit + base layout primitives

> ✅ **Done** (2026-07-10) — **PrimeVue 4** (confirmed) with the Aura preset via `@primeuix/themes`
> (NOT the deprecated `@primevue/themes`) + primeicons + ToastService; dark-mode selector `.dark`.
> `src/constants/labels.ts` = the English-enum → Uzbek-label map (roles; daraja I/II/III + Tag
> severities green/amber/red); base primitives `DarajaBadge`, `PageHeader`; responsive base CSS
> using PrimeVue design tokens. Uzbek-facing per CLAUDE.md §4.
> **F1 frontend foundation complete → F2 (auth & layout) next.**

Configure a UI library (PrimeVue or Naive UI), base components (button, table, form
inputs, modal, toast), theme, and the **English-enum → Uzbek-label** map (daraja,
colors) so the UI reads in Uzbek. Responsive base (TZ #15 "mobile-friendly").
Edge case: pick ONE UI kit and stick to it. The product UI is Uzbek-facing — this is
where English enum keys (daraja I/II/III, green/yellow/red) map to Uzbek display labels.

---

**BLOCK F2 — Auth & layout** (FRNTND-5 … FRNTND-7) · dependency: BCKND-B2, FRNTND-F1
Goal: login, route guards, and the role-aware app shell.

---

# FRNTND-5 — Login page

> ✅ **Done** (2026-07-10) — `LoginView.vue`: username/password with inline required-field
> validation, submit disabled while pending (`loading`), server errors shown in Uzbek via Toast
> (`toMessage`), **"remember me"** (localStorage vs sessionStorage via `tokens.ts` startSession),
> and redirect to `?redirect=` after login. Card visual matching the landing.

Login view (username/password, validation, error display, "remember me") wired to
the auth store. Visual language consistent with the existing landing.
Edge case: show server errors (invalid credentials) in Uzbek; disable submit while
pending; redirect to the intended route after login.

# FRNTND-6 — Route guards + role-based routing

> ✅ **Done** (2026-07-10) — `router.beforeEach`: unauth on a `requiresAuth` route → login with
> `?redirect=` (destination preserved); an authed user hitting `/login` → home; a route with
> `meta.roles` and the wrong role → `/403` (`ForbiddenView`). `meta.requiresAuth` on the `/` parent
> is inherited by children. User management (`/users`) is gated to `super_admin`/`region_admin`.

Router guards: require auth for app routes (redirect to login otherwise); role-based
route access (e.g. user management only for super_admin/region_admin); per-role
landing.
Edge case: guard runs before each navigation; an unauthorized role → 403 view;
preserve the intended destination through login.

# FRNTND-7 — App shell (navbar/sidebar) + role-based menu

> ✅ **Done** (2026-07-10) — `layouts/AppLayout.vue` = the authenticated shell: sticky top navbar
> (brand, scope chip = org/region, user dropdown via PrimeVue Menu with role label + logout),
> sidebar with a **role-filtered menu** (`config/navigation.ts` → `visibleNav(role)`), active-link
> highlighting (exact for home, prefix for sections). Responsive: sidebar collapses to a PrimeVue
> Drawer under 768px (hamburger). App routes render as its children; section routes are placeholders
> until their F-block. **F2 auth & layout complete → F3 (catalog UI) next.**

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

> ✅ **Done** (2026-07-10) — `stores/catalog.ts` caches the small global lists (regions, sport
> types, age categories, exercises) once per session via `ensureLoaded()`; districts fetched +
> memoized per region (cascade). `api/catalog.ts` + `types/catalog.ts`. Reusable pickers in
> `components/pickers/`: `RegionSelect`, `DistrictSelect` (cascade on region), `OrganizationSelect`
> (fetched by region), `SportSelect`, `AgeCategorySelect`, `GenderSelect`, `ExerciseSelect` — all
> `defineModel` + PrimeVue Select, reused by F4 forms / F7 filters. `CatalogView.vue` = tabbed
> browse (Tabs + DataTable) of the reference data with Uzbek enum labels (extended `labels.ts`:
> gender, org type, value_type, direction). Verified: eslint + vue-tsc + build clean.

Read views for reference data (regions, sport types, TOIFA age categories, exercises,
batteries) and reusable select components (region/district cascade, sport picker, etc.)
used across forms and filters. Cache catalog in a Pinia store.
Edge case: catalog rarely changes → cache it; the reusable pickers are shared by
athlete forms (F4) and rating filters (F7).

# FRNTND-9 — Norms & catalog management (super_admin)

> ✅ **Done** (2026-07-10) — `views/catalog/NormsView.vue` (route `/catalog/norms`, **super_admin**
> gated + linked from the catalog view for that role): norm list (DataTable, filter by
> exercise/gender), create/edit Dialog with the **band editor** (fixed 10/8/6-point rows,
> lower/upper `[l, u)` inputs, null = ±∞) that enforces **non-overlapping bands client-side**
> (`utils/normBands.ts` mirrors BCKND-26), and delete via ConfirmDialog. `DarajaThreshold` shown
> **read-only** (the API is read-only — admin-edited; noted in the UI). `ConfirmationService` +
> `<ConfirmDialog>` wired app-wide. Verified: eslint + vue-tsc + build clean.
> **F3 catalog UI complete → F4 (athletes UI) next.**

Admin UI the SPA owns: a Norm + bands editor (`NormBand` 10/8/6 rows) and the
`DarajaThreshold` editor, plus any catalog CRUD not left to Django admin. Gated to
super_admin.
Edge case: the band editor enforces non-overlapping `[lower, upper)` bands client-side
(mirror BCKND-26); super_admin only; pure reference CRUD can stay in Django admin if simpler.

---

**BLOCK F4 — Athletes UI** (FRNTND-10 … FRNTND-12) · dependency: BCKND-B5
Goal: athlete list, card, and create/edit form.

---

# FRNTND-10 — Athlete list + filters

> ✅ **Done** (2026-07-10) — `views/athletes/AthletesView.vue`: PrimeVue DataTable in **lazy**
> mode (server pagination — `page`/`ordering` query params), filter bar (Region/Sport/Gender/
> AgeCategory pickers + **debounced** name search, all → API.md §5 query params, scope enforced
> server-side), sortable columns, loading/empty states, row → card. Names resolved via the cached
> catalog store. `api/athletes.ts` (strips null filters) + `types/athlete.ts`.

A paginated athlete table with filters
(region/district/org/sport/gender/age/coach/search); the server enforces
scope. Row → athlete card.
Edge case: filters map to query params (API.md §5); don't duplicate scope logic
client-side; debounce search; loading/empty states.

# FRNTND-11 — Athlete card page

> ✅ **Done** (2026-07-10) — `views/athletes/AthleteCardView.vue`: tabbed detail — personal data
> (FKs resolved to names), the **derived TOIFA age category + block** as badges, and a comparison
> link. `birth_year` (no BMI, per spec). The Sessiyalar / Baholash / Tavsiyalar tabs show no-data
> states now and are wired when their APIs land (F5 sessions, F6 evaluation, F9 recommendations).

Athlete detail: personal data, derived TOIFA age category + block, session history,
latest evaluation summary (physical_total + daraja + color), recommendations, and a
link to comparison. Tabbed.
Edge case: handle athletes with no evaluation yet (no-data states); show the derived
TOIFA + block; BMI is deferred (not shown).

# FRNTND-12 — Athlete create/edit form

> ✅ **Done** (2026-07-10) — `views/athletes/AthleteFormView.vue` (routes `/athletes/new` +
> `/athletes/:id/edit`, **gated to DATA_ENTRY_ROLES** via `utils/permissions.ts` — matches backend
> `DATA_ENTRY_ROLES`; ministry can't reach it). All reference pickers incl. **region→district
> cascade** + org + sport + `CoachSelect` (scoped `/users?role=coach`). Client validation (required
> fields) mirrors the server; district∈region enforced by the cascade; the coach-role rule +
> scope are enforced server-side and surfaced via `toMessage`. No weight-category (deferred).
> **F4 athletes UI complete → F5 (measurements UI) next.**

Form with reference pickers (region→district cascade, org, sport, coach),
validation, role-gated writes.
Edge case: district depends on region (cascade); client validation mirrors the
server (coach role, district ∈ region); only write-allowed roles see the form. No
weight-category picker (deferred).

---

**BLOCK F5 — Measurements UI** (FRNTND-13 … FRNTND-15) · dependency: BCKND-B6, BCKND-B11
Goal: the physical battery entry form, finalize, and the Excel import UI.

---

# FRNTND-13 — Session + battery entry

> ✅ **Done** (2026-07-10) — `MeasurementsView.vue` (hub: recent sessions + new-session dialog
> with `AthleteAutocomplete` + date) → `SessionView.vue`. The entry form is **data-driven from
> `GET /sessions/{id}/battery/`** (BCKND-40) — one input per battery exercise, placeholder +
> **client validation per `value_type`** (`utils/rawValue.ts`: mm:ss / seconds / count / signed cm)
> + height/weight; save draft via `POST …/measurements/` + PATCH session. If the battery is
> undefined → "admin must configure" message. Raw values are strings (backend parses).

Create a session (date; optional height/weight placeholders) and enter raw values via a
form **generated from the athlete's `TestBattery`** — the 5 age×gender-specific exercises,
each rendered per its `value_type` (mm:ss for times, signed cm for flexibility, integer
counts); save as draft.
Edge case: the form is data-driven from the battery endpoint (BCKND-40) — 5 inputs, not a
fixed set; validate ranges/format client-side per `value_type`; only draft is editable; if
the group's battery is undefined, show an "admin must configure" message.

# FRNTND-14 — Finalize + result display

> ✅ **Done** (2026-07-10) — "Yakunlash" → `POST …/finalize/` (persists the draft first). On
> success shows the server-computed evaluation inline: `physical_total` (0–50), `DarajaBadge`
> (daraja I/II/III/none + color), and the per-exercise `points` (10/8/6) table — **no client
> scoring**. The missing-exercises `400` surfaces via `toMessage` (the backend names them).
> Finalized → read-only. NOTE: a *reloaded* finalized session can't re-display its evaluation —
> there is **no GET evaluations endpoint** (scoring exposes only `/evaluations/recompute/`); it
> points to the Results section (F6), which is **blocked** on that missing backend endpoint.

Finalize action (server validates the 5 required exercises); on success show the computed
evaluation — `physical_total` (0–50), `daraja` (I/II/III/none), `color`, and per-exercise
`points` (10/8/6). Handle the missing-exercises `400`.
Edge case: show which battery exercises are missing on `400`; finalized → read-only; show
the daraja color indicator immediately; scoring is server-computed (no client scoring).

# FRNTND-15 — Excel import UI

> ✅ **Done** (2026-07-10) — `ImportView.vue`: **template download** per group
> (`GET /imports/template/?age_category&gender` → blob), **upload** (`POST /imports/` multipart:
> file + age_category + gender + date), then **polls `GET /imports/{id}/`** every 1.5s while
> `validating` → shows `row_count`/`error_count` + a per-row errors table; `validated` → **commit**
> button (`POST …/commit/`, partial commit allowed); `failed` → the file-level error; `committed`
> → success. `api/imports.ts`. Route gated to `DATA_ENTRY_ROLES`. **F5 measurements UI complete →
> F6 (results UI) — BLOCKED on a missing GET-evaluations backend endpoint (see FRNTND-14 note).**

Template download (per age×gender battery), upload, per-row validation progress/errors,
commit of valid rows; polls `/imports/{id}`.
Edge case: show per-row errors; allow partial commit; poll async status; large-file
upload feedback.

---

**BLOCK F6 — Results UI** (FRNTND-16 … FRNTND-17) · dependency: BCKND-B7
Goal: the physical evaluation result view and history/trend.

---

# FRNTND-16 — Evaluation result view

> ✅ **Done** (2026-07-10) — **Unblocked by adding `GET /evaluations/`** (scoped read viewset +
> tests, commit `562e9dd`). `components/EvaluationPanel.vue`: the latest evaluation's
> `physical_total` (/50), `DarajaBadge` (I/II/III/**none**=Nishonsiz, color-coded), and the
> per-exercise raw→`points` (10/8/6) table — server-computed, no client scoring. Wired into the
> athlete card's Baholash tab; the finalized SessionView now re-fetches its evaluation on reload
> (`?session=`). BMI deferred.

Detailed evaluation: the 5 per-exercise scores (raw value → 10/8/6 points),
`physical_total`, `daraja` + `color`, and recommendations. Uzbek daraja labels;
color-coded.
Edge case: render the 5 battery exercises with their raw values and points; show the total,
the daraja badge and color; BMI / other categories are deferred (not shown).

# FRNTND-17 — Evaluation history + trend

> ✅ **Done** (2026-07-10) — same `EvaluationPanel.vue`: a **trend line chart** (PrimeVue Chart /
> chart.js) of `physical_total` over `session_date` (shown only for 2+ points; y-axis 0–50) + a
> paginated history table (date / ball / DarajaBadge). Fetches `GET /evaluations/?athlete=&ordering=-session_date`.
> The athlete card also gained a Sessiyalar tab (session list → session view). **F6 results UI
> complete → F7 (rating UI) next.**

An athlete's evaluations over time (table + a simple trend chart of `ranking_score`
(= physical_total), and the daraja per date).
Edge case: the chart handles 1 vs many points; this is the coach's monitoring view
(progress over time).

---

**BLOCK F7 — Rating UI** (FRNTND-18 … FRNTND-19) · dependency: BCKND-B8
Goal: the rating table, the headline "Top Athletes" feature, and region ranking.

---

# FRNTND-18 — Rating table + Top Athletes

> ✅ **Done** (2026-07-10) — `views/rating/RatingView.vue`: a shared filter bar
> (region/sport/age/gender — no block) driving three tabs. **Top sportchilar** is the
> headline feature (`components/rating/TopAthletes.vue`) — a gold/silver/bronze podium list
> from `GET /rating/top/` (limit 10), each row clickable to the athlete card. **Toʻliq
> reyting** = a lazy-paginated ranked table from `GET /rating/athletes/` (rank/F.I.O/ball/
> daraja via `DarajaBadge`). `api/rating.ts` wraps the three endpoints; scope is enforced
> server-side (BCKND-49), the client only passes filters. Tabs refetch only when stale for
> the current filters (a `loaded` flag). Verified: eslint + vue-tsc + build clean.

Rating views: filters (sport/region/age/gender — no block), a ranked table
(rank/score/**daraja**/color), with "Top Athletes" prominent — the headline feature (TZ).
Edge case: the "Top Athletes" filter set (sport+region+age+gender) is the headline
feature; daraja color indicators; scoped by role.

# FRNTND-19 — Region ranking view

> ✅ **Done** (2026-07-10) — the **Viloyatlar** tab in `RatingView.vue`: a region table
> (rank / viloyat / I-daraja count / average `ranking_score`) from `GET /rating/regions/`.
> Tab visibility gated to `super_admin`/`ministry`/`region_admin` (`canSeeRegions`) — a
> region_admin sees only their own region since the backend scopes the rows; coaches/operators
> don't get the tab. Verified: eslint + vue-tsc + build clean.
> **F7 rating UI complete → F8 (comparison UI) next.**

A region-ranking table (high-daraja count per region, average physical_total) for
ministry/super_admin.
Edge case: visible to ministry/super_admin (region_admin sees own); optional
chart/map.

---

**BLOCK F8 — Comparison UI** (FRNTND-20) · dependency: BCKND-B9
Goal: the side-by-side comparison view.

---

# FRNTND-20 — Comparison view

> ✅ **Done** (2026-07-10) — `views/comparison/ComparisonView.vue` + `api/comparison.ts`
> (`GET /comparison/?athletes=1,2,3`). An `AthleteAutocomplete` adds 2–3 chips (dedupe, max 3);
> **Taqqoslash** calls the endpoint. Result = per-athlete cards (physical_total /50 + `DarajaBadge`,
> the **leader** card ringed + a "Yetakchi" crown tag) over a matrix table: rows = the ordered
> **union of exercise NAMES** (batteries differ by age×gender), per-exercise **winner** cell
> highlighted (highest points; ties highlight all), a "Umumiy ball" footer with the leader
> highlighted. No-evaluation athletes render "—". Selection reflects to `?athletes=` for shareable
> links; the athlete card's "Taqqoslash" pre-seeds `?athletes=<id>`. Scope is server-side (403 on
> out-of-scope, no leak). Verified: eslint + vue-tsc + build clean.
> **F8 comparison UI complete → F9 (recommendation & report UI) next.**

Pick 2–3 athletes and show them side-by-side: physical_total, daraja,
exercise-by-exercise points, with the leader highlighted.
Edge case: 2–3 only; highlight the leader (highest physical_total) and the per-exercise
winner; note batteries differ by age×gender.

---

**BLOCK F9 — Recommendation & Report UI** (FRNTND-21 … FRNTND-22) · dependency: BCKND-B10, BCKND-B12
Goal: recommendations display and the report request/download flow.

---

# FRNTND-21 — Recommendations view

> ✅ **Done** (2026-07-10) — `views/recommendations/RecommendationsView.vue`: a tab for **sportchi
> tavsiyalari** (an `AthleteAutocomplete` → the existing `RecommendationsPanel`, which reads the
> latest evaluation's generated recs from `GET /recommendations/?athlete=`) and a super_admin-only
> **Qoidalar** tab (`components/recommendations/RulesManager.vue`) — full CRUD on
> `/recommendation-rules/` (target = exercise 0–10 or physical_total 0–50, comparator, threshold,
> template, is_active) with a Dialog form + confirm-delete; thresholds stay DATA (SCORING §8) and
> the form caps them to mirror the backend validation. Fixed `api/recommendations.ts`: the
> serialized `exercise` is the NAME string, not an id. Verified: eslint + vue-tsc + build clean.

Show generated recommendations on the athlete/evaluation; (admin) manage
recommendation rules (conditions on points/total).
Edge case: recommendations come from the latest evaluation; rules management gated to
super_admin.

# FRNTND-22 — Reports UI (request + download)

> ✅ **Done** (2026-07-10) — `views/reports/ReportsView.vue` + `api/reports.ts`. A request form
> (type Sportchi/Viloyat/Sport/Respublika + format PDF/Word/Excel): the **athlete** type shows an
> `AthleteAutocomplete`, the ranking/republic types show optional region/sport/age/gender filters;
> `POST /reports/` (202). A list table shows each report's status (Navbatda/Ishlanmoqda/Tayyor/Xato
> Tag + spinner while active) and **polls `GET /reports/` every 2.5s while any report is
> pending/processing**, stopping when none are (cleared on unmount). **Yuklab olish** is enabled
> only when `done` → `GET /reports/{id}/download/` as a blob, filename from Content-Disposition,
> anchor-click save; a 409-before-done never happens since the button is gated. Scope + visibility
> are server-side (requester-only; super_admin/ministry see all). Verified: eslint + vue-tsc + build
> clean.
> **F9 recommendation & report UI complete → F10 (dashboard UI) next.**

Request a report (type, format, params), see its status
(pending/processing/done/failed), and download when ready; polls `/reports/{id}`.
Edge case: async status polling; download enabled only when `done`; scope params to
the user.

---

**BLOCK F10 — Dashboard UI** (FRNTND-23 … FRNTND-24) · dependency: BCKND-B13
Goal: the role-scoped dashboard with stats and charts.

---

# FRNTND-23 — Dashboard / home

> ✅ **Done** (2026-07-10) — upgraded `views/HomeView.vue` into the dashboard, fed by
> `GET /stats/overview/` (`api/stats.ts`). A role-framed subtitle (ministry → Respublika, coach →
> own athletes) over a KPI grid (`components/dashboard/StatCard.vue`): faol sportchilar, I-daraja
> soni, soʻnggi-30-kun sessiyalari, viloyatlar + an OTM/OPSTTM caption. Recent activity = the
> scoped `recent_sessions` count; quick-link cards to the main sections. All numbers are scoped
> server-side. Verified: eslint + vue-tsc + build clean.

A role-scoped dashboard: key counts (athletes, by daraja), recent activity,
quick links; fed by `/stats/overview`.
Edge case: role-scoped numbers; different emphasis per role (ministry → national,
coach → own athletes).

# FRNTND-24 — Charts + polish

> ✅ **Done** (2026-07-10) — `components/dashboard/DarajaDonut.vue` (doughnut of the by-daraja
> distribution, fixed I/II/III/none colours) and `RegionBars.vue` (horizontal bar of per-region
> I-daraja counts from `/rating/regions/`, mounted only for super_admin/ministry). Both **degrade
> to an empty-state Message** with no data. The dashboard has explicit loading / error (with a
> "Qayta urinish" retry) / empty states; KPI, chart and quick-link grids use `auto-fit minmax`
> for mobile responsiveness (TZ #15). Uzbek enum labels come from the existing `constants/labels.ts`
> maps (full multi-locale vue-i18n is the separate FRNTND-25). Verified: eslint + vue-tsc + build
> clean.
> **F10 dashboard UI complete → FRNTND track (F1–F10) done. Remaining: gap-review additions
> (FRNTND-25/26, BCKND-68/69/70, DVPS-20).**

Charts (daraja distribution, by region), responsive polish, and consistent
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
English-enum → localized-label maps (daraja, colors) live in the locale files.
Edge case: reference/content data (region/sport/exercise names, recommendation texts)
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
physical 10/8/6 → daraja scoring + the "Top Athletes" feature) to the implementing
task(s) and an acceptance check; plus a UAT checklist for client sign-off.
Edge case: every TZ requirement must map to ≥1 task (coverage gaps surface here);
keep it updated as tasks change; this is the QA acceptance basis.

---

## DEFERRED (parked — see `docs/DEFERRED.md`)

The physical-first re-scope parked the tasks below. They are **not deleted** — the design
is correct in spirit but cannot be built until the client delivers the functional /
morphofunctional / psychological criteria (and their real structure may differ, as the
physical criteria did). One-line rationale per item; revisit when those criteria arrive.

# DEF-1 — WeightCategory model (was part of BCKND-18)

`WeightCategory(sport_type, gender, name, min_kg, max_kg)` + the `weight-categories`
API/filter. Rationale: weight belongs to the morphofunctional category, which has no
criteria yet; the physical scheme groups by age × gender only, and `weight_category` is
not on the Athlete either.

# DEF-2 — TestType block/category model + OTM/OPSTTM test seed (was BCKND-19, BCKND-24)

The old `TestType(block, category, unit, direction, …)` model and the OTM-10
(5 physical + 5 functional) / OPSTTM morpho(7) + psych(6) test seed. Rationale: replaced by
the block-independent `Exercise` pool + `TestBattery`; the non-physical test lists
(functional/morpho/psych) wait for real criteria (`DEFERRED.md` §2).

# DEF-3 — Sport/block-specific norms + lookup fallback (was part of BCKND-26/27)

`Norm.sport_type` / `Norm.block` and the `sport+age+gender → age+gender` lookup fallback.
Rationale: physical norms are sport- and block-independent; the lookup is now an exact
numeric-age match (`DEFERRED.md` §4).

# DEF-4 — LevelThreshold (percentage → 5/3 levels) (was BCKND-30)

The OTM 5-level / OPSTTM 3-level percentage cut-offs config + seed. Rationale: physical uses
`physical_total` (0–50) → `DarajaThreshold` (I/II/III), not a percentage → 5/3-level mapping.

# DEF-5 — BMI computation + category (was BCKND-44)

`bmi(weight_kg, height_cm)` + `bmi_category(value)` (7 categories). Rationale: BMI is
morphofunctional and informational only, with no active criteria (`DEFERRED.md` §3).
`TestSession.height_cm`/`weight_kg` remain nullable placeholders for this future work.

# DEF-6 — OTM/OPSTTM evaluation strategies (was BCKND-45)

`OtmEvaluationStrategy` / `OpsttmEvaluationStrategy` (strategy polymorphism; per-block
percentage + 5/3 levels + equal-weighted category average). Rationale: superseded by the
single physical scheme; `Organization.type` is now a classification attribute only
(`DEFERRED.md` §1).

# DEF-7 — Multi-category Evaluation fields + non-physical report types (touched BCKND-43, BCKND-62)

The multi-category `Evaluation` fields (`bmi_value`, `physical_pct`/`functional_pct`/
`morpho_pct`/`psych_pct`, `percentage`, `level`) and the OTM/OPSTTM report types. Rationale:
how physical + functional + morpho + psych combine into one verdict is undefined until those
criteria exist (`DEFERRED.md` §4); Evaluation now stores `physical_total`/`daraja` only.

# DEF-8 — Excel bulk-import of non-physical norms (touched B4)

Bulk norm import for the functional/morpho/psych categories. Rationale: only the physical
tables exist today; they load via `seed_physical` (BCKND-32). Other-category import waits
for criteria (`DEFERRED.md` §4).
