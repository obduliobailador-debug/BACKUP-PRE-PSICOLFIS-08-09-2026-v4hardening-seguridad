import { useEffect } from "react";

/**
 * Observes elements with class `.reveal` and adds `.reveal-visible` when they
 * scroll into view, powering the on-scroll fade-in animations across the site.
 */
export const useScrollReveal = () => {
  useEffect(() => {
    const observed = new WeakSet();
    const reveal = (el) => el.classList.add('reveal-visible');

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            reveal(entry.target);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    const registerTargets = () => {
      const targets = document.querySelectorAll('.reveal:not(.reveal-visible)');
      targets.forEach((el) => {
        if (!observed.has(el)) {
          observed.add(el);
          io.observe(el);
        }
      });
    };

    registerTargets();
    const interval = setInterval(registerTargets, 500);
    const stopScan = setTimeout(() => clearInterval(interval), 5000);

    return () => {
      clearInterval(interval);
      clearTimeout(stopScan);
      io.disconnect();
    };
  }, []);
};
