/**
 * Izbornik — sve stavke, sekcije sklopive (collapsible)
 */
(function (global) {
  const STORAGE_KEY = "pastoral_nav_sections";

  const SECTION_IDS = {
    Pregled: "pregled",
    "Župa i vjernici": "zupa",
    Liturgija: "liturgija",
    Sakramenti: "sakramenti",
    Financije: "financije",
    Isprave: "isprave",
    "Župni ured": "ured",
  };

  const DEFAULT_OPEN = {
    pregled: true,
    zupa: true,
    liturgija: true,
    sakramenti: false,
    financije: false,
    isprave: false,
    ured: false,
  };

  function loadState() {
    try {
      return { ...DEFAULT_OPEN, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") };
    } catch {
      return { ...DEFAULT_OPEN };
    }
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* ignore */
    }
  }

  function sectionIdForLabel(text) {
    return SECTION_IDS[text] || text.toLowerCase().replace(/\s+/g, "-").slice(0, 24);
  }

  function currentPageFile() {
    return location.pathname.split("/").pop() || "app.html";
  }

  function buildCollapsibleNavHtml(navItems, api) {
    const esc = api.escapeHtml;
    const pageUrl = api.pageUrl;
    const state = loadState();
    const currentFile = currentPageFile();
    let activeSectionId = "pregled";
    const sections = [];
    let current = null;

    navItems.forEach((item) => {
      if (item.type === "label") {
        if (current) sections.push(current);
        const id = sectionIdForLabel(item.text);
        current = { id, label: item.text, links: [] };
        return;
      }
      const [file, icon, label] = item;
      if (!current) {
        current = { id: "pregled", label: "Pregled", links: [] };
      }
      const href = pageUrl(file);
      const isActive = href.includes(currentFile) || file.includes(currentFile);
      if (isActive) activeSectionId = current.id;
      current.links.push({ file, icon, label, href, isActive });
    });
    if (current) sections.push(current);

    if (state[activeSectionId] === undefined) state[activeSectionId] = true;

    return sections
      .map((sec) => {
        const open = !!state[sec.id];
        const items = sec.links
          .map(
            (l) =>
              `<li><a href="${l.href}" class="${l.isActive ? "active" : ""}"><span class="nav-ico">${l.icon}</span>${esc(l.label)}</a></li>`
          )
          .join("");
        return `<li class="nav-section" data-nav-section="${sec.id}">
          <button type="button" class="nav-section-toggle" aria-expanded="${open}" data-section="${sec.id}">
            <span class="nav-section-chev" aria-hidden="true"></span>
            <span class="nav-section-title">${esc(sec.label)}</span>
          </button>
          <ul class="nav-section-items"${open ? "" : ' hidden'}>${items}</ul>
        </li>`;
      })
      .join("");
  }

  function bindCollapsibleNav(navEl) {
    if (!navEl || navEl.dataset.navBound) return;
    navEl.dataset.navBound = "1";

    navEl.addEventListener("click", (e) => {
      const btn = e.target.closest(".nav-section-toggle");
      if (!btn || !navEl.contains(btn)) return;
      const id = btn.dataset.section;
      const list = navEl.querySelector(`.nav-section[data-nav-section="${id}"] .nav-section-items`);
      const open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (list) list.hidden = !open;
      const state = loadState();
      state[id] = open;
      saveState(state);
    });
  }

  function setAllSections(open) {
    const state = {};
    Object.keys(DEFAULT_OPEN).forEach((k) => {
      state[k] = open;
    });
    saveState(state);
  }

  function mount(navEl, navItems, api) {
    if (!navEl) return;
    navEl.innerHTML = buildCollapsibleNavHtml(navItems, api);
    bindCollapsibleNav(navEl);
  }

  function injectSidebarFooterControls() {
    const foot = document.querySelector(".sidebar-footer");
    if (!foot || document.getElementById("nav-expand-all")) return;

    const wrap = document.createElement("div");
    wrap.className = "nav-footer-toggles";
    wrap.innerHTML = `
      <button type="button" class="btn btn-ghost btn-sm" id="nav-expand-all" style="flex:1">Razvij sve</button>
      <button type="button" class="btn btn-ghost btn-sm" id="nav-collapse-all" style="flex:1">Skupi sve</button>`;
    foot.insertBefore(wrap, foot.firstChild);

    wrap.querySelector("#nav-expand-all")?.addEventListener("click", () => {
      setAllSections(true);
      location.reload();
    });
    wrap.querySelector("#nav-collapse-all")?.addEventListener("click", () => {
      setAllSections(false);
      location.reload();
    });
  }

  global.PastoralSidebarNav = {
    mount,
    injectSidebarFooterControls,
    setAllSections,
    loadState,
  };
})(typeof window !== "undefined" ? window : global);
