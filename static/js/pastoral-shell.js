/**
 * Django shell — sidebar layout, footer, UI polish (bez zamjene server navigacije).
 */
(function (global) {
  const SIDEBAR_COLLAPSED_KEY = "pastoral_sidebar_collapsed";

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function shellPageUrl(file) {
    return global.PastoralBase.adminPage(file);
  }

  function ensureSidebarLayout() {
    const sidebar = document.querySelector(".sidebar");
    const nav = sidebar?.querySelector(".nav");
    if (!sidebar || !nav || sidebar.querySelector(".sidebar-nav-scroll")) return;
    const scroll = document.createElement("div");
    scroll.className = "sidebar-nav-scroll";
    nav.parentNode.insertBefore(scroll, nav);
    scroll.appendChild(nav);
  }

  function ensureSidebarToggle() {
    const sidebar = document.querySelector(".sidebar");
    const toggle = document.getElementById("sidebar-toggle");
    const backdrop = document.getElementById("sidebar-backdrop");
    if (!sidebar || !toggle || toggle.dataset.bound === "1") return;
    toggle.dataset.bound = "1";

    sidebar.querySelectorAll(".nav a").forEach((link) => {
      if (!link.title) link.title = link.textContent.trim().replace(/\s+/g, " ");
    });

    const isMobile = () => global.matchMedia("(max-width: 1100px)").matches;
    const syncAria = () => {
      const expanded = isMobile()
        ? document.body.classList.contains("sidebar-mobile-open")
        : !document.body.classList.contains("sidebar-collapsed");
      toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
      toggle.setAttribute("aria-label", expanded ? "Sakrij navigaciju" : "Prikaži navigaciju");
    };
    const closeMobile = () => {
      document.body.classList.remove("sidebar-mobile-open");
      syncAria();
    };

    try {
      if (!isMobile() && localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1") {
        document.body.classList.add("sidebar-collapsed");
      }
    } catch {
      /* localStorage nije obvezan */
    }
    syncAria();

    toggle.addEventListener("click", () => {
      if (isMobile()) {
        document.body.classList.toggle("sidebar-mobile-open");
      } else {
        document.body.classList.toggle("sidebar-collapsed");
        try {
          localStorage.setItem(
            SIDEBAR_COLLAPSED_KEY,
            document.body.classList.contains("sidebar-collapsed") ? "1" : "0"
          );
        } catch {
          /* localStorage nije obvezan */
        }
      }
      syncAria();
    });
    backdrop?.addEventListener("click", closeMobile);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMobile();
    });
    global.addEventListener("resize", () => {
      if (!isMobile()) document.body.classList.remove("sidebar-mobile-open");
      syncAria();
    });
  }

  function renderAppFooter(settings) {
    const year = new Date().getFullYear();
    const s = settings || {};
    return `
    <div class="app-footer-inner">
      <div class="app-footer-col">
        <strong>${esc(s.shortName || s.name)}</strong>
        <span>${esc(s.city)} · ${esc(s.pastor)}</span>
      </div>
      <div class="app-footer-col app-footer-links">
        <a href="tel:${esc((s.phone || "").replace(/\s/g, ""))}">${esc(s.phone || "")}</a>
        <a href="mailto:${esc(s.email || "")}">${esc(s.email || "")}</a>
        <a href="${shellPageUrl("pages/obitelji.html")}">Obitelji</a>
        <a href="${shellPageUrl("public/index.html")}" target="_blank" rel="noopener">Javni obrasci</a>
        <a href="${shellPageUrl("pages/postavke.html")}">Postavke</a>
      </div>
      <div class="app-footer-col app-footer-copy">
        <span>Pastoral · ${year}</span>
      </div>
    </div>`;
  }

  function ensureAppFooter(settings) {
    const main = document.querySelector(".app-shell .main");
    if (!main) return;
    let foot = document.getElementById("app-footer");
    if (!foot) {
      foot = document.createElement("footer");
      foot.id = "app-footer";
      foot.className = "app-footer";
      main.appendChild(foot);
    }
    foot.innerHTML = renderAppFooter(settings);
  }

  function initPriestToolsLite() {
    const PT = global.PastoralPriestTools;
    if (!PT) return;
    PT.init({
      loadData: () => global.PastoralApi.load(),
      getSettings: () => global.PastoralParish?.loadSettings?.() || {},
      showToast: (msg) => {
        if (typeof global.showToast === "function") global.showToast(msg);
      },
    });
  }

  function initDjangoShell() {
    if (!document.querySelector(".app-shell")) return;
    if (document.body.dataset.djangoShell !== "1") return;
    if (document.body.dataset.shellInit === "1") return;
    document.body.dataset.shellInit = "1";

    global.PastoralParish?.applyTheme?.();
    const settings = global.PastoralParish?.loadSettings?.() || {};

    ensureSidebarLayout();
    ensureSidebarToggle();
    ensureAppFooter(settings);

    const nav = document.querySelector(".sidebar .nav");
    if (nav) nav.dataset.built = "django";

    global.PastoralNav?.init?.();

    const needsData = document.body.dataset.needsParishData === "1";
    if (needsData) global.PastoralApi?.ensureLoaded?.().catch(() => {});

    initPriestToolsLite();

    if (global.PastoralTheme) global.PastoralTheme.initThemePicker();

    global.PastoralUiPolish?.enhance?.();
  }

  global.PastoralShell = {
    ensureSidebarLayout,
    ensureAppFooter,
    initDjangoShell,
    shellPageUrl,
  };

  /* --- pastoral-nav (sklopive sekcije) --- */
  const NAV_STORAGE_KEY = "pastoral_nav_sections";
  const NAV_DEFAULT_OPEN = {
    pregled: true,
    zupa: true,
    liturgija: true,
    sakramenti: false,
    financije: false,
    isprave: false,
    suradnja: true,
    ured: true,
  };

  function navLoadState() {
    try {
      return { ...NAV_DEFAULT_OPEN, ...JSON.parse(localStorage.getItem(NAV_STORAGE_KEY) || "{}") };
    } catch {
      return { ...NAV_DEFAULT_OPEN };
    }
  }

  function navSaveState(state) {
    try {
      localStorage.setItem(NAV_STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* ignore */
    }
  }

  function bindCollapsibleNav(navEl) {
    if (!navEl || navEl.dataset.navBound) return;
    navEl.dataset.navBound = "1";
    const state = navLoadState();
    navEl.querySelectorAll(".nav-section").forEach((sec) => {
      const id = sec.dataset.navSection;
      const btn = sec.querySelector(".nav-section-toggle");
      const list = sec.querySelector(".nav-section-items");
      const open = state[id] !== false;
      if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (list) list.hidden = !open;
    });
    navEl.addEventListener("click", (e) => {
      const btn = e.target.closest(".nav-section-toggle");
      if (!btn || !navEl.contains(btn)) return;
      const id = btn.dataset.section;
      const list = navEl.querySelector(`.nav-section[data-nav-section="${id}"] .nav-section-items`);
      const open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (list) list.hidden = !open;
      const next = navLoadState();
      next[id] = open;
      navSaveState(next);
    });
  }

  function bindNavigationVisibilityControls() {
    const expandAllButton = document.getElementById("nav-expand-all");
    const collapseAllButton = document.getElementById("nav-collapse-all");
    if (!expandAllButton || !collapseAllButton) return;

    expandAllButton.addEventListener("click", () => {
      const expandedNavigationState = {};
      Object.keys(NAV_DEFAULT_OPEN).forEach((sectionIdentifier) => {
        expandedNavigationState[sectionIdentifier] = true;
      });
      navSaveState(expandedNavigationState);
      location.reload();
    });
    collapseAllButton.addEventListener("click", () => {
      const collapsedNavigationState = {};
      Object.keys(NAV_DEFAULT_OPEN).forEach((sectionIdentifier) => {
        collapsedNavigationState[sectionIdentifier] = false;
      });
      navSaveState(collapsedNavigationState);
      location.reload();
    });
  }

  function initNav() {
    const nav = document.getElementById("sidebar-nav");
    bindCollapsibleNav(nav);
    bindNavigationVisibilityControls();
  }

  global.PastoralNav = { init: initNav, loadState: navLoadState, saveState: navSaveState };

  /* --- UI init (tema + shell) --- */
  document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.dataset.page;
    const isLogin = page === "login";
    if (document.body.dataset.djangoShell === "1") {
      initDjangoShell();
    } else if (window.PastoralTheme) {
      window.PastoralTheme.initThemePicker({ fixed: isLogin });
    }
  });
})(typeof window !== "undefined" ? window : global);
