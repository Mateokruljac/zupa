/**
 * Križ s zoomom — pri ulasku u portal nakon prijave s login.html
 */
(function (global) {
  const ENTER_KEY = "pastoral_portal_reveal";
  const DURATION = 480;

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function scheduleAfterLogin() {
    try {
      sessionStorage.setItem(ENTER_KEY, "1");
    } catch {
      /* ignore */
    }
  }

  function shouldRunEnterReveal() {
    try {
      if (sessionStorage.getItem(ENTER_KEY) !== "1") return false;
      sessionStorage.removeItem(ENTER_KEY);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * @returns {Promise<void>}
   */
  function runEnterReveal() {
    if (prefersReducedMotion()) return Promise.resolve();

    return new Promise((resolve) => {
      const root = document.documentElement;
      root.classList.add("login-reveal-pending");

      const overlay = document.createElement("div");
      overlay.className = "login-reveal-overlay";
      overlay.setAttribute("aria-hidden", "true");
      overlay.innerHTML = `
        <div class="login-reveal-glow" aria-hidden="true"></div>
        <svg class="login-reveal-cross" viewBox="0 0 64 64" fill="none" aria-hidden="true">
          <rect x="28" y="6" width="8" height="52" rx="2" fill="currentColor"/>
          <rect x="10" y="22" width="44" height="8" rx="2" fill="currentColor"/>
        </svg>`;

      function finish() {
        overlay.classList.add("is-out");
        root.classList.remove("login-reveal-pending");
        root.classList.add("login-reveal-done");
        window.setTimeout(() => {
          overlay.remove();
          resolve();
        }, 320);
      }

      document.body.appendChild(overlay);
      requestAnimationFrame(() => overlay.classList.add("is-in"));
      window.setTimeout(finish, DURATION);
    });
  }

  function tryPortalEnterReveal() {
    if (document.body?.dataset.page === "login") return false;
    if (!document.querySelector(".app-shell")) return false;
    if (!shouldRunEnterReveal()) return false;
    runEnterReveal();
    return true;
  }

  function autoInit() {
    tryPortalEnterReveal();
  }

  global.PastoralLoginReveal = {
    ENTER_KEY,
    scheduleAfterLogin,
    runEnterReveal,
    tryPortalEnterReveal,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoInit, { once: true });
  } else {
    autoInit();
  }
})(typeof window !== "undefined" ? window : global);
