# LITE-VERSION BUILD CONTRACT

This is a **simplified MVP demo version** of the SPORT-DIAGNOSTIKA.UZ site, sitting under `lite/`. The premium version remains untouched at the repo root.

**Goal:** Look like an honest early-stage MVP — clean, plain, government/educational feel. Not a polished SaaS. The client should perceive "real, in-progress work," not "expensive finished product."

## Style direction

- **Light mode.** White/very light page background.
- **Simple, conservative palette.** Royal blue primary + Uzbekistan green accent.
- **Minimal effects.** No gradient text, no floating animations, no glow/blur, no count-up.
- **Plain typography.** Inter or system font. No display tricks.
- **Borders, not shadows.** Subtle 1px borders on cards; tiny shadow at most.
- **Static.** Hover states OK, but nothing animated on load.
- **Same content** as premium version (same Uzbek copy, same sections, same data) — only styling changes.

## Tokens (in `lite/assets/css/style.css`)

```
--bg:          #ffffff
--bg-alt:      #f8fafc
--bg-soft:     #f1f5f9
--border:      #e2e8f0
--border-strong: #cbd5e1
--text:        #0f172a
--text-muted:  #475569
--text-dim:    #64748b

--primary:     #1d4ed8       /* royal blue */
--primary-700: #1e40af
--accent:      #15803d       /* forest green (UZ flag) */
--accent-700:  #166534
--warn:        #d97706
--danger:      #dc2626

--radius-sm: 4px
--radius:    8px
--radius-lg: 12px

--shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04)
--shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)

--font: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
--container: 1120px
```

Body: `background: var(--bg); color: var(--text); font-family: var(--font); font-size: 16px; line-height: 1.6;`

## File structure

```
lite/
├── index.html
├── login.html
└── assets/
    ├── css/style.css     (single CSS file — no imports, ~250-350 lines)
    ├── js/main.js        (~30 lines: mobile menu only)
    └── img/logo.svg      (small simple logo)
```

`<head>` of each HTML links: Inter from Google Fonts, then `assets/css/style.css`, then `defer` JS.

## Page structure (same as premium, simpler look)

### `lite/index.html`

Same sections as premium:
- Header: brand left, nav (Imkoniyatlar, Bloklar, Qanday ishlaydi, Statistika, Aloqa), action buttons. White background, 1px bottom border.
- Hero: text only — eyebrow, h1, paragraph, two buttons. **No illustration, no floating card.** A single right-side mini-panel showing "Reyting namunasi" with 3 plain rows is OK and helpful, but keep it as a plain bordered box.
- Features: 9 cards. Plain white cards with 1px border, small icon (24×24 line SVG), title, 1-line text. Grid 3-col → 2-col → 1-col.
- Blocks: 2 cards (OTM, OPSTTM) — plain white with simple top accent (2px solid line in primary or accent color), title, description, plain bullet list.
- How: 5 numbered steps in a simple grid. Just numbers in colored circles + title + text. No connector line.
- Stats: 4 simple stat tiles (large number + label) and the rating preview table — plain table with bordered rows, color dots/badges next to score.
- CTA: simple centered block with title + 2 buttons.
- Footer: 4 columns, light gray bg.

### `lite/login.html`

Plain centered form on a slightly off-white background. **No two-column split.** Single centered card:
- Brand on top
- "Tizimga kirish" heading
- Foydalanuvchi nomi input
- Parol input
- "Meni eslab qol" + "Parolni unutdingizmi?"
- "Kirish" button (full width, primary)
- Help line below
- "← Bosh sahifaga qaytish" link

Form: `onsubmit="event.preventDefault();"`

## Class names (use these — same as premium for content parity, but styled simply)

`.container, .btn, .btn-primary, .btn-ghost, .btn-block, .site-header, .nav, .nav-links, .nav-actions, .nav-burger, .brand, .brand-logo, .brand-name, .brand-tld, .hero, .hero-inner, .hero-content, .eyebrow, .hero-title, .hero-subtitle, .hero-actions, .hero-aside (replaces .hero-visual — a simple side panel with stat preview), .features, .section-head, .section-title, .section-subtitle, .features-grid, .feature-card, .feature-icon, .feature-title, .feature-text, .blocks, .blocks-grid, .block-card, .block-card--primary, .block-card--accent, .block-num, .block-title, .block-desc, .block-list, .block-meta, .how, .how-grid, .how-step, .how-step-num, .how-step-title, .how-step-text, .stats, .stats-grid, .stat, .stat-num, .stat-label, .rating-preview, .rating-row, .rating-rank, .rating-name, .rating-region, .rating-score, .badge-green, .badge-yellow, .badge-red, .cta, .cta-inner, .cta-actions, .site-footer, .footer-inner, .footer-col, .footer-title, .footer-list, .footer-brand, .footer-desc, .footer-bottom, .login-page, .login-card, .login-title, .login-subtitle, .login-form, .form-row, .form-row-inline, .form-control, .checkbox, .link-muted, .login-foot, .login-back, .tag`

## Rules for ALL agents

- All visible text in **Uzbek (Latin)**. Use proper apostrophes (`'`) for o' / g'.
- No emojis. Use small line SVGs (24×24, stroke=currentColor, stroke-width=2) for icons.
- No comments unless non-obvious.
- No frameworks, no Tailwind, no JS deps. Plain HTML/CSS/JS.
- Don't touch the premium version files (root level). Only write inside `lite/`.
- Lite version logo can reuse the premium SVG mark but with simpler color (primary blue + accent green, no gradient — flat colors only).
