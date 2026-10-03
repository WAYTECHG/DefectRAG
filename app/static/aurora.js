// Small visual enhancements; analysis status remains driven by the existing application.
(() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reducedMotion.matches || !('IntersectionObserver' in window)) return;

  const sections = [...document.querySelectorAll('.reveal')];
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      observer.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -7% 0px', threshold: .05 });

  // Mark sections already onscreen before enabling reveal styles.
  sections.forEach((section) => {
    if (section.getBoundingClientRect().top < window.innerHeight) section.classList.add('in-view');
    observer.observe(section);
  });
  document.body.classList.add('motion-ready');

  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  document.querySelectorAll('.hero, .benchmark-grid article, .principle-grid article, .support-grid a, .hero-link, .primary-button, .secondary-button').forEach((element) => {
    element.addEventListener('pointermove', (event) => {
      const bounds = element.getBoundingClientRect();
      element.style.setProperty('--pointer-x', `${event.clientX - bounds.left}px`);
      element.style.setProperty('--pointer-y', `${event.clientY - bounds.top}px`);
    }, { passive: true });
  });
})();
