---
name: Project — SPORT-DIAGNOSTIKA.UZ
description: Static landing+login site for an Uzbek athlete monitoring platform; current state has lite (MVP demo) at root and premium hidden under premium/
type: project
originSessionId: 88e28f80-af71-4306-99ce-935db4fcd38d
---
**Project:** SPORT-DIAGNOSTIKA.UZ — landing + login pages for a future platform that tracks physical/functional readiness of OPSTTM athletes and OTM (university) student-athletes across Uzbekistan. Original spec: `SPORT.docx` in repo root.

**Repo:** `https://github.com/JahonovAsilbek/sport-diagnostika`. Custom domain via root `CNAME` (likely `sport-diagnostika.uz`). Deployed via GitHub Pages from `main` branch root. Local path: `/Users/asilbekjahonov/personal/sport`.

**Current layout (as of 2026-05-08):**
- Root `index.html`, `login.html`, `assets/css/style.css`, `assets/js/main.js`, `assets/img/logo.svg` → **LITE** (light-mode, simple, MVP feel)
- `premium/index.html`, `premium/login.html`, `premium/assets/...` → **PREMIUM** (dark mode, gradients, animations, more sections like hero illustration + floating athlete card)
- `CONTRACT.md` and `LITE-CONTRACT.md` are local-only build specs used to coordinate parallel agents (not the platform's contracts).

**Why two versions:**
- **Why:** The user is about to demo the project to a paying client and is worried that a polished SaaS-style design will make the client suspicious that "the work isn't real / has been over-promised." The lite version intentionally looks like an honest in-progress MVP.
- **How to apply:**
  - Treat root `/` as the **client-facing demo**. Don't add slick effects there — keep it plain, light, government-form-like.
  - Treat `premium/` as the **real direction** the project will return to after the demo. Improvements/features should also be reflected in premium.
  - When the user says "demo o'tkazganimdan keyin hozirgi versiyaga yana qaytamiz" he means he'll later swap them back: premium → root, lite removed or archived. The swap has been done with `git mv`, so it's reversible the same way (see commit `5bbeccd`).
  - Whenever you change branding/copy in one version, mirror it to the other unless the user says otherwise — they're meant to be the same product, only the styling differs.

**Footer credit:** Both versions show `jahonov.uz` (link only, no "Ishlab chiquvchi:" prefix) in `.footer-credit` inside `.footer-bottom`. Don't reintroduce the prefix.

**Login form:** Static demo only — `onsubmit="event.preventDefault();"`. There is no role select (it was explicitly removed); just username + password + remember-me + forgot-password link. Don't reintroduce the role select.

**Build philosophy that worked here:**
- The user likes the "8 parallel agents + shared CONTRACT.md" pattern for new builds. The CONTRACT defines tokens/class names so parallel CSS/HTML agents stay coherent. Keep that pattern available for future expansions.
