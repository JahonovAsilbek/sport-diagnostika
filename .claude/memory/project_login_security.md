---
name: project_login_security
description: Login throttling + cache-based brute-force lockout; the root autouse cache-isolation test fixture
metadata:
  type: project
---

**Login security (BCKND-69).**

- DRF throttling in `REST_FRAMEWORK` (`config/settings/base.py`): global `AnonRateThrottle` +
  `UserRateThrottle` for the whole API; `LoginView` sets `throttle_classes = [ScopedRateThrottle]`
  + `throttle_scope = "login"` for a harder cap. Rates are env vars `THROTTLE_ANON` / `THROTTLE_USER`
  / `THROTTLE_LOGIN` (defaults 60/min, 2000/day, 10/min).
- Brute-force lockout in `apps/accounts/security.py` — **cache/Redis, keyed per (username, IP)**.
  N failures in a window → lock for a cooldown. Config: `LOGIN_LOCKOUT_THRESHOLD` / `_WINDOW` /
  `_COOLDOWN` (defaults 5 / 900s / 900s). **Fails open** on a cache outage (the rate throttle still
  caps volume) rather than locking everyone out.
- `LoginView.post` (`apps/accounts/api.py`) checks the lock first (→ 429), counts a failure on
  `rest_framework.exceptions.AuthenticationFailed`, clears the counter on success, and always
  returns the **same generic** error (`"Login yoki parol noto'g'ri."`) for wrong-password /
  unknown-user / locked — no account enumeration.
- Client IP comes from the shared `apps/audit/context.client_ip(request)` (first X-Forwarded-For
  hop only when `AUDIT_TRUST_X_FORWARDED_FOR` is set — prod behind Nginx; else `REMOTE_ADDR`).

**Test gotcha:** the root `conftest.py` has an **autouse `_isolate_cache`** fixture that
`cache.clear()`s before every test. Required because throttling + the lockout + the stats/rating
caches all live in the shared cache and would otherwise leak counters across tests (a test making
>10 login or >60 anon requests would spuriously 429). Any new cache-dependent test relies on this.
Related: [[project_dev_toolchain]], [[project_deploy_prod]].
