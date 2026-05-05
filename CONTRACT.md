# SPORT-DIAGNOSTIKA.UZ — Build Contract

This is a **shared contract** that every parallel agent MUST follow so the assembled site is coherent. Do not invent class names that aren't listed here. Do not redefine variables. Use only what's declared below.

Site is a **static landing + login** for an Uzbek athlete monitoring platform — **no backend, no real auth, no JS frameworks**. Plain HTML5, CSS3, vanilla JS. All visible text in **Uzbek (Latin)**.

---

## 1. Design tokens (declared in `assets/css/base.css`)

```
--color-bg:           #07101F   /* deep navy page background */
--color-bg-elev:      #0E1B30   /* card / elevated surface */
--color-bg-soft:      #15243C   /* subtle surface */
--color-border:       #1F3354
--color-text:         #E6EEFB
--color-text-muted:   #9AA8C2
--color-text-dim:     #6A7894

--color-primary:      #00D4FF   /* cyan — primary brand */
--color-primary-700:  #0099B5
--color-accent:       #1EB53A   /* green — Uzbekistan flag green */
--color-warn:         #F5B700
--color-danger:       #EF4444
--color-success:      #10B981

--gradient-hero:      linear-gradient(135deg, #00D4FF 0%, #1EB53A 100%)
--gradient-card:      linear-gradient(180deg, #15243C 0%, #0E1B30 100%)

--radius-sm: 6px
--radius:    12px
--radius-lg: 20px
--radius-pill: 999px

--shadow-sm: 0 2px 8px rgba(0,0,0,0.25)
--shadow:    0 8px 24px rgba(0,0,0,0.35)
--shadow-lg: 0 20px 60px rgba(0,0,0,0.5)
--shadow-glow: 0 0 40px rgba(0,212,255,0.25)

--font-sans: "Inter", "SF Pro Display", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
--font-display: "Inter", system-ui, sans-serif   /* same family, heavier weight */

--container: 1200px
--space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
--space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px; --space-9: 96px;
```

Use Inter from Google Fonts: `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap`

Body sets `background: var(--color-bg); color: var(--color-text); font-family: var(--font-sans);`

## 2. Global utility classes (in `base.css`)

- `.container` → `max-width: var(--container); margin: 0 auto; padding: 0 24px;`
- `.btn` → base button (pill, padding 12px 24px, font-weight 600)
- `.btn-primary` → background `var(--color-primary)`, color `#04111E`, hover lifts + glow
- `.btn-ghost` → transparent, border `1px solid var(--color-border)`, color `var(--color-text)`, hover bg `var(--color-bg-soft)`
- `.btn-lg` → larger padding (16px 32px), font-size 1.05rem
- `.eyebrow` → small uppercase label, color `var(--color-primary)`, letter-spacing 0.12em, font-size 0.78rem, font-weight 700
- `.section-title` → h2 style: 2.25rem clamped, font-weight 800, line-height 1.15
- `.section-subtitle` → 1.05rem, color `var(--color-text-muted)`, max-width 720px
- `.tag` → pill chip: bg `var(--color-bg-soft)`, border, padding 4px 12px, font-size 0.8rem
- `.badge-green`, `.badge-yellow`, `.badge-red` → status dots / badges using accent / warn / danger colors

## 3. Page structure — `index.html`

Single landing page with these sections in order. **Use these IDs and classnames exactly.**

```
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="#">
      <img src="assets/img/logo.svg" alt="" class="brand-logo">
      <span class="brand-name">SPORT-DIAGNOSTIKA<span class="brand-tld">.UZ</span></span>
    </a>
    <nav class="nav-links">
      <a href="#features">Imkoniyatlar</a>
      <a href="#blocks">Bloklar</a>
      <a href="#how">Qanday ishlaydi</a>
      <a href="#stats">Statistika</a>
      <a href="#contact">Aloqa</a>
    </nav>
    <div class="nav-actions">
      <a class="btn btn-ghost" href="login.html">Kirish</a>
      <a class="btn btn-primary" href="login.html">Boshlash</a>
    </div>
    <button class="nav-burger" aria-label="Menyu" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>

<main>
  <section class="hero" id="top"> ... </section>
  <section class="features" id="features"> ... </section>
  <section class="blocks" id="blocks"> ... </section>      <!-- 2 ta blok: OTM + OPSTTM -->
  <section class="how" id="how"> ... </section>            <!-- Qanday ishlaydi: 5 qadam -->
  <section class="stats" id="stats"> ... </section>        <!-- Reyting/indikator demo + raqamlar -->
  <section class="cta" id="contact"> ... </section>        <!-- Yakuniy chaqiriq -->
</main>

<footer class="site-footer"> ... </footer>
```

### Hero section (`section.hero`)
- Eyebrow: "O'zbekiston Respublikasi · OPSTTM va OTM"
- Title (h1): "Talaba-sportchilar **funksional va jismoniy** monitoring platformasi"
- Subtitle: ~2 sentence description in Uzbek explaining unified database for OPSTTM athletes and university student-athletes, automatic ranking by region/sport/age.
- Two buttons: `.btn btn-primary btn-lg` "Platformaga kirish" → login.html, `.btn btn-ghost btn-lg` "Imkoniyatlar" → #features
- Visual on right: `<div class="hero-visual">` containing `<img src="assets/img/hero-illustration.svg" alt="" class="hero-illustration">` plus a floating "athlete card" mock (`.hero-card`) with name "Aliyev A.", region "Namangan", sport "Gandbol", overall score badge "87 — Yuqori daraja" (green), and 3 mini metric rows.
- Below the headline, a row of `.hero-trust` showing 3 small items with icons + text: "14 hudud", "30+ sport turi", "5 yosh kategoriyasi".

### Features section (`section.features`)
- Eyebrow: "IMKONIYATLAR"
- Title: "Bitta tizimda — diagnostika, monitoring, reyting va tavsiya"
- Subtitle: 1 sentence summary.
- Grid of **9 feature cards** (`.features-grid` with `.feature-card`). Each card:
  - `.feature-icon` (inline SVG OK, or emoji fallback as a minimal placeholder — but prefer simple inline SVG icons)
  - h3 `.feature-title`
  - p `.feature-text`
- The 9 cards (titles + 1-sentence text in Uzbek):
  1. **Sportchi bazasi** — har bir sportchi uchun shaxsiy elektron karta: shaxsiy ma'lumot, sport turi, razryad, murabbiy.
  2. **Hududlar kesimi** — Qoraqalpog'iston, Toshkent shahri va 12 viloyat bo'yicha alohida ko'rinish.
  3. **Sport turlari saralash** — gandbol, futbol, boks, dzyudo, kurash, suzish va boshqalar bo'yicha eng kuchli sportchilarni avtomatik aniqlash.
  4. **Yosh kategoriyalari** — 12–13, 14–15, 16–17, 18–21, 22+ guruhlari uchun alohida me'yorlar.
  5. **Jismoniy tayyorgarlik testlari** — 30/60/100 m yugurish, sakrash, tortilish, qo'l kuchi, chaqqonlik — avtomatik balga aylantiriladi.
  6. **Funksional ko'rsatkichlar** — Polar H10 puls, tiklanish vaqti, OTS, spirografiya, aerob imkoniyat.
  7. **Avtomatik reyting** — viloyat, sport turi, yosh, jins va tashkilot kesimida yuqori → past tartibida tartiblanadi.
  8. **Rangli indikator** — yashil/sariq/qizil tizimi orqali bir qarashda holatni baholash.
  9. **Tavsiya va hisobot** — sportchiga ilmiy tavsiya, PDF/Word/Excel formatda avtomatik hisobot.

### Blocks section (`section.blocks`) — 2 ta asosiy blok
- Eyebrow: "ASOSIY BLOKLAR"
- Title: "Ikki yo'nalish — bitta platforma"
- Two columns (`.blocks-grid` with two `.block-card`):
  - **Block 1: OTM talaba-sportchilari** — list of metrics: Tana vazni indeksi, Jismoniy tayyorgarlik (5 test), Funksional holat (5 test). Add a `.block-meta` line: "Universitet va institutlar talabalari uchun"
  - **Block 2: OPSTTM sportchilari** — Olimpiya va paralimpiya tayyorlash markazlari. Metrics: Tana vazni indeksi, Jismoniy tayyorgarlik, Funksional holat, **Morfofunksional holat**, **Psixologik holat**.
- Each block card: header with number badge ("01" / "02"), title, description, then `<ul class="block-list">` of metric items each with a small check/dot icon.

### How section (`section.how`) — 5 qadam
- Eyebrow: "QANDAY ISHLAYDI"
- Title: "Ma'lumotdan reytinggacha — 5 qadamda"
- 5 step cards in a horizontal grid (`.how-grid` with `.how-step`):
  1. **Ma'lumot kiritish** — qo'lda yoki Excel orqali ommaviy yuklash.
  2. **Test natijalari** — jismoniy va funksional sinovlar bal sifatida saqlanadi.
  3. **Avtomatik tahlil** — yosh, jins, sport turi va hudud kesimida solishtirish.
  4. **Reyting va indikator** — yuqori/o'rta/past darajalar yashil-sariq-qizil bilan ko'rsatiladi.
  5. **Tavsiya va hisobot** — ilmiy asoslangan tavsiya hamda PDF/Word/Excel hisobot.

Each step has a `.how-step-num` ("01"–"05"), `.how-step-title`, `.how-step-text`.

### Stats section (`section.stats`)
- Eyebrow: "RAQAMLARDA"
- Title: "Yagona elektron baza — butun respublika miqyosida"
- Row of 4 stat cards (`.stats-grid` with `.stat`):
  - `.stat-num` "14" / `.stat-label` "Hudud"
  - `.stat-num` "30+" / `.stat-label` "Sport turi"
  - `.stat-num` "5" / `.stat-label` "Yosh kategoriyasi"
  - `.stat-num` "100%" / `.stat-label` "Avtomatik tahlil"
- Below the stats, a **rating preview panel** (`.rating-preview`) showing a mock leaderboard with 3 rows:
  - "1. Aliyev A. — Namangan — 87 ball" with green badge "Yuqori"
  - "2. Valiyev B. — Samarqand — 79 ball" with yellow badge "O'rta"
  - "3. Karimov S. — Toshkent — 62 ball" with red badge "Past"
- Show `.rating-preview-header` with column labels: "Sportchi", "Hudud", "Ball", "Daraja".

### CTA section (`section.cta`)
- Title: "Sportchilaringizni bir tizimga jamlang"
- Subtitle: short.
- Two buttons same as hero.

### Footer (`footer.site-footer`)
- 4 columns: brand+desc, "Platforma" links (Imkoniyatlar/Bloklar/Qanday ishlaydi/Statistika), "Foydalanuvchilar" links (Super admin / Viloyat admini / Murabbiy / Laboratoriya xodimi / Vazirlik), "Aloqa" (placeholder email/phone, "O'zbekiston Respublikasi").
- Bottom row: "© 2026 SPORT-DIAGNOSTIKA.UZ — Barcha huquqlar himoyalangan."

## 4. Page structure — `login.html`

Two-column split layout:

```
<div class="login-page">
  <aside class="login-side">         <!-- left brand panel, hidden on mobile -->
    <a class="brand" href="index.html"> ... </a>
    <h2 class="login-side-title">Talaba-sportchilar funksional va jismoniy monitoring</h2>
    <p class="login-side-text">Yagona elektron baza — OPSTTM va OTM uchun.</p>
    <ul class="login-side-list">
      <li>Avtomatik reyting va indikator</li>
      <li>Hudud, sport turi va yosh kesimida tahlil</li>
      <li>PDF / Word / Excel hisobotlar</li>
    </ul>
  </aside>

  <main class="login-main">
    <a class="brand login-brand-mobile" href="index.html"> ... </a>
    <div class="login-card">
      <h1 class="login-title">Tizimga kirish</h1>
      <p class="login-subtitle">Foydalanuvchi nomi va parolingizni kiriting.</p>

      <form class="login-form" onsubmit="event.preventDefault();">
        <div class="form-row">
          <label for="role">Rol</label>
          <select id="role" class="form-control">
            <option>Super admin</option>
            <option>Viloyat admini</option>
            <option>Murabbiy</option>
            <option>Laboratoriya xodimi</option>
            <option>Vazirlik vakili</option>
          </select>
        </div>
        <div class="form-row">
          <label for="login">Foydalanuvchi nomi</label>
          <input id="login" class="form-control" type="text" placeholder="ism.familiya" autocomplete="username">
        </div>
        <div class="form-row">
          <label for="password">Parol</label>
          <input id="password" class="form-control" type="password" placeholder="••••••••" autocomplete="current-password">
        </div>
        <div class="form-row form-row-inline">
          <label class="checkbox"><input type="checkbox"> Meni eslab qol</label>
          <a href="#" class="link-muted">Parolni unutdingizmi?</a>
        </div>
        <button class="btn btn-primary btn-lg btn-block" type="submit">Kirish</button>
      </form>

      <p class="login-foot">Hisobingiz yo'qmi? <a href="#">Tizim administratori bilan bog'laning</a></p>
    </div>

    <p class="login-back"><a href="index.html">← Bosh sahifaga qaytish</a></p>
  </main>
</div>
```

## 5. CSS file split

All CSS lives in `assets/css/`. `index.html` and `login.html` link a single `assets/css/main.css` which `@import`s the others (this file is created by the harness, not the agents). Agents only write their assigned file.

- `base.css` — Tokens, reset, typography, generic `.container`, buttons (`.btn`, `.btn-primary`, `.btn-ghost`, `.btn-lg`, `.btn-block`), eyebrow, section-title, section-subtitle, tag, badge-green/yellow/red, link-muted, checkbox.
- `layout.css` — `.site-header`, `.nav`, `.nav-links`, `.nav-actions`, `.nav-burger` + mobile open state (`.nav-links.open`), `.brand`, `.brand-logo`, `.brand-name`, `.brand-tld`, `.site-footer` columns + bottom bar, footer link styles. Sticky header with subtle blur background when scrolled (class `.scrolled` toggled by JS).
- `sections.css` — `.hero`, `.hero-inner` (2-col grid → stacks on mobile), `.hero-visual`, `.hero-illustration`, `.hero-card` (mock athlete card), `.hero-trust`, `.features`, `.features-grid` (3-col → 2-col → 1-col), `.feature-card`, `.feature-icon`, `.how`, `.how-grid` (5-col → wraps), `.how-step`, `.how-step-num`, `.cta`. Section vertical padding ~96px desktop, 64px mobile.
- `blocks.css` — `.blocks`, `.blocks-grid` (2-col → 1-col), `.block-card` (with subtle gradient border accent — primary for OTM, accent green for OPSTTM), `.block-num`, `.block-list` items with check icon, `.block-meta`. Plus `.stats`, `.stats-grid` (4-col → 2-col), `.stat`, `.stat-num`, `.stat-label`, `.rating-preview`, `.rating-preview-header`, `.rating-row` (with `.badge-green/yellow/red`).
- `login.css` — `.login-page` (split 2-col grid 1fr 1fr → 1-col mobile), `.login-side` (gradient hero-style background, hidden < 900px), `.login-main`, `.login-card`, `.login-title`, `.login-subtitle`, `.login-form`, `.form-row`, `.form-row-inline`, `.form-control` (matches design tokens, focus ring uses primary), `.checkbox`, `.btn-block`, `.login-foot`, `.login-back`, `.login-brand-mobile` (visible only on mobile when side hidden), `.login-side-title`, `.login-side-text`, `.login-side-list`.

## 6. JS contract (`assets/js/main.js`)

Vanilla, no deps. Implement only:
1. Mobile nav toggle: clicking `.nav-burger` toggles `.open` class on `.nav-links` and `aria-expanded`.
2. Sticky header shadow: add `.scrolled` to `.site-header` when `window.scrollY > 8`.
3. Smooth scroll for in-page anchor links (CSS `scroll-behavior: smooth` is fine, but also handle close-mobile-menu on click).
4. Animated count-up for `.stat-num` when `.stats` enters viewport (IntersectionObserver). If the value contains non-digits (e.g. "30+", "100%"), animate the leading digits and re-append the suffix.
5. Reveal-on-scroll: add `.in-view` class to elements with `[data-reveal]` when intersecting. CSS for transition is in sections.css (translateY+opacity → 0).

Keep it under ~120 lines. No frameworks.

## 7. SVG assets (`assets/img/`)

- `logo.svg` — 32×32 mark: a stylized circular "S" or shield with primary→accent gradient. Single-color fallback OK. Should look good at 28px.
- `hero-illustration.svg` — abstract sport+data illustration (~520×420). Examples: silhouette of a runner with overlaid data lines / heart-rate waveform / ranking bars. Use only colors from the design tokens. Keep it geometric/modern, not cartoonish.

## 8. Important rules for ALL agents

- All visible text **MUST be in Uzbek (Latin alphabet)**. Use proper apostrophes (`'`) for o' and g'.
- DO NOT add comments to HTML/CSS/JS unless they explain something non-obvious.
- DO NOT install dependencies, no Node/npm, no Tailwind, no React. Plain files only.
- DO NOT create extra files outside your assigned ones.
- Reference design tokens via `var(--token-name)`. Never hardcode colors.
- Keep CSS rules tight — avoid bloated selectors. Mobile breakpoints at `max-width: 900px` and `max-width: 600px`.
- Test in your head: open in a browser, does it look professional and clean? Aim for a modern SaaS look (think Linear, Vercel, Stripe — dark, clean, slight glow, generous spacing).
