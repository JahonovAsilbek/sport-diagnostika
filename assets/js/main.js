(() => {
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const burger = $('.nav-burger');
  const navLinks = $('.nav-links');
  if (burger && navLinks) {
    const closeMenu = () => {
      navLinks.classList.remove('open');
      burger.setAttribute('aria-expanded', 'false');
    };
    burger.addEventListener('click', () => {
      const isOpen = navLinks.classList.toggle('open');
      burger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
    $$('a', navLinks).forEach((a) => {
      a.addEventListener('click', () => {
        if (navLinks.classList.contains('open')) closeMenu();
      });
    });
  }

  const header = $('.site-header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  const stats = $('.stats');
  const statNums = $$('.stat-num');
  if (stats && statNums.length) {
    const easeOutQuad = (t) => 1 - (1 - t) * (1 - t);
    const animateNum = (el) => {
      const raw = el.textContent.trim();
      const match = raw.match(/^(\d+)(.*)$/);
      if (!match) return;
      const target = parseInt(match[1], 10);
      const suffix = match[2] || '';
      if (reduceMotion) {
        el.textContent = target + suffix;
        return;
      }
      const duration = 1100;
      const start = performance.now();
      const tick = (now) => {
        const t = Math.min(1, (now - start) / duration);
        const v = Math.round(target * easeOutQuad(t));
        el.textContent = v + (t === 1 ? suffix : '');
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    const statObserver = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          statNums.forEach(animateNum);
          obs.disconnect();
        }
      });
    }, { threshold: 0.3 });
    statObserver.observe(stats);
  }

  const revealEls = $$('[data-reveal]');
  if (revealEls.length) {
    if (reduceMotion) {
      revealEls.forEach((el) => el.classList.add('in-view'));
    } else {
      const revealObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
            obs.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12 });
      revealEls.forEach((el) => revealObserver.observe(el));
    }
  }
})();
