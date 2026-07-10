---
name: project_frontend
description: Frontend stack + conventions (Vue 3 + TS + PrimeVue) — decisions, auth wiring, verify commands
metadata:
  type: project
---

The Vue 3 SPA lives in `frontend/` (scaffolded in F1, FRNTND-1…4). Confirmed foundational choices
(both were "decision to confirm" in TASK.md):

- **TypeScript** (not plain JS) and **PrimeVue 4** (not Naive UI) — pick-ONE, locked.
- **Theme preset comes from `@primeuix/themes`** (e.g. `import Aura from '@primeuix/themes/aura'`),
  NOT `@primevue/themes` — the latter is deprecated as of primevue 4.5. `app.use(PrimeVue, { theme:
  { preset: Aura, options: { darkModeSelector: '.dark' } } })`.

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
  Uzbek labels + the daraja map live in `src/constants/labels.ts` (English enum → Uzbek display,
  CLAUDE.md §4). Extend that file per feature rather than hardcoding labels in components.

The SPA build (`frontend/dist`) is what nginx serves in prod (D3/D5) — `/` 404s until it exists.
See [[project_deploy_prod]].
