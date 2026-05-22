/**
 * Uvod — kretanje kroz ekrane (prva prijava + ponovno iz Postavki)
 */
(function (global) {
  const STORAGE_KEY = "pastoral_onboarding_v1";

  let api = null;
  let stepIndex = 0;
  let overlayEl = null;
  let active = false;

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function saveState(patch) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...loadState(), ...patch }));
  }

  function isCompleted() {
    const s = loadState();
    return !!(s.completed || s.skippedAll);
  }

  function currentPageId() {
    return document.body.dataset.page || "dashboard";
  }

  function pageMatches(step) {
    if (!step.page) return true;
    if (step.page === "dashboard") return currentPageId() === "dashboard";
    return currentPageId() === step.page;
  }

  function buildSteps() {
    const p = (file) => api.pageUrl(file);
    return [
      {
        type: "welcome",
        page: "dashboard",
        short: "Start",
        label: "Uvod",
        title: "Dobrodošli u Pastoral",
        text: "Provest ćemo vas kroz glavne ekrane župnog ureda. Možete preskočiti bilo koji ekran ili cijeli obilazak.",
      },
      {
        type: "screen",
        page: "dashboard",
        url: p("app.html"),
        short: "Ploča",
        label: "Nadzorna ploča",
        title: "Ekran: Nadzorna ploča",
        text: "Ovdje počinjete svaki dan: brzi pristup, brojke za danas, nakane i zadatke.",
        focus: "#dashboard-root",
        navHighlight: 'a[href*="app.html"]',
      },
      {
        type: "screen",
        page: "obitelji",
        url: p("pages/obitelji.html"),
        short: "Obitelji",
        label: "Obitelji",
        title: "Ekran: Obitelji",
        text: "Tablica domaćinstava — klik na red otvara karton u modalu (zatvaranje na ×).",
        focus: "#page-root",
        navHighlight: 'a[href*="obitelji"]',
      },
      {
        type: "screen",
        page: "ulice",
        url: p("pages/ulice.html"),
        short: "Ulice",
        label: "Ulice",
        title: "Ekran: Ulice",
        text: "Pregled po ulicama i kvartovima za obilazak i planiranje.",
        focus: "#page-root",
        navHighlight: 'a[href*="ulice"]',
      },
      {
        type: "screen",
        page: "nakane",
        url: p("pages/nakane.html"),
        short: "Nakane",
        label: "Misne nakane",
        title: "Ekran: Kalendar nakana",
        text: "Kalendar po danima i upis nakana. Odaberite dan, zatim „+ Nova nakana”.",
        focus: "#nakane-calendar, #nakane-day-panel",
        navHighlight: 'a[href*="nakane"]',
      },
      {
        type: "screen",
        page: "mise",
        url: p("pages/mise.html"),
        short: "Mise",
        label: "Raspored misa",
        title: "Ekran: Raspored misa",
        text: "Tjedni raspored misa — nakane se vežu uz sat u kalendaru.",
        focus: "#page-root",
        navHighlight: 'a[href*="mise"]',
      },
      {
        type: "screen",
        page: "krsenja",
        url: p("pages/krsenja.html"),
        short: "Krštenja",
        label: "Krštenja",
        title: "Ekran: Krštenja",
        text: "Isto za prvu pričest, krizmu, vjenčanja i pogrebe — tablica i unos u modalu.",
        focus: "#page-root",
        navHighlight: 'a[href*="krsenja"]',
      },
      {
        type: "screen",
        page: "krizma",
        url: p("pages/krizma.html"),
        short: "Krizma",
        label: "Krizma",
        title: "Ekran: Krizma",
        text: "Krizmanici po godini, katehete, uvoz i ispis dokumenata.",
        focus: "#page-root",
        navHighlight: 'a[href*="krizma"]',
      },
      {
        type: "screen",
        page: "dugovanja",
        url: p("pages/dugovanja.html"),
        short: "Dug.",
        label: "Dugovanja",
        title: "Ekran: Dugovanja",
        text: "Pregled svih neplaćenih stavki — lukno, nakane, sakramenti — filtrirajte po kategoriji i godini.",
        focus: "#page-root",
        navHighlight: 'a[href*="dugovanja"]',
      },
      {
        type: "screen",
        page: "javne-prijave",
        url: p("pages/javne-prijave.html"),
        short: "Prijave",
        label: "Javne prijave",
        title: "Ekran: Javne prijave",
        text: "Prijave s weba — „U evidenciju” prenosi u registar.",
        focus: "#page-root",
        navHighlight: 'a[href*="javne-prijave"]',
      },
      {
        type: "screen",
        page: "dokumenti",
        url: p("pages/dokumenti.html"),
        short: "Dok.",
        label: "Dokumenti",
        title: "Ekran: Dokumenti",
        text: "Predlošci, Excel/CSV i ispis (npr. pristupnice).",
        focus: "#page-root",
        navHighlight: 'a[href*="dokumenti"]',
      },
      {
        type: "screen",
        page: "zadaci",
        url: p("pages/zadaci.html"),
        short: "Zadaci",
        label: "Zadaci",
        title: "Ekran: Zadaci",
        text: "Podsjetnici za župni ured i sastanke.",
        focus: "#page-root",
        navHighlight: 'a[href*="zadaci"]',
      },
      {
        type: "screen",
        page: "postavke",
        url: p("pages/postavke.html"),
        short: "Post.",
        label: "Postavke",
        title: "Ekran: Postavke",
        text: "Podaci župe, boje i „Ponovi uvod u aplikaciju”.",
        focus: ".main .content, #page-root",
        navHighlight: 'a[href*="postavke"]',
      },
      {
        type: "finish",
        page: "any",
        short: "Kraj",
        label: "Gotovo",
        title: "Obilazak završen",
        text: "Sada znate gdje je što. Pretraga: Ctrl+K, pomoć: ?, ispis za danas u traci.",
      },
    ];
  }

  function getSteps() {
    return buildSteps();
  }

  function screenStepsOnly() {
    return getSteps().filter((s) => s.type === "screen");
  }

  function clearHighlights() {
    document.querySelectorAll(".onboarding-target").forEach((el) => el.classList.remove("onboarding-target"));
    document.querySelectorAll(".onboarding-nav-active").forEach((el) => el.classList.remove("onboarding-nav-active"));
    document.querySelector(".main")?.classList.remove("onboarding-main-highlight");
    document.querySelector(".sidebar")?.classList.remove("onboarding-sidebar-dim");
  }

  function teardown() {
    active = false;
    clearHighlights();
    overlayEl?.remove();
    overlayEl = null;
    document.body.classList.remove("onboarding-active", "onboarding-screen-mode", "onboarding-modal-mode");
    document.removeEventListener("keydown", onKeydown);
  }

  /** Ukloni ostatke overlaya / body klasa ako obilazak nije aktivan */
  function ensureCleanupIfDone() {
    const state = loadState();
    if (state.completed || state.skippedAll) {
      teardown();
      return;
    }
    if (!state.inProgress && !active) {
      document.body.classList.remove("onboarding-active", "onboarding-screen-mode", "onboarding-modal-mode");
      clearHighlights();
      overlayEl?.remove();
      overlayEl = null;
    }
  }

  function finishTour(skippedAll) {
    saveState({
      completed: true,
      inProgress: false,
      step: 0,
      skippedAll: !!skippedAll,
      completedAt: new Date().toISOString(),
    });
    teardown();
    api?.showToast(skippedAll ? "Obilazak preskočen — pomoć je pod ?" : "Obilazak završen — sretan rad!");
  }

  function goToStep(index) {
    const steps = getSteps();
    if (index >= steps.length) {
      finishTour(false);
      return;
    }
    if (index < 0) return;
    stepIndex = index;
    saveState({ step: stepIndex, completed: false, inProgress: true });
    runStep();
  }

  function nextStep() {
    const steps = getSteps();
    const step = steps[stepIndex];
    if (step?.type === "welcome") {
      saveState({ inProgress: true, step: 1 });
    }
    goToStep(stepIndex + 1);
  }

  function prevStep() {
    goToStep(stepIndex - 1);
  }

  function skipStep() {
    nextStep();
  }

  function navigateToStep(step) {
    saveState({ step: stepIndex, completed: false, inProgress: true });
    sessionStorage.setItem("pastoral_onb_transition", step.label || step.title);
    location.href = step.url;
  }

  function showTransitionBanner() {
    const msg = sessionStorage.getItem("pastoral_onb_transition");
    if (!msg) return;
    sessionStorage.removeItem("pastoral_onb_transition");
    const el = document.createElement("div");
    el.className = "onboarding-transition";
    el.innerHTML = `<div class="onboarding-transition-inner"><span class="onboarding-transition-spin"></span> Otvaramo: <strong>${esc(msg)}</strong></div>`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 900);
  }

  function renderStepper(total) {
    const steps = getSteps();
    return `
      <div class="onboarding-stepper" role="tablist" aria-label="Ekrani obilaska">
        ${steps
          .map((s, i) => {
            const cls = [
              "onboarding-stepper-item",
              i === stepIndex ? "is-current" : "",
              i < stepIndex ? "is-done" : "",
              s.type === "welcome" || s.type === "finish" ? "is-meta" : "",
            ]
              .filter(Boolean)
              .join(" ");
            return `<span class="${cls}" title="${esc(s.label || s.short)}"><span class="onboarding-stepper-dot"></span><span class="onboarding-stepper-label">${esc(s.short || "")}</span></span>`;
          })
          .join("")}
      </div>`;
  }

  function renderChrome(step, total) {
    const n = stepIndex + 1;
    const isLast = step.type === "finish" || n >= total;
    const screenNum =
      step.type === "screen" ? screenStepsOnly().findIndex((s) => s.page === step.page) + 1 : 0;
    const eyebrow =
      step.type === "screen"
        ? `Ekran ${screenNum} od ${screenStepsOnly().length} · Korak ${n} / ${total}`
        : `Korak ${n} / ${total}`;

    return `
      <footer class="onboarding-chrome">
        ${renderStepper(total)}
        <div class="onboarding-chrome-body">
          <div class="onboarding-chrome-text">
            <span class="onboarding-screen-eyebrow">${eyebrow}</span>
            <h3 class="onboarding-chrome-title">${esc(step.title)}</h3>
            <p class="onboarding-chrome-desc">${esc(step.text)}</p>
          </div>
          <div class="onboarding-chrome-actions">
            ${stepIndex > 0 ? '<button type="button" class="btn btn-ghost btn-sm" data-onb-prev>← Prethodni</button>' : ""}
            <button type="button" class="btn btn-ghost btn-sm" data-onb-skip-step">Preskoči</button>
            <button type="button" class="btn btn-ghost btn-sm" data-onb-skip-all>Završi obilazak</button>
            <button type="button" class="btn btn-primary" data-onb-next>${isLast ? "Započni rad" : "Sljedeći ekran →"}</button>
          </div>
        </div>
      </footer>`;
  }

  function bindChromeEvents() {
    overlayEl?.querySelector("[data-onb-next]")?.addEventListener("click", () => nextStep());
    overlayEl?.querySelector("[data-onb-prev]")?.addEventListener("click", () => prevStep());
    overlayEl?.querySelector("[data-onb-skip-step]")?.addEventListener("click", () => skipStep());
    overlayEl?.querySelector("[data-onb-skip-all]")?.addEventListener("click", () => finishTour(true));
  }

  function highlightNav(selector) {
    document.querySelectorAll(".onboarding-nav-active").forEach((el) => el.classList.remove("onboarding-nav-active"));
    if (!selector) return;
    const link = document.querySelector(`.sidebar .nav ${selector}`);
    if (link) link.classList.add("onboarding-nav-active");
  }

  function applyScreenHighlight(step) {
    clearHighlights();
    const main = document.querySelector(".main");
    const sidebar = document.querySelector(".sidebar");
    if (main) main.classList.add("onboarding-main-highlight");
    if (sidebar) sidebar.classList.add("onboarding-sidebar-dim");
    highlightNav(step.navHighlight);

    if (step.focus) {
      const parts = step.focus.split(",").map((s) => s.trim());
      for (const sel of parts) {
        const el = document.querySelector(sel);
        if (el) {
          el.classList.add("onboarding-target");
          el.scrollIntoView({ block: "nearest", behavior: "smooth" });
          break;
        }
      }
    }
  }

  function renderWelcomeOrFinish(step, total) {
    teardown();
    active = true;
    document.body.classList.add("onboarding-active", "onboarding-modal-mode");

    overlayEl = document.createElement("div");
    overlayEl.className = "onboarding-overlay onboarding-overlay--modal";
    overlayEl.innerHTML = `
      <div class="onboarding-backdrop" data-onb-backdrop></div>
      <div class="onboarding-modal-card">
        ${renderStepper(total)}
        <div class="onboarding-modal-body">
          <h2 class="onboarding-modal-title">${esc(step.title)}</h2>
          <p class="onboarding-modal-text">${esc(step.text)}</p>
          ${step.type === "welcome" ? `<p class="card-sub">Obilazak: ${screenStepsOnly().length} ekrana, oko 2 minute.</p>` : ""}
        </div>
        <div class="onboarding-modal-actions">
          ${step.type === "finish" ? "" : stepIndex > 0 ? '<button type="button" class="btn btn-ghost" data-onb-prev>← Natrag</button>' : ""}
          ${step.type === "welcome" ? '<button type="button" class="btn btn-ghost" data-onb-skip-all>Preskoči obilazak</button>' : ""}
          <button type="button" class="btn btn-primary" data-onb-next>${step.type === "finish" ? "Započni rad" : "Kreni kroz ekrane →"}</button>
        </div>
      </div>`;
    document.body.appendChild(overlayEl);
    bindChromeEvents();
    document.addEventListener("keydown", onKeydown);
  }

  function renderScreenStep(step, total) {
    teardown();
    active = true;
    document.body.classList.add("onboarding-active", "onboarding-screen-mode");

    overlayEl = document.createElement("div");
    overlayEl.className = "onboarding-overlay onboarding-overlay--screen";
    overlayEl.innerHTML = renderChrome(step, total);
    document.body.appendChild(overlayEl);

    applyScreenHighlight(step);
    bindChromeEvents();
    document.addEventListener("keydown", onKeydown);
  }

  function runStep() {
    const steps = getSteps();
    const step = steps[stepIndex];
    if (!step) {
      finishTour(false);
      return;
    }

    if (step.type === "welcome" || step.type === "finish") {
      if (step.type === "welcome" && !pageMatches({ page: "dashboard" })) {
        navigateToStep({ ...step, url: api.pageUrl("app.html"), label: step.label });
        return;
      }
      renderWelcomeOrFinish(step, steps.length);
      return;
    }

    if (step.type === "screen") {
      if (!pageMatches(step)) {
        navigateToStep(step);
        return;
      }
      renderScreenStep(step, steps.length);
      return;
    }

    nextStep();
  }

  function onKeydown(e) {
    if (!active) return;
    if (e.key === "Escape") finishTour(true);
    if (e.key === "Enter" && !e.shiftKey) {
      const tag = document.activeElement?.tagName;
      if (tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") nextStep();
    }
  }

  function start(fromStep) {
    if (isCompleted() && fromStep === undefined) return false;
    stepIndex = typeof fromStep === "number" ? fromStep : 0;
    const prev = loadState();
    const inProgress = prev.inProgress === true || (typeof fromStep === "number" && fromStep > 0);
    saveState({ completed: false, step: stepIndex, inProgress });
    runStep();
    return true;
  }

  function resumeIfNeeded() {
    const state = loadState();
    if (state.completed || state.skippedAll) return false;
    if (!state.inProgress) return false;
    if (typeof state.step !== "number") return false;

    showTransitionBanner();
    stepIndex = state.step;
    active = true;
    setTimeout(() => runStep(), 400);
    return true;
  }

  function maybeStartOnFirstVisit() {
    const state = loadState();
    if (state.completed || state.skippedAll) return false;

    if (state.inProgress) return resumeIfNeeded();

    if (state.started) return false;

    saveState({ started: true, step: 0, completed: false, inProgress: false });
    stepIndex = 0;
    if (currentPageId() !== "dashboard") {
      sessionStorage.setItem("pastoral_onb_transition", "Nadzorna ploča");
      location.href = api.pageUrl("app.html") + "?onboarding=1";
      return true;
    }
    setTimeout(() => start(0), 600);
    return true;
  }

  function reset() {
    localStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem("pastoral_onb_transition");
    teardown();
    api?.showToast("Obilazak resetiran");
  }

  function restart() {
    saveState({ completed: false, started: true, step: 0, skippedAll: false, inProgress: true });
    sessionStorage.setItem("pastoral_onb_transition", "Nadzorna ploča");
    location.href = api.pageUrl("app.html") + "?onboarding=restart";
  }

  global.PastoralOnboarding = {
    init(hooks) {
      api = hooks;
    },
    isCompleted,
    ensureCleanupIfDone,
    start,
    resumeIfNeeded,
    maybeStartOnFirstVisit,
    reset,
    restart,
    finishTour,
    teardown,
  };
})(typeof window !== "undefined" ? window : global);
