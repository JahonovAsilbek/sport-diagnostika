---
name: project_theme
description: SPA theme mirrors the LITE root landing — minimal light theme, blue primary; token-based so components restyle via CSS vars
metadata:
  type: project
---

The SPA theme mirrors the **root landing** (`assets/css/style.css`, the *lite* version) — a clean,
minimal **light** theme with a **blue primary**. (An earlier premium dark cyan/navy pass, F29–F32,
was reverted per user preference on 2026-07-13; the app is light now.)

**Palette (from the landing `:root`):** page `#f8fafc` / cards `#ffffff` / soft `#f1f5f9`; borders
`#e2e8f0` (strong `#cbd5e1`); text `#0f172a` / muted `#475569` / dim `#64748b`; **primary `#1d4ed8`**
(hover `#1e40af`), accent green `#15803d`, warn `#d97706`, danger `#dc2626`. Radii 4/8/12; subtle
`--shadow-sm`; Inter font. **No gradients / glow** — minimal and flat.

**How it's wired:**
- `src/theme/preset.ts` — `definePreset(Aura, …)` with a **blue** primary scale (500 = `#1d4ed8`),
  light mode (no dark colorScheme override). Aura light supplies the surfaces.
- `main.ts` — uses `SportPreset`; `darkModeSelector: '.app-dark'` (never applied → always light);
  self-hosts Inter via `@fontsource-variable/inter`.
- `src/assets/main.css` — the lite `--color-*` tokens + light scrollbars + a muted table header.
  Two legacy tokens are kept **flat** so component styles need no edits: `--gradient-card: #ffffff`
  and `--shadow-glow: var(--shadow-sm)` (so any `var(--gradient-card)` card is white and any
  `var(--shadow-glow)` hover is a subtle shadow, not a glow).

**Convention:** style with the `--color-*` / `--p-*` tokens, never hardcoded colors. Shell/cards
use `--color-*`; PrimeVue components follow Aura-light + the blue primary. Daraja badges/charts keep
green/yellow/red (TZ #9 indicator). See [[project_frontend]], [[project_i18n]].
