/**
 * Vizualni polish — efekti na svim admin stranicama (automatski)
 */
(function (global) {
  const PAGE_LABELS = {
    dashboard: "Nadzorna ploča",
    nakane: "Misne nakane",
    "zupni-listic": "Župni listić",
    mise: "Raspored misa",
    krsenja: "Krštenja",
    "prva-pricest": "Prva pričest",
    krizma: "Krizma",
    vjencanja: "Vjenčanja",
    pogrebi: "Pogrebi",
    pomazanje: "Pomazanje",
    obitelji: "Obitelji",
    ulice: "Ulice",
    dugovanja: "Dugovanja",
    racuni: "Ulazni računi",
    blagajna: "Blagajna",
    "financijska-izvjestaja": "Fin. izvješća",
    formulari: "Formulari",
    potvrde: "Potvrde",
    dokumenti: "Dokumenti",
    "maticne-knjige": "Matične knjige",
    dekanat: "Dekanat i suradnja",
    "operativno-srediste": "Operativno središte",
    vijeca: "Vijeća",
    kalendar: "Događaji i zadaci",
    "javne-prijave": "Javne prijave",
    podsjetnici: "Podsjetnici",
    postavke: "Postavke",
    vjernici: "Vjernici",
  };

  const PAGE_GLYPH = {
    dashboard: "✦",
    nakane: "☩",
    "zupni-listic": "📰",
    mise: "◉",
    krsenja: "💧",
    "prva-pricest": "✞",
    krizma: "✠",
    vjencanja: "♥",
    pogrebi: "✝",
    pomazanje: "🕯",
    obitelji: "👨‍👩‍👧",
    dugovanja: "€",
    blagajna: "📒",
    kalendar: "📅",
    "javne-prijave": "📝",
    dekanat: "⇄",
    "operativno-srediste": "⌘",
  };

  let observerBound = false;
  let moTimer = null;

  function reducedMotion() {
    return global.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function homeHref() {
    const B = global.PastoralBase;
    if (B?.adminPage) return B.adminPage("app.html");
    return location.pathname.includes("/pages/") ? "../app.html" : "app.html";
  }

  function pageHref(file) {
    if (global.PastoralBase?.adminPage) {
      const f = file.startsWith("pages/") || file.startsWith("public/") ? file : `pages/${file}`;
      return global.PastoralBase.adminPage(f);
    }
    const inPages = location.pathname.includes("/pages/");
    if (inPages) return file;
    return file.startsWith("pages/") ? file : `pages/${file}`;
  }

  function injectAmbience() {
    const main = document.querySelector(".app-shell .main");
    if (!main || main.querySelector(".ui-ambience-layer")) return;
    const layer = document.createElement("div");
    layer.className = "ui-ambience-layer";
    layer.setAttribute("aria-hidden", "true");
    main.prepend(layer);
  }

  function injectContextStrip() {
    const main = document.querySelector(".app-shell .main");
    const topbar = main?.querySelector(".topbar");
    if (!topbar || main.querySelector(".ui-context-strip")) return;

    const dateStr = new Date().toLocaleDateString("hr-HR", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });

    let pills = "";
    const stats = global.PastoralApi?.readOfficeStats?.() || global.PastoralPriestTools?.getOfficeStats?.({});
    if (stats) {
      const nova = stats.nova_prijave ?? stats.novaPrijave;
      const todayN = stats.today_nakane ?? stats.todayNakane;
      const debts = stats.debts_unpaid ?? stats.debtsUnpaid;
      const deanery = stats.interparish_pending ?? stats.interparishPending ?? 0;
      const operations = stats.operations_attention ?? stats.operationsAttention ?? 0;
      const tasks = (stats.overdue_tasks ?? stats.overdueTasks ?? 0) + (stats.due_today_tasks ?? stats.dueTodayTasks ?? 0);
      if (nova > 0) {
        pills += `<a href="${pageHref("javne-prijave.html")}" class="ui-pill ui-pill--alert">Prijave <span class="ui-pill-num">${nova}</span></a>`;
      }
      if (todayN > 0) {
        pills += `<a href="${pageHref("nakane.html")}" class="ui-pill">Nakane danas <span class="ui-pill-num">${todayN}</span></a>`;
      }
      if (debts > 0) {
        pills += `<a href="${pageHref("dugovanja.html")}" class="ui-pill ui-pill--warn">Dugovanja <span class="ui-pill-num">${debts}</span></a>`;
      }
      if (tasks > 0) {
        pills += `<a href="${pageHref("kalendar.html")}" class="ui-pill">Zadaci <span class="ui-pill-num">${tasks}</span></a>`;
      }
      if (deanery > 0) {
        pills += `<a href="${pageHref("dekanat.html")}" class="ui-pill ui-pill--alert">Dekanat <span class="ui-pill-num">${deanery}</span></a>`;
      }
      if (operations > 0 && document.body.dataset.page !== "operativno-srediste") {
        pills += `<a href="${pageHref("operativno-srediste.html")}" class="ui-pill ui-pill--alert">Moj radni red <span class="ui-pill-num">${operations}</span></a>`;
      }
    }

    if (!pills) {
      pills = `<a href="${pageHref("nakane.html")}" class="ui-pill">Nakane</a>
        <a href="${pageHref("obitelji.html")}" class="ui-pill">Obitelji</a>
        <a href="${pageHref("blagajna.html")}" class="ui-pill">Blagajna</a>`;
    }

    const strip = document.createElement("div");
    strip.className = "ui-context-strip fx-scroll-reveal";
    strip.innerHTML = `<span class="ui-context-date">${dateStr}</span><div class="ui-context-pills">${pills}</div>`;
    topbar.insertAdjacentElement("afterend", strip);
    requestAnimationFrame(() => strip.classList.add("fx-scroll-reveal--in"));
  }

  function polishTopbar() {
    const topbar = document.querySelector(".app-shell .topbar");
    if (!topbar) return;
    if (!topbar.dataset.uiPolish) {
      topbar.dataset.uiPolish = "1";
      topbar.classList.add("topbar--fancy");
    }

    let head = topbar.querySelector(".topbar-head");
    const rawHead = topbar.querySelector(":scope > div:not(.topbar-actions)");
    if (!head && rawHead) {
      rawHead.classList.add("topbar-head");
      head = rawHead;
    }

    let actions = topbar.querySelector(".topbar-actions");
    if (!actions) {
      actions = document.createElement("div");
      actions.className = "topbar-actions";
      topbar.appendChild(actions);
    }

    topbar.querySelectorAll(":scope > a.btn, :scope > button.btn").forEach((el) => {
      if (el.closest("#theme-picker-root")) return;
      if (!actions.contains(el)) actions.appendChild(el);
    });
    global.PastoralTheme?.repositionInTopbar?.();

    const page = document.body.dataset.page;
    const label = PAGE_LABELS[page];
    const h1 = topbar.querySelector("h1");
    if (h1 && !h1.classList.contains("fx-topbar-title")) {
      h1.classList.add("fx-topbar-title");
      const glyph = PAGE_GLYPH[page];
      if (glyph && !h1.querySelector(".fx-topbar-glyph")) {
        const span = document.createElement("span");
        span.className = "fx-topbar-glyph";
        span.setAttribute("aria-hidden", "true");
        span.textContent = glyph;
        h1.prepend(span);
      }
    }

    if (head && label && page !== "dashboard" && !head.querySelector(".topbar-crumb")) {
      const crumb = document.createElement("p");
      crumb.className = "topbar-crumb fx-crumb-in";
      crumb.innerHTML = `<a href="${homeHref()}">Početna</a><span class="topbar-crumb-sep" aria-hidden="true">›</span><span>${label}</span>`;
      head.insertBefore(crumb, head.firstChild);
    }
  }

  function staggerCards(root) {
    if (!root || reducedMotion()) return;
    const cards = root.querySelectorAll(
      ".card:not([data-no-stagger]):not(.kpi-card--link), .public-form-card, .canon-panel, .gdpr-admin-banner"
    );
    cards.forEach((card, i) => {
      if (!card.classList.contains("fx-card-hover")) card.classList.add("fx-card-hover");
      if (card.classList.contains("ui-card-enter")) return;
      card.classList.add("ui-card-enter");
      card.style.animationDelay = `${Math.min(i * 48, 520)}ms`;
    });
  }

  function staggerTableRows(root) {
    if (!root || reducedMotion()) return;
    root.querySelectorAll(".data-table tbody").forEach((tbody) => {
      tbody.querySelectorAll("tr").forEach((tr, i) => {
        if (!tr.classList.contains("ui-row-fancy")) tr.classList.add("ui-row-fancy");
        if (tr.dataset.rowStagger) return;
        tr.dataset.rowStagger = "1";
        tr.classList.add("ui-row-stagger");
        tr.style.animationDelay = `${Math.min(i * 28, 360)}ms`;
      });
    });
  }

  function polishSectionTitles(root) {
    const scope = root || document;
    scope.querySelectorAll(".section-title").forEach((el) => {
      if (!el.classList.contains("fx-section-title")) el.classList.add("fx-section-title");
    });
  }

  function polishChipsAndTabs(root) {
    const scope = root || document;
    scope
      .querySelectorAll(
        ".debts-cat-chip, .listic-tab, .plan-tabs button, .family-tab, .table-kit-pagination button, .nav-section-toggle, .families-toolbar button, .families-active-filters button, #obitelji-new-top"
      )
      .forEach((el) => {
        if (!el.classList.contains("fx-chip-lift")) el.classList.add("fx-chip-lift");
      });
  }

  function animateKpiValues(root) {
    if (reducedMotion()) return;
    const scope = root || document;
    scope.querySelectorAll(".card-value, .kpi-card .card-value").forEach((el) => {
      if (el.dataset.kpiAnimated || el.closest("[class*='kpi-tone--']")) return;
      const raw = el.textContent.trim();
      const m = raw.match(/^(\d+)([.,](\d+))?/);
      if (!m) return;
      const target = parseInt(m[1], 10);
      if (target > 9999 || target < 0) return;
      const suffix = raw.slice(m[0].length);
      el.dataset.kpiAnimated = "1";
      el.classList.add("fx-kpi-pop");
      const start = performance.now();
      const dur = 700;
      function tick(now) {
        const t = Math.min(1, (now - start) / dur);
        const ease = 1 - Math.pow(1 - t, 3);
        el.textContent = Math.round(target * ease) + suffix;
        if (t < 1) requestAnimationFrame(tick);
        else el.textContent = raw;
      }
      requestAnimationFrame(tick);
    });
  }

  function polishBadges(root) {
    const scope = root || document;
    scope.querySelectorAll(".badge-urgent, .badge-pending").forEach((b) => {
      if (!b.classList.contains("fx-badge-glow")) b.classList.add("fx-badge-glow");
    });
  }

  function setupScrollReveal(root) {
    if (reducedMotion()) return;
    const scope = root || document;
    const nodes = scope.querySelectorAll(
      ".card.wide, .kpi-row .card:not(.kpi-card--link), .table-wrap, .listic-layout, .docs-layout, .debts-toolbar"
    );
    nodes.forEach((el) => {
      if (el.classList.contains("fx-scroll-reveal")) return;
      el.classList.add("fx-scroll-reveal");
    });

    if (!global.IntersectionObserver) {
      nodes.forEach((el) => el.classList.add("fx-scroll-reveal--in"));
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("fx-scroll-reveal--in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.06, rootMargin: "0px 0px -4% 0px" }
    );

    nodes.forEach((el) => {
      if (!el.classList.contains("fx-scroll-reveal--in")) io.observe(el);
    });
  }

  function bindDynamicObserver() {
    if (observerBound) return;
    observerBound = true;
    const targets = [document.getElementById("page-root"), document.getElementById("dashboard-root")].filter(Boolean);
    if (!targets.length) return;

    const mo = new MutationObserver(() => {
      clearTimeout(moTimer);
      moTimer = setTimeout(() => refresh(), 80);
    });

    targets.forEach((t) => mo.observe(t, { childList: true, subtree: true }));
  }

  function polishContentAreas() {
    document.body.classList.add("ui-polish-active");
    const page = document.body.dataset.page;
    if (page) document.body.classList.add(`ui-page--${page.replace(/[^a-z0-9-]/gi, "-")}`);

    document.querySelectorAll(".main .content, #dashboard-root, #page-root").forEach((el) => {
      el.classList.add("content--fancy");
      staggerCards(el);
      staggerTableRows(el);
      polishSectionTitles(el);
      polishChipsAndTabs(el);
      polishBadges(el);
      setupScrollReveal(el);
    });

    document.querySelectorAll(".data-table tbody tr").forEach((tr) => {
      if (!tr.classList.contains("ui-row-fancy")) tr.classList.add("ui-row-fancy");
    });

    document.querySelectorAll(".list-item--clickable, .list-item").forEach((li) => {
      if (!li.classList.contains("list-item--clickable")) li.classList.add("ui-list-fancy");
    });

    document.querySelectorAll(".empty-state").forEach((el) => {
      if (!el.classList.contains("ui-empty-fancy")) el.classList.add("ui-empty-fancy");
    });

    document.querySelectorAll(".form-group input, .form-group select, .form-group textarea").forEach((el) => {
      if (!el.classList.contains("ui-field-fancy")) el.classList.add("ui-field-fancy");
    });

    document.querySelectorAll(".sidebar .nav a.active").forEach((a) => {
      if (!a.classList.contains("fx-nav-active")) a.classList.add("fx-nav-active");
    });

    animateKpiValues(document.querySelector(".main"));
  }

  function enhance() {
    if (!document.querySelector(".app-shell")) return;
    injectAmbience();
    polishTopbar();
    injectContextStrip();
    polishContentAreas();
    bindDynamicObserver();
  }

  function refresh() {
    if (!document.body.classList.contains("ui-polish-active")) {
      enhance();
      return;
    }
    polishContentAreas();
    polishTopbar();
  }

  global.PastoralUiPolish = { enhance, refresh, staggerCards, PAGE_LABELS };
})(typeof window !== "undefined" ? window : global);
