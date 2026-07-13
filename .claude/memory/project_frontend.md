---
name: project_frontend
description: Frontend stack + conventions (Vue 3 + TS + PrimeVue) — decisions, auth wiring, verify commands
metadata:
  type: project
---

The Vue 3 SPA lives in `frontend/` (scaffolded in F1, FRNTND-1…4). Confirmed foundational choices
(both were "decision to confirm" in TASK.md):

- **TypeScript** (not plain JS) and **PrimeVue 4** (not Naive UI) — pick-ONE, locked.
- **Theme preset comes from `@primeuix/themes`** (`import Aura from '@primeuix/themes/aura'`), NOT
  `@primevue/themes` (deprecated as of primevue 4.5). The app now ships a **custom dark preset**
  (cyan/navy, dark by default) — see [[project_theme]].

Stack: Vite 6, Vue Router, Pinia (setup stores), axios, ESLint 9 flat config
(`@vue/eslint-config-typescript` + `eslint-plugin-vue` + prettier-skip-formatting), Prettier
(no-semi, single-quote, printWidth 100). Path alias `@/* → src/*`. Vite dev-proxies `/api` →
`http://localhost:8000` (override `VITE_API_TARGET`) — mirrors the nginx prod topology.

**Verify (run from `frontend/`):** `npm run lint:check` · `npm run type-check` (vue-tsc --noEmit) ·
`npm run build`. All three must pass before a frontend block is done (CLAUDE.md §8 frontend = eslint
+ build/type-check).

**Auth wiring (FRNTND-2/3):**
- Tokens (JWT pair) live in `src/api/tokens.ts` (localStorage, keys `sd.access`/`sd.refresh`) — a
  single source both the axios interceptor and the Pinia auth store read, so there's **no import
  cycle** (client ↔ store).
- `src/api/client.ts` interceptor: attaches the access token; on 401 refreshes with a
  **single-flight lock** (`refreshPromise` shared across concurrent 401s) via a *bare* axios
  instance (using the intercepted one would recurse); retries; on refresh failure clears tokens +
  `window.location.assign('/login')`. `toMessage(error)` → Uzbek message.
- **`POST /auth/login/` returns `{access, refresh, user}` in one call** (LoginSerializer adds the
  profile), so the store skips a separate /me on login. `restore()` (app load) validates via
  `/auth/me/`. Logout: `POST /auth/logout/ {refresh}` blacklists.
- Roles (backend `Role`): `super_admin` · `region_admin` · `coach` · `lab_operator` · `ministry`.
  Enum→label helpers are **reactive functions in `src/i18n/labels.ts`** (FRNTND-25); `constants/
  labels.ts` keeps only `DarajaLevel`/`Severity`/`DARAJA_SEVERITY` (CSS). See [[project_i18n]].

**Management UIs (FRNTND-27/28):** users at `/users` (`UsersView` → User CRUD `/users/`, incl. the
`reset-password` action; region_admin scoped, can't create super_admin) and organizations at
`/catalog/organizations` (`OrganizationsView`, super_admin, linked from `CatalogView`). **Catalog
write is super_admin-only via `CatalogViewSet` (a `ModelViewSet` + `ReadOnlyOrSuperAdmin`)** — there
are no separate catalog write APIs, just reuse `/catalog/<entity>/` POST/PUT/DELETE. The read
`UserSerializer` now also exposes `first_name`/`last_name` (so the edit form prefills).

The SPA build (`frontend/dist`) is what nginx serves in prod (D3/D5) — `/` 404s until it exists.
See [[project_deploy_prod]].
