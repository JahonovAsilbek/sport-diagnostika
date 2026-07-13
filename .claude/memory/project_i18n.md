---
name: project_i18n
description: Frontend i18n (FRNTND-25) — vue-i18n setup, per-namespace glob-composed locales, kk→uz fallback, $t/useI18n convention, enum-label helper functions
metadata:
  type: project
---

Frontend i18n (FRNTND-25) — vue-i18n v11, Composition mode (`legacy:false`, `globalInjection:true`).

**Architecture (`frontend/src/i18n/`):**
- `config.ts` — locale registry (`SUPPORTED_LOCALES = ['uz','ru','kk','en']`, `DEFAULT_LOCALE='uz'`, `LOCALE_META`, `isSupportedLocale`). Leaf module, no imports → no cycle.
- `messages.ts` — composes the message tree from `locales/*.ts` via **`import.meta.glob({ eager:true, import:'default' })`**. Adding a namespace = just drop a new `locales/<ns>.ts` file; it auto-wires (no registration edit).
- `index.ts` — `createI18n({ fallbackLocale:'uz', ... })`; `setLocale()` persists to `localStorage['locale']` + sets `<html lang>`; `getStoredLocale()`.
- `labels.ts` — enum→label **functions** (`roleLabel`, `darajaLabel`, `genderLabel`, `orgTypeLabel`, `valueTypeLabel`, `directionLabel`, `reportTypeLabel`, `reportStatusLabel`), each `i18n.global.t('enums.<x>.<key>')`. Functions (not const maps) so they're reactive to locale AND callable from plain `.ts` (api/*, utils/*). Call `i18n.global.t(...)` as a method — never destructure `t` (loses binding).

**Locale files:** one per namespace, `export default { uz:{…}, ru:{…}, en:{…} }` — **kk omitted on purpose** (ru+en fully translated, kk falls back to uz per user decision; a native speaker fills kk later). 14 namespaces, ~299 uz keys.

**Conventions (follow these in new components):**
- Templates: `$t('ns.key')` (global injection).
- Scripts: `const { t } = useI18n({ useScope: 'global' })` — the `{ useScope:'global' }` is REQUIRED, else vue-i18n uses a local scope and spams dev-console fallback warnings.
- Reactive option arrays / computed labels that use `t` or a label helper must be wrapped in `computed(() => …)`.
- Interpolation: named only — `'{n} ta'` + `$t('k', { n })`. No plural pipe `|`.

**What is NOT translated (kept literal / Uzbek content):** reference data from the API (region/district/organization/sport/exercise/age-category NAMES, athlete names, recommendation/rule texts); locale-neutral tokens (comparator symbols ≤<≥>, report formats PDF/Word/Excel, OTM/OPSTTM acronyms, `mm:ss`). `constants/labels.ts` keeps only `DarajaLevel`/`Severity` types + `DARAJA_SEVERITY` (CSS severities) — all enum LABEL maps moved to i18n. See [[project_frontend]], [[project_period_filter]] (FRNTND-26 period UI reuses the switcher + `enums.periodType`).
