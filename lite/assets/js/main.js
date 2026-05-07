(() => {
  const burger = document.querySelector('.nav-burger');
  const navLinks = document.querySelector('.nav-links');
  if (!burger || !navLinks) return;

  const setExpanded = (open) => {
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
  };
  setExpanded(navLinks.classList.contains('open'));

  burger.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    setExpanded(open);
  });

  navLinks.addEventListener('click', (e) => {
    const target = e.target;
    if (target && target.closest && target.closest('a') && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      setExpanded(false);
    }
  });
})();
