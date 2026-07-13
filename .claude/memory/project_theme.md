---
name: project_theme
description: SPA premium dark theme (FRNTND-29+) — cyan/navy PrimeVue preset, dark-by-default, html.dark var-override technique; migration is phased F29→F32
metadata:
  type: project
---

The SPA adopts the `premium/` landing's visual language (`premium/assets/css/base.css`): an
electric-cyan primary (`#00D4FF`) over deep-navy surfaces (`#07101F` ground / `#0E1B30` cards /
`#1F3354` borders), **dark by default**, Inter font, glow accents.

**How it's wired (FRNTND-29):**
- `src/theme/preset.ts` — `definePreset(Aura, …)` overriding `semantic.primary` (cyan 50–950) and
  `semantic.colorScheme.dark.surface` (navy 0–950, high index = darker bg), plus dark `primary`
  (contrast `#04111E`) + `highlight`. Every PrimeVue component inherits the token graph.
- `main.ts` — uses `SportPreset`, `darkModeSelector:'.dark'`, and **adds `.dark` to `<html>` at boot**
  (dark by default). Imports `@fontsource-variable/inter` (self-hosted, incl. Cyrillic).
- `src/assets/main.css` — premium `--color-*` / radius / shadow / glow tokens, radial-glow
  `body::before`, dark scrollbars. **Key technique:** the shell + components read `--p-*` PrimeVue
  vars directly, so `html.dark { --p-content-background: … }` (specificity 0,1,1 — outranks
  PrimeVue's `.dark`) pins the shell-critical vars to exact premium hues without touching each file.

**Palette anchors:** primary `#00D4FF` / accent `#1EB53A` / warn `#F5B700` / danger `#EF4444` /
success `#10B981`; daraja badges (green/yellow/red) already align.

**Migration is phased:** F29 foundation (done) → **F30** shell+login → **F31** component/view sweep
(remove hardcoded light fallbacks like `#fff`/`#e2e8f0`/`#f1f5f9`) → **F32** polish (glows,
transitions, chart palettes, empty states). When restyling a view, prefer the `--color-*` /
`--p-*` tokens over hardcoded colors. See [[project_frontend]].
