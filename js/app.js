/**
 * Pastoral — jedna župa, administracija
 */
function loadCanonComplianceScript() {
  if (window.PastoralCanon) return Promise.resolve();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/canon-compliance.js" : "js/canon-compliance.js";
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
}

function loadGdprEngine() {
  if (window.PastoralGdpr) return Promise.resolve();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/gdpr-engine.js" : "js/gdpr-engine.js";
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
}

function loadUiPolish() {
  if (window.PastoralUiPolish) return Promise.resolve();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/ui-polish.js" : "js/ui-polish.js";
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
}

function loadKpiTheme() {
  if (window.PastoralKpi) return Promise.resolve();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/kpi-theme.js" : "js/kpi-theme.js";
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
}

function loadChartJs() {
  if (window.PastoralChartLoader) return window.PastoralChartLoader.loadChartJs();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/chart-loader.js" : "js/chart-loader.js";
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => (window.PastoralChartLoader ? window.PastoralChartLoader.loadChartJs().then(resolve).catch(resolve) : resolve());
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
}

function loadAnalyticsEngine() {
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/analytics-engine.js" : "js/analytics-engine.js";
  return loadChartJs().then(
    () =>
      new Promise((resolve) => {
        if (window.PastoralAnalytics) {
          resolve();
          return;
        }
        const s = document.createElement("script");
        s.src = src;
        s.onload = () => resolve();
        s.onerror = () => resolve();
        document.head.appendChild(s);
      })
  );
}

function loadSidebarNav() {
  if (window.PastoralSidebarNav) return Promise.resolve();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/sidebar-nav-engine.js" : "js/sidebar-nav-engine.js";
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
}

function dashQuickActionsHtml(d) {
  const today = new Date().toISOString().slice(0, 10);
  const novaPrijave = (d.publicSubmissions || []).filter((s) => s.status === "nova").length;
  const dateLabel = new Date().toLocaleDateString("hr-HR", { weekday: "long", day: "numeric", month: "long" });
  return `
    <section class="card wide dash-welcome ui-card-enter" data-no-stagger>
      <h2 class="section-title" style="margin-top:0">${escapeHtml(dateLabel)}</h2>
      <p class="card-sub">Brzi ulaz — puni pregled i svi moduli su u izborniku lijevo (sekcije se mogu sklopiti).</p>
      <div class="dash-quick-grid">
        <a href="${pageUrl("pages/nakane.html")}" class="dash-quick-btn dash-quick-btn--primary fx-card-hover">
          <span class="dash-quick-ico">☩</span><span>Misne nakane</span>
        </a>
        <a href="${pageUrl("pages/obitelji.html")}" class="dash-quick-btn fx-card-hover">
          <span class="dash-quick-ico">👨‍👩‍👧</span><span>Obitelji</span>
        </a>
        <a href="${pageUrl("pages/javne-prijave.html")}" class="dash-quick-btn fx-card-hover">
          <span class="dash-quick-ico">📝</span><span>Prijave${novaPrijave ? ` (${novaPrijave})` : ""}</span>
        </a>
        <a href="${pageUrl("pages/blagajna.html")}" class="dash-quick-btn fx-card-hover">
          <span class="dash-quick-ico">📒</span><span>Blagajna</span>
        </a>
      </div>
    </section>`;
}

const NAV = [
  { type: "label", text: "Pregled" },
  ["app.html", "⊞", "Nadzorna ploča"],
  ["pages/admin-paket.html", "📚", "Uredbe i dokumentacija"],
  { type: "label", text: "Župa i vjernici" },
  ["pages/podsjetnici.html", "🔔", "Podsjetnici"],
  ["pages/obitelji.html", "👨‍👩‍👧", "Obitelji"],
  ["pages/posjete.html", "🏠", "Posjete"],
  ["pages/ulice.html", "🛣", "Ulice"],
  { type: "label", text: "Liturgija" },
  ["pages/nakane.html", "☩", "Misne nakane"],
  ["pages/mise.html", "◉", "Raspored misa"],
  ["pages/zupni-listic.html", "📰", "Župni listić"],
  { type: "label", text: "Sakramenti" },
  ["pages/krsenja.html", "💧", "Krštenja"],
  ["pages/prva-pricest.html", "✞", "Prva pričest"],
  ["pages/krizma.html", "✠", "Krizma"],
  ["pages/vjencanja.html", "♥", "Vjenčanja"],
  ["pages/pogrebi.html", "✝", "Pogrebi"],
  ["pages/pomazanje.html", "🕯", "Pomazanje"],
  { type: "label", text: "Financije" },
  ["pages/dugovanja.html", "€", "Dugovanja"],
  ["pages/racuni.html", "🧾", "Računi"],
  ["pages/blagajna.html", "📒", "Blagajna"],
  ["pages/financijska-izvjestaja.html", "📊", "Fin. izvješća"],
  { type: "label", text: "Isprave" },
  ["pages/formulari.html", "🖨", "Formulari (ispis)"],
  ["pages/potvrde.html", "📜", "Potvrde"],
  ["pages/dokumenti.html", "📄", "Dokumenti (Excel)"],
  ["pages/maticne-knjige.html", "📖", "Matične knjige"],
  { type: "label", text: "Župni ured" },
  ["pages/vijeca.html", "👥", "Vijeća ŽPV/ŽEV"],
  ["pages/kalendar.html", "📅", "Događaji"],
  ["pages/zadaci.html", "📋", "Zadaci"],
  ["pages/javne-prijave.html", "📝", "Javne prijave"],
  ["pages/komunikacija.html", "✉", "Obavijesti"],
  ["pages/poruke.html", "💬", "Poruke ureda"],
  ["pages/korisnici.html", "👤", "Korisnici i grupe"],
  ["pages/postavke.html", "⚙", "Postavke"],
  ["pages/sigurnost.html", "🛡", "Sigurnost"],
];

let calendarMonth = new Date();
let selectedCalendarDay = null;
let nakaneTableSort = { key: "date", dir: "asc" };
let nakaneTableFilter = { search: "", status: "all" };
let nakaneCharts = [];

const NAKANE_VIEW_MODES = ["today", "calendar", "evidence"];

function getNakaneViewMode() {
  try {
    const m = sessionStorage.getItem("nakane-view-mode");
    if (NAKANE_VIEW_MODES.includes(m)) return m;
  } catch {
    /* ignore */
  }
  return "today";
}

function applyNakaneViewMode() {
  const layout = document.querySelector(".nakane-layout");
  if (!layout) return;
  const mode = getNakaneViewMode();
  layout.classList.remove("nakane-mode-today", "nakane-mode-calendar", "nakane-mode-evidence");
  layout.classList.add(`nakane-mode-${mode}`);
}

function setNakaneViewMode(mode, opts = {}) {
  if (!NAKANE_VIEW_MODES.includes(mode)) return;
  try {
    sessionStorage.setItem("nakane-view-mode", mode);
  } catch {
    /* ignore */
  }
  if (mode === "today") {
    selectedCalendarDay = new Date().toISOString().slice(0, 10);
    calendarMonth = new Date();
  }
  applyNakaneViewMode();
  refreshNakanePage();
  if (opts.scrollTo) {
    requestAnimationFrame(() => {
      document.getElementById(opts.scrollTo)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
}

function getNakaneDaySummary(iso) {
  const list = getData().intentions.filter((n) => n.date === iso);
  return { list, count: list.length, unpaid: list.filter((n) => !n.paid).length };
}

function getNextMassHint(iso, list) {
  if (window.PastoralMise?.getNextMassHint) {
    return window.PastoralMise.getNextMassHint(getData(), iso);
  }
  const today = new Date().toISOString().slice(0, 10);
  if (iso !== today) return "";
  const d = getData();
  const schedule = [...(d.massSchedule || []).map((m) => m.time), "07:30", "09:00", "11:00", "18:00"].filter(
    (v, i, a) => a.indexOf(v) === i
  );
  const nowMins = new Date().getHours() * 60 + new Date().getMinutes();
  const toMins = (t) => {
    const [h, m] = String(t || "0:0").split(":").map(Number);
    return h * 60 + m;
  };
  const upcoming = schedule.filter((t) => toMins(t) >= nowMins - 30).sort((a, b) => toMins(a) - toMins(b))[0];
  if (!upcoming) return "Sve mise za danas su prošle.";
  const massCount = list.filter((n) => n.massTime === upcoming).length;
  return `Sljedeća misa: ${upcoming} — ${massCount} nakana`;
}

function mountNakaneCommandBar() {
  const layout = document.querySelector(".nakane-layout");
  if (!layout || document.getElementById("nakane-command-bar")) return;
  const bar = document.createElement("section");
  bar.id = "nakane-command-bar";
  bar.className = "card nakane-command-bar";
  layout.insertBefore(bar, layout.firstChild);
}

function renderNakaneCommandBar() {
  mountNakaneCommandBar();
  const bar = document.getElementById("nakane-command-bar");
  if (!bar) return;
  const mode = getNakaneViewMode();
  const today = new Date().toISOString().slice(0, 10);
  if (mode === "today") selectedCalendarDay = today;
  const activeIso = mode === "today" ? today : selectedCalendarDay || today;
  const { count, unpaid, list } = getNakaneDaySummary(activeIso);
  const pageStats = mode === "evidence" ? computeNakanePageStats(getData()) : null;
  const nextHint =
    mode === "today" || activeIso === today ? getNextMassHint(mode === "today" ? today : activeIso, list) : "";

  const metaBlock =
    mode === "evidence"
      ? `<strong class="nakane-command-date">Evidencija</strong>
         <span class="card-sub">${pageStats.total} nakana · ${pageStats.unpaid} neplaćeno · ${pageStats.stipendTotal} €</span>`
      : `<strong class="nakane-command-date">${escapeHtml(fmtDate(activeIso))}</strong>
         <span class="card-sub">${count} nakana${unpaid ? ` · ${unpaid} neplaćeno` : ""}</span>
         ${nextHint ? `<span class="nakane-next-mass">${escapeHtml(nextHint)}</span>` : ""}`;

  bar.innerHTML = `
    <div class="nakane-command-inner">
      <div class="nakane-mode-tabs" role="tablist" aria-label="Prikaz nakana">
        ${[
          ["today", "Danas"],
          ["calendar", "Kalendar"],
          ["evidence", "Evidencija"],
        ]
          .map(
            ([id, label]) =>
              `<button type="button" class="nakane-mode-tab${mode === id ? " is-active" : ""}" data-nakane-mode="${id}" role="tab" aria-selected="${mode === id}">${label}</button>`
          )
          .join("")}
      </div>
      <div class="nakane-command-meta">${metaBlock}</div>
      <div class="nakane-command-actions">
        ${mode !== "evidence" ? `<button type="button" class="btn btn-secondary btn-sm" id="nakane-cmd-print">🖨 Ispis</button>` : ""}
        <button type="button" class="btn btn-primary btn-sm" id="nakane-cmd-add">+ Nova nakana</button>
      </div>
    </div>`;

  bar.querySelectorAll("[data-nakane-mode]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = btn.dataset.nakaneMode;
      setNakaneViewMode(next, { scrollTo: next === "evidence" ? "nakane-evidence" : "nakane-workspace" });
    });
  });
  bar.querySelector("#nakane-cmd-print")?.addEventListener("click", () => printNakaneDay(activeIso));
  bar.querySelector("#nakane-cmd-add")?.addEventListener("click", () => {
    if (mode === "evidence" && !selectedCalendarDay) selectedCalendarDay = today;
    window.PastoralCrudModals?.openNakana(refreshNakanePage);
  });
}

function goToNakaneToday() {
  setNakaneViewMode("today", { scrollTo: "nakane-workspace" });
}

function normNakanaText(s) {
  return String(s ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function findNakanaDuplicates(data, fields, excludeId) {
  const sameMass = (data.intentions || []).filter(
    (n) => n.id !== excludeId && n.date === fields.date && n.massTime === fields.massTime
  );
  if (!sameMass.length) return null;
  const sameText = sameMass.filter((n) => normNakanaText(n.intentionFor) === normNakanaText(fields.intentionFor));
  const req = normNakanaText(fields.requestedBy);
  const sameTextAndRequester =
    req && sameText.filter((n) => normNakanaText(n.requestedBy) === req);
  return { sameMass, sameText, sameTextAndRequester };
}

async function confirmNakanaIfDuplicate(fields, excludeId) {
  const dup = findNakanaDuplicates(getData(), fields, excludeId);
  if (!dup) return true;
  let message = `Za misu u ${fields.massTime} već postoji ${dup.sameMass.length} nakana toga dana.`;
  if (dup.sameText.length) {
    message += `\n\nIsta namjera („${fields.intentionFor}”) već je upisana ${dup.sameText.length}× na tu misu.`;
  }
  if (dup.sameTextAndRequester?.length) {
    message += `\n\nIsti naručitelj (${fields.requestedBy}) s istom namjerom — vjerojatno duplikat.`;
  }
  message += "\n\nSvejedno spremiti?";
  return modalConfirm(message, { title: "Upozorenje — mogući duplikat" });
}

function updateNakana(id, fields) {
  const data = getData();
  const row = data.intentions.find((n) => n.id === id);
  if (!row) return false;
  row.date = fields.date;
  row.massTime = fields.massTime;
  row.intentionFor = fields.intentionFor;
  row.requestedBy = fields.requestedBy || "";
  row.stipend = Number(fields.stipend) || 0;
  row.notes = fields.notes || "";
  saveData(data);
  return true;
}

function printNakaneDay(iso, massTimeFilter) {
  const settings = window.PastoralParish?.loadSettings?.() || {};
  const dateLabel = new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  let list = getData().intentions.filter((n) => n.date === iso);
  if (massTimeFilter) list = list.filter((n) => n.massTime === massTimeFilter);
  list = list.slice().sort((a, b) => String(a.massTime || "").localeCompare(String(b.massTime || "")));
  const title = massTimeFilter ? `Nakane — ${dateLabel} · misa ${massTimeFilter}` : `Nakane — ${dateLabel}`;

  const html = `<!DOCTYPE html><html lang="hr"><head><meta charset="UTF-8"><title>${escapeHtml(title)}</title>
    <style>
      body{font-family:Georgia,serif;padding:24px;color:#222;max-width:720px;margin:0 auto}
      h1{font-size:1.35rem;margin:0 0 4px} .meta{color:#555;font-size:0.85rem;margin-bottom:20px}
      table{width:100%;border-collapse:collapse;font-size:0.92rem;margin-top:12px}
      th,td{border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}
      th{background:#f5f0e8}
      .mass-head{font-size:1rem;margin:20px 0 6px;border-bottom:1px solid #ccc;padding-bottom:4px}
      @media print{body{padding:12px}.no-print{display:none}}
    </style></head><body>
    <h1>${escapeHtml(settings.name || "Župa")}</h1>
    <p class="meta">${escapeHtml(title)}${massTimeFilter ? "" : ` · ${list.length} nakana`}</p>
    ${
      list.length
        ? (massTimeFilter
            ? `<table><thead><tr><th>Za koga</th><th>Naručitelj</th><th>Stipendij</th><th>Plaćeno</th><th>Bilješka</th></tr></thead><tbody>
              ${list
                .map(
                  (n) =>
                    `<tr><td>${escapeHtml(n.intentionFor)}</td><td>${escapeHtml(n.requestedBy || "—")}</td><td>${Number(n.stipend) || 0} €</td><td>${n.paid ? "da" : "ne"}</td><td>${escapeHtml(n.notes || "—")}</td></tr>`
                )
                .join("")}</tbody></table>`
            : (() => {
                const byMass = {};
                list.forEach((n) => {
                  const t = n.massTime || "—";
                  if (!byMass[t]) byMass[t] = [];
                  byMass[t].push(n);
                });
                return Object.keys(byMass)
                  .sort()
                  .map(
                    (t) => `<h2 class="mass-head">Misa ${escapeHtml(t)}</h2>
                    <table><thead><tr><th>Za koga</th><th>Naručitelj</th><th>Stipendij</th><th>Plaćeno</th><th>Bilješka</th></tr></thead><tbody>
                    ${byMass[t]
                      .map(
                        (n) =>
                          `<tr><td>${escapeHtml(n.intentionFor)}</td><td>${escapeHtml(n.requestedBy || "—")}</td><td>${Number(n.stipend) || 0} €</td><td>${n.paid ? "da" : "ne"}</td><td>${escapeHtml(n.notes || "—")}</td></tr>`
                      )
                      .join("")}</tbody></table>`
                  )
                  .join("");
              })())
        : "<p>Nema nakana za ispis.</p>"
    }
    <p class="meta no-print" style="margin-top:28px">Pastoral · ${new Date().toLocaleString("hr-HR")}</p>
    <p class="no-print"><button onclick="window.print()">Ispis / PDF</button></p>
    </body></html>`;

  const w = window.open("", "_blank");
  if (!w) {
    showToast("Omogućite skočne prozore za ispis");
    return;
  }
  w.document.write(html);
  w.document.close();
}

function renderNakaneDayListHtml(list) {
  if (!list.length) return '<p class="empty-state">Nema nakana za ovaj dan.</p>';
  const byMass = {};
  list.forEach((n) => {
    const t = n.massTime || "—";
    if (!byMass[t]) byMass[t] = [];
    byMass[t].push(n);
  });
  return Object.keys(byMass)
    .sort()
    .map((massTime) => {
      const items = byMass[massTime];
      return `<div class="nakane-mass-group">
        <div class="nakane-mass-group-head">
          <h3 class="nakane-mass-time">Misa ${escapeHtml(massTime)}</h3>
          <button type="button" class="btn btn-ghost btn-sm" data-print-mass="${escapeHtml(massTime)}" title="Ispis samo ove mise">🖨</button>
        </div>
        ${items
          .map(
            (n) => `<div class="list-item nakane-day-item" data-intent-id="${n.id}">
          <div>
            <strong>${escapeHtml(n.intentionFor)}</strong>${n.gregorianDay ? ` <span class="badge">Gregorijanska ${n.gregorianDay}/30</span>` : ""}
            <br><small>${escapeHtml(n.requestedBy || "—")} · ${Number(n.stipend) || 0} €</small>
            ${n.notes ? `<br><small class="nakane-day-notes">📝 ${escapeHtml(n.notes)}</small>` : ""}
            ${n.paid && n.paymentId ? `<br><small class="card-sub">Ref: ${escapeHtml(n.paymentId)}</small>` : ""}
          </div>
          <div class="nakana-item-actions">
            ${n.paid ? '<span class="badge badge-done">plaćeno</span>' : '<span class="badge badge-urgent">neplaćeno</span>'}
            <button type="button" class="btn btn-ghost btn-sm" data-edit-intent="${n.id}" title="Uredi">✎</button>
            ${!n.paid ? `<button type="button" class="btn btn-primary btn-sm" data-pay-intent="${n.id}">Plati</button>` : ""}
            <button type="button" class="btn btn-ghost btn-sm" data-del-intent="${n.id}">×</button>
          </div>
        </div>`
          )
          .join("")}
      </div>`;
    })
    .join("");
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", { day: "numeric", month: "short", year: "numeric" });
}

function pageUrl(file) {
  const B = window.PastoralBase;
  const f = String(file);
  if (B) {
    if (f.startsWith("public/") || f === "public/index.html") return B.publicPage(f.replace(/^public\//, ""));
    if (f === "app" || f === "app.html") return B.adminPage("app.html");
    if (f === "login.html" || f === "login") return B.adminPage("login.html");
    return B.adminPage(`pages/${f.replace(/^\/?pages\//, "")}`);
  }
  const inPages = location.pathname.includes("/pages/");
  if (f === "app" || f === "app.html") return inPages ? "../app.html" : "app.html";
  if (f === "login.html" || f === "login") return inPages ? "../login.html" : "login.html";
  const name = f.replace(/^\/?pages\//, "");
  return inPages ? name : `pages/${name}`;
}

const SESSION_HOURS = 8;

function parseSession() {
  try {
    const raw = localStorage.getItem(window.PastoralParish.SESSION_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (s.expiresAt && Date.now() > s.expiresAt) return null;
    return s;
  } catch {
    return null;
  }
}

const ROLE_LABELS = { zupnik: "Župnik", vikar: "Vikar", upravitelj: "Upravitelj", kateheta: "Kateheta" };

function loadPermissionsEngine() {
  if (window.PastoralPermissions) return Promise.resolve();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/permissions-engine.js" : "js/permissions-engine.js";
  return new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
}

function loadUsersGroupsEngine() {
  if (window.PastoralUsersGroups) return Promise.resolve();
  const inPages = location.pathname.includes("/pages/");
  const src = inPages ? "../js/users-groups-engine.js" : "js/users-groups-engine.js";
  return loadPermissionsEngine().then(
    () =>
      new Promise((resolve) => {
        const s = document.createElement("script");
        s.src = src;
        s.onload = () => resolve();
        s.onerror = () => resolve();
        document.head.appendChild(s);
      })
  );
}

function showToast(msg) {
  document.querySelector(".toast")?.remove();
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2800);
}

function modalConfirm(message, opts = {}) {
  const CM = window.PastoralCrudModals;
  if (CM?.confirm) return CM.confirm(message, opts);
  return Promise.resolve(confirm(message));
}

function initOnboardingApi() {
  const OB = window.PastoralOnboarding;
  if (!OB) return;
  OB.init({
    pageUrl,
    showToast,
  });
}

function runOnboardingAfterShell() {
  const OB = window.PastoralOnboarding;
  if (!OB) return;
  OB.ensureCleanupIfDone();
  const params = new URLSearchParams(location.search);
  if (params.get("onboarding") === "restart") {
    OB.start(0);
    return;
  }
  if (params.get("onboarding") === "1") {
    OB.start(0);
    return;
  }
  if (OB.resumeIfNeeded()) return;
  OB.maybeStartOnFirstVisit();
}

function initPriestToolsApi() {
  const PT = window.PastoralPriestTools;
  if (!PT) return;
  PT.init({
    getData,
    getSettings: () => window.PastoralParish.loadSettings(),
    pageUrl,
    showToast,
    escapeHtml,
  });
}

function initCrudModalsApi() {
  const CM = window.PastoralCrudModals;
  if (!CM) return;
  CM.init({
    getData,
    saveData,
    uid,
    showToast,
    escapeHtml,
    fmtDate,
    findFamily,
    persistFamilies,
    renderObiteljiPage,
    refreshFamilyDetailModal,
    openFamilyDetailModal,
    renderKrizmaPage,
    getSelectedCalendarDay: () => selectedCalendarDay,
    saveIntentionPaid: (fields, payment, onDone) => {
      saveIntentionAfterPayment(fields, payment);
      onDone?.();
    },
    saveIntentionUnpaid: (fields, onDone) => {
      addNakanaUnpaid(fields);
      onDone?.();
    },
    updateNakana,
    confirmNakanaIfDuplicate,
  });
}

function requireSession() {
  if (!parseSession()) {
    localStorage.removeItem(window.PastoralParish.SESSION_KEY);
    location.href = pageUrl("login.html");
    return false;
  }
  return true;
}

function getData() {
  return window.PastoralData.load();
}

function saveData(data) {
  window.PastoralData.save(data);
}

function uid(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
}

function col(key, label, opts = {}) {
  if (opts.render) return { key, label, render: opts.render };
  if (opts.fmt) return { key, label, render: (row) => escapeHtml(String(opts.fmt(row[key]) ?? "—")) };
  if (opts.badge) return { key, label, render: (row) => `<span class="badge">${escapeHtml(row[key] ?? "—")}</span>` };
  if (opts.strong) return { key, label, render: (row) => `<strong>${escapeHtml(row[key] ?? "—")}</strong>` };
  return { key, label, render: (row) => escapeHtml(row[key] ?? "—") };
}

function mountPaginatedTable(mountId, rows, columns, exportName, onImport, rowAttrs, tableOpts = {}) {
  const el = document.getElementById(mountId);
  const TK = window.PastoralTableKit;
  if (!el || !TK) return null;
  return TK.mountDataTable({
    mount: el,
    rows,
    columns,
    exportName,
    pageSize: tableOpts.pageSize || 10,
    onImport,
    rowAttrs,
    hideToolbarSearch: tableOpts.hideToolbarSearch,
    hideImport: tableOpts.hideImport,
  });
}

let familyDetailOverlay = null;

function getStreetName(data, streetId) {
  return data.streets?.find((s) => s.id === streetId)?.name || "—";
}

function syncParishionersFromFamilies(data) {
  data.parishioners = [];
  (data.families || []).forEach((fam) => {
    (fam.members || []).forEach((m) => {
      data.parishioners.push({
        id: m.id,
        family: fam.surname,
        name: m.name,
        phone: fam.phone,
        email: fam.email || "",
        status: fam.status === "aktivna" ? "aktivan" : fam.status,
        roles: m.roles || [],
      });
    });
  });
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

function renderAppFooter(settings) {
  const year = new Date().getFullYear();
  return `
    <div class="app-footer-inner">
      <div class="app-footer-col">
        <strong>${escapeHtml(settings.shortName || settings.name)}</strong>
        <span>${escapeHtml(settings.city)} · ${escapeHtml(settings.pastor)}</span>
      </div>
      <div class="app-footer-col app-footer-links">
        <a href="tel:${escapeHtml((settings.phone || "").replace(/\s/g, ""))}">${escapeHtml(settings.phone || "")}</a>
        <a href="mailto:${escapeHtml(settings.email || "")}">${escapeHtml(settings.email || "")}</a>
        <a href="${pageUrl("pages/obitelji.html")}">Obitelji</a>
        <a href="${location.pathname.includes("/pages/") ? "../public/index.html" : "public/index.html"}" target="_blank" rel="noopener">Javni obrasci</a>
        <a href="${pageUrl("pages/sigurnost.html")}#gdpr">Privatnost (GDPR)</a>
      </div>
      <div class="app-footer-col app-footer-copy">
        <span>Pastoral · demo ${year}</span>
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

function initShell() {
  const P = window.PastoralParish;
  P.applyTheme();
  const settings = P.loadSettings();

  ensureSidebarLayout();

  const logoMount = document.getElementById("sidebar-logo");
  if (logoMount) {
    logoMount.innerHTML = `
      <a href="${pageUrl("app.html")}" class="logo">
        ${P.renderLogoHtml()}
        <span class="logo-text"><small>${escapeHtml(settings.diocese)}</small><strong>${escapeHtml(settings.shortName || settings.name)}</strong></span>
      </a>`;
  }

  const meta = document.getElementById("sidebar-tenant-meta");
  const sess = parseSession();
  const roleLine = sess?.roleLabel || (sess?.role ? ROLE_LABELS[sess.role] || sess.role : settings.pastor);
  if (meta) meta.textContent = `${settings.city} · ${roleLine}`;

  const nav = document.querySelector(".sidebar .nav");
  if (nav && !nav.dataset.built) {
    nav.dataset.built = "1";
    const sess = parseSession();
    const navItems = window.PastoralPermissions?.filterNav ? window.PastoralPermissions.filterNav(NAV, sess) : NAV;
    if (window.PastoralSidebarNav) {
      window.PastoralSidebarNav.mount(nav, navItems, { pageUrl, escapeHtml });
      window.PastoralSidebarNav.injectSidebarFooterControls();
    } else {
      nav.innerHTML = navItems.map((item) => {
        if (item.type === "label") return `<li class="nav-section-label">${escapeHtml(item.text)}</li>`;
        const [file, icon, label] = item;
        return `<li><a href="${pageUrl(file)}"><span class="nav-ico">${icon}</span>${escapeHtml(label)}</a></li>`;
      }).join("");
    }
  }

  ensureAppFooter(settings);

  if (window.PastoralTheme) window.PastoralTheme.initThemePicker();

  initPriestToolsApi();
  window.PastoralPriestTools?.enhanceShell();

  window.PastoralGdpr?.mountAdminBanner({ pageUrl });

  window.PastoralUiPolish?.enhance();

  initOnboardingApi();
  setTimeout(runOnboardingAfterShell, 300);

  if (window.PastoralLiturgical) {
    const now = new Date();
    const L = window.PastoralLiturgical;
    if (L.loadLitcalYearsForMonth) {
      L.loadLitcalYearsForMonth(now.getFullYear(), now.getMonth()).catch(() => {});
    } else {
      L.loadLitcalYear(now.getFullYear()).catch(() => {});
    }
    if (!document.body.dataset.liturgicalListen) {
      document.body.dataset.liturgicalListen = "1";
      document.addEventListener("pastoral-liturgical-ready", () => {
        const page = document.body.dataset.page;
        if (page === "nakane") {
          renderNakaneCalendar();
          if (selectedCalendarDay) renderNakaneDayPanel();
        }
      });
    }
  }

  document.getElementById("btn-logout")?.addEventListener("click", () => {
    localStorage.removeItem(P.SESSION_KEY);
    location.href = pageUrl("login.html");
  });
}

function renderDashboard() {
  const d = getData();
  const today = new Date().toISOString().slice(0, 10);
  const root = document.getElementById("dashboard-root");
  if (!root) return;

  const PT = window.PastoralPriestTools;
  const stats = PT ? PT.getOfficeStats(d) : {};

  const todayIntentions = d.intentions.filter((n) => n.date === today);
  const unpaid = stats.unpaidNakane ?? d.intentions.filter((n) => !n.paid).length;
  const confYear = d.confirmations.find((c) => c.year === new Date().getFullYear()) || d.confirmations[0];
  const openTasks = stats.openTasks ?? d.tasks.filter((t) => !t.done).length;
  const overdueTasks = stats.overdueTasks ?? 0;
  const DEMO = window.PastoralDemo;
  const demoBlock = DEMO
    ? DEMO.mountDashboardWow({ getData, getSettings: () => window.PastoralParish.loadSettings(), pageUrl, showToast, escapeHtml })
    : null;
  const priestExtras = PT ? PT.renderDashboardExtras(d, stats) : "";
  const REM = window.PastoralReminders;
  const reminderItems = REM ? REM.collectReminders(d) : [];
  const remindersHtml = REM
    ? `<section class="card wide reminders-dashboard-card">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
          <h2 class="section-title" style="margin:0">Podsjetnici <span class="badge badge-urgent">${reminderItems.length}</span></h2>
          <a href="${pageUrl("pages/podsjetnici.html")}" class="btn btn-primary btn-sm">Cijeli inbox</a>
        </div>
        <div id="dash-reminders-mount">${REM.renderInboxHtml(reminderItems.slice(0, 8), { escapeHtml, pageUrl })}</div>
      </section>`
    : "";

  const analyticsHtml = window.PastoralAnalytics
    ? window.PastoralAnalytics.renderAnalyticsHtml(d)
    : "";

  root.innerHTML = `
    ${dashQuickActionsHtml(d)}
    ${analyticsHtml}
    ${demoBlock?.html || ""}
    ${window.PastoralGdpr ? window.PastoralGdpr.renderDashboardGdprCard({ pageUrl }) : ""}
    ${priestExtras}
    ${remindersHtml}
    <div id="liturgical-dashboard-mount"></div>
    ${(() => {
      const K = window.PastoralKpi;
      if (!K) {
        return `<div class="kpi-row">
      <a href="${pageUrl("pages/nakane.html")}?date=today" class="card kpi-card kpi-card--link"><p class="card-label">Nakane danas</p><p class="card-value">${todayIntentions.length}</p></a>
      <a href="${pageUrl("pages/dugovanja.html")}" class="card kpi-card kpi-card--link"><p class="card-label">Dugovanja</p><p class="card-value">${stats.debtsUnpaid ?? 0}</p></a>
    </div>`;
      }
      return K.row([
        { tone: "liturgy", label: "Nakane danas", value: todayIntentions.length, href: pageUrl("pages/nakane.html") + "?date=today" },
        { tone: "alert", label: "Neplaćene nakane", value: unpaid, href: pageUrl("pages/nakane.html") },
        { tone: "sacrament", label: `Krizmanici (${confYear?.year || "—"})`, value: confYear?.candidates?.length || 0, href: pageUrl("pages/krizma.html") },
        { tone: "sacrament", label: "Krštenja", value: d.baptisms.filter((b) => b.baptismDate >= today).length, href: pageUrl("pages/krsenja.html") },
        { tone: "pastoral", label: "Zadaci", value: openTasks, href: pageUrl("pages/zadaci.html") },
        { tone: "pastoral", label: "Obitelji", value: (d.families || []).length, href: pageUrl("pages/obitelji.html") },
        { tone: "finance", label: "Lukno", value: stats.luknoUnpaid ?? 0, href: pageUrl("pages/dugovanja.html") + "?cat=lukno" },
        { tone: "finance", label: "Dugovanja", value: stats.debtsUnpaid ?? 0, href: pageUrl("pages/dugovanja.html") },
        { tone: "neutral", label: "Podsjetnici", value: stats.remindersCount ?? 0, href: pageUrl("pages/podsjetnici.html") },
        { tone: "neutral", label: "Posjeti", value: stats.visitsDue ?? 0, href: pageUrl("pages/posjete.html") },
        { tone: "accent", label: "Uredbe", value: window.PastoralAdminDocs ? window.PastoralAdminDocs.CATALOG.length : "—", href: pageUrl("pages/admin-paket.html") },
      ]);
    })()}
    <div class="dashboard-grid">
      <section class="${window.PastoralKpi ? window.PastoralKpi.sectionClass("liturgy") : "card"}">
        <h2 class="section-title">Današnje misne nakane</h2>
        ${todayIntentions.length
          ? todayIntentions
              .map(
                (n) =>
                  `<a href="${pageUrl("pages/nakane.html")}?date=today" class="list-item list-item--clickable"><div><strong>${escapeHtml(n.intentionFor)}</strong><br><small>${escapeHtml(n.massTime)} · ${escapeHtml(n.requestedBy)}</small></div>${n.paid ? '<span class="badge badge-done">plaćeno</span>' : '<span class="badge badge-urgent">neplaćeno</span>'}</a>`
              )
              .join("")
          : '<p class="empty-state">Nema nakana za danas.</p>'}
        <a href="${pageUrl("pages/nakane.html")}?date=today" class="btn btn-primary btn-sm">Kalendar nakana</a>
      </section>
      <section class="${window.PastoralKpi ? window.PastoralKpi.sectionClass("sacrament") : "card"}">
        <h2 class="section-title">Sljedeći sakramenti</h2>
        ${[...d.baptisms.slice(0, 2).map((b) => ({ t: "krštenje", n: b.childName, d: b.baptismDate })), ...d.weddings.slice(0, 1).map((w) => ({ t: "vjenčanje", n: w.couple, d: w.weddingDate })), ...d.funerals.slice(0, 1).map((f) => ({ t: "pogreb", n: f.deceased, d: f.funeralDate }))]
          .map((x) => `<div class="list-item"><span class="badge badge-sacrament">${x.t}</span> <strong>${escapeHtml(x.n)}</strong> — ${fmtDate(x.d)}</div>`)
          .join("") || '<p class="empty-state">—</p>'}
      </section>
      <section class="card wide">
        <h2 class="section-title">Prioritetni zadaci župnog ureda${overdueTasks ? ` <span class="badge badge-urgent">${overdueTasks} zakašnjelo</span>` : ""}</h2>
        ${d.tasks
          .filter((t) => !t.done)
          .sort((a, b) => (a.due || "9999").localeCompare(b.due || "9999"))
          .slice(0, 6)
          .map((t) => {
            const late = t.due && t.due < today;
            return `<a href="${pageUrl("pages/zadaci.html")}" class="list-item list-item--clickable"><strong>${escapeHtml(t.title)}</strong><span class="badge ${late || t.priority === "visoka" ? "badge-urgent" : ""}">${fmtDate(t.due)}</span></a>`;
          })
          .join("") || '<p class="empty-state">Nema otvorenih zadataka.</p>'}
        <a href="${pageUrl("pages/zadaci.html")}" class="btn btn-primary btn-sm">Svi zadaci</a>
      </section>
      <section class="${window.PastoralKpi ? window.PastoralKpi.sectionClass("finance") : "card"}">
        <h2 class="section-title">Lukno ${new Date().getFullYear()} — neplaćeno</h2>
        ${(() => {
          const y = new Date().getFullYear();
          const FC = window.PastoralFamilyCrud;
          const unpaidFam = (d.families || []).filter((f) => FC && !FC.currentYearStatus(f, y).paid);
          return unpaidFam.length
            ? unpaidFam
                .slice(0, 6)
                .map(
                  (f) =>
                    `<a href="${pageUrl("pages/obitelji.html")}?family=${encodeURIComponent(f.id)}" class="list-item list-item--clickable"><strong>${escapeHtml(f.surname)}</strong><br><small>${escapeHtml(f.address || "")}</small></a>`
                )
                .join("")
            : '<p class="empty-state">Sve obitelji su označene kao platile lukno.</p>';
        })()}
        <a href="${pageUrl("pages/obitelji.html")}" class="btn btn-ghost btn-sm">Obitelji</a>
        <a href="${pageUrl("pages/dugovanja.html")}?cat=lukno" class="btn btn-primary btn-sm">Sva dugovanja</a>
      </section>
    </div>`;
  if (window.PastoralAnalytics) {
    requestAnimationFrame(() => window.PastoralAnalytics.paintDashboardCharts(d));
  }
  const litMount = document.getElementById("liturgical-dashboard-mount");
  if (litMount && window.PastoralLiturgical) {
    window.PastoralLiturgical.mountInto(litMount, today, { compact: true });
  }
  demoBlock?.bind?.();
  document.getElementById("priest-demo-story")?.addEventListener("click", () => {
    window.PastoralDemo?.openSalesStory({ showToast, pageUrl });
  });
  window.PastoralTheme?.repositionInTopbar?.();
  const remMount = document.getElementById("dash-reminders-mount");
  if (remMount && REM) {
    REM.bindInbox(remMount, { escapeHtml, pageUrl, showToast, getData }, getData);
    remMount.dataset.remount = "";
    remMount.addEventListener("pastoral-reminders-refresh", () => renderDashboard());
  }
}

function buildMonthGrid(year, month) {
  const first = new Date(year, month, 1);
  const startPad = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < startPad; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) {
    const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    cells.push(iso);
  }
  return cells;
}

function computeNakanePageStats(data) {
  const intentions = data.intentions || [];
  const total = intentions.length;
  const paid = intentions.filter((n) => n.paid).length;
  const unpaid = total - paid;
  const paidPct = total ? Math.round((paid / total) * 100) : 0;
  const stipendTotal = intentions.reduce((s, n) => s + (Number(n.stipend) || 0), 0);
  const stipendUnpaid = intentions.filter((n) => !n.paid).reduce((s, n) => s + (Number(n.stipend) || 0), 0);
  const now = new Date();
  const last6 = [];
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const mk = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    last6.push({
      label: d.toLocaleDateString("hr-HR", { month: "short" }),
      count: intentions.filter((n) => n.date?.startsWith(mk)).length,
    });
  }
  return { total, paid, unpaid, paidPct, stipendTotal, stipendUnpaid, last6 };
}

function destroyNakaneCharts() {
  nakaneCharts.forEach((c) => c.destroy());
  nakaneCharts = [];
}

function paintNakaneCharts(stats) {
  if (!window.Chart) return;
  destroyNakaneCharts();
  const paidCanvas = document.getElementById("chart-nakane-paid");
  const monthsCanvas = document.getElementById("chart-nakane-months");
  if (paidCanvas && stats.total) {
    nakaneCharts.push(
      new window.Chart(paidCanvas, {
        type: "doughnut",
        data: {
          labels: ["Plaćeno", "Neplaćeno"],
          datasets: [
            {
              data: [stats.paid, stats.unpaid],
              backgroundColor: ["#2d6a4f", "#9b3d3d"],
              borderWidth: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "62%",
          plugins: {
            legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } },
          },
        },
      })
    );
  }
  if (monthsCanvas) {
    nakaneCharts.push(
      new window.Chart(monthsCanvas, {
        type: "bar",
        data: {
          labels: stats.last6.map((x) => x.label),
          datasets: [
            {
              label: "Nakane",
              data: stats.last6.map((x) => x.count),
              backgroundColor: "color-mix(in srgb, #3d5a80 75%, transparent)",
              borderRadius: 4,
              maxBarThickness: 28,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 10 } } },
            y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } }, grid: { color: "rgba(0,0,0,0.06)" } },
          },
        },
      })
    );
  }
}

function renderNakaneStats() {
  const el = document.getElementById("nakane-stats");
  if (!el) return;
  const d = getData();
  const stats = computeNakanePageStats(d);

  el.innerHTML = `
    <div class="nakane-stats-head">
      <div>
        <h2 class="section-title">Pregled i statistika</h2>
        <p class="card-sub">Ukupna evidencija nakana — tablicu ispod sortirajte i filtrirajte.</p>
      </div>
    </div>
    <div class="nakane-kpi-grid">
      <article class="nakane-kpi-tile nakane-kpi-tile--total">
        <p class="nakane-kpi-label">Ukupno</p>
        <p class="nakane-kpi-value">${stats.total}</p>
        <p class="nakane-kpi-sub">svih nakana u evidenciji</p>
      </article>
      <article class="nakane-kpi-tile nakane-kpi-tile--paid">
        <p class="nakane-kpi-label">Plaćeno</p>
        <p class="nakane-kpi-value">${stats.paid}</p>
        <p class="nakane-kpi-sub">${stats.paidPct}% od ukupnog broja</p>
      </article>
      <article class="nakane-kpi-tile nakane-kpi-tile--unpaid">
        <p class="nakane-kpi-label">Neplaćeno</p>
        <p class="nakane-kpi-value">${stats.unpaid}</p>
        <p class="nakane-kpi-sub">${stats.stipendUnpaid} € stipendija</p>
      </article>
      <article class="nakane-kpi-tile nakane-kpi-tile--stipend">
        <p class="nakane-kpi-label">Stipendiji</p>
        <p class="nakane-kpi-value">${stats.stipendTotal} €</p>
        <p class="nakane-kpi-sub">ukupno u evidenciji</p>
      </article>
    </div>
    <div class="nakane-charts-grid">
      <article class="analytics-stat card-section--finance">
        <p class="card-label">Evidencija plaćenih i neplaćenih misnih nakana</p>
        <div class="chart-wrap chart-wrap--md"><canvas id="chart-nakane-paid"></canvas></div>
        ${stats.total ? "" : '<p class="empty-state">Nema nakana za prikaz.</p>'}
      </article>
      <article class="analytics-stat card-section--liturgy">
        <p class="card-label">Nakane — zadnjih 6 mjeseci</p>
        <div class="chart-wrap chart-wrap--md"><canvas id="chart-nakane-months"></canvas></div>
      </article>
    </div>`;

  loadChartJs().then(() => paintNakaneCharts(stats));
}

function clearNakaneLitTopbar() {
  document.getElementById("nakane-lit-swatch-corner")?.remove();
  document.getElementById("nakane-topbar-lit")?.remove();
}

function renderCalNakaneList(nakane, maxVisible = 3) {
  if (!nakane?.length) return "";
  const shown = nakane.slice(0, maxVisible);
  const rest = nakane.length - shown.length;
  return `<div class="cal-nakane-list">
    ${shown.map((n) => `<span class="cal-nakane-item" title="${escapeHtml(n.intentionFor)}">${escapeHtml(n.intentionFor)}</span>`).join("")}
    ${rest > 0 ? `<span class="cal-nakane-more">+ ${rest} više</span>` : ""}
  </div>`;
}

function sortNakaneRows(rows, sort) {
  const mul = sort.dir === "desc" ? -1 : 1;
  return [...rows].sort((a, b) => {
    let va;
    let vb;
    switch (sort.key) {
      case "massTime":
        va = a.massTime || "";
        vb = b.massTime || "";
        break;
      case "intentionFor":
        va = a.intentionFor || "";
        vb = b.intentionFor || "";
        break;
      case "requestedBy":
        va = a.requestedBy || "";
        vb = b.requestedBy || "";
        break;
      case "stipend":
        va = Number(a.stipend) || 0;
        vb = Number(b.stipend) || 0;
        return (va - vb) * mul;
      case "paid":
        va = a.paid ? 1 : 0;
        vb = b.paid ? 1 : 0;
        return (va - vb) * mul;
      case "date":
      default:
        va = a.date || "";
        vb = b.date || "";
        break;
    }
    return String(va).localeCompare(String(vb), "hr") * mul;
  });
}

function renderNakaneTable() {
  const mount = document.getElementById("nakane-table");
  if (!mount) return;
  const d = getData();
  const allRows = d.intentions || [];
  const q = nakaneTableFilter.search.trim().toLowerCase();
  let filtered = allRows.filter((n) => {
    if (nakaneTableFilter.status === "paid" && !n.paid) return false;
    if (nakaneTableFilter.status === "unpaid" && n.paid) return false;
    if (!q) return true;
    return [n.date, n.massTime, n.intentionFor, n.requestedBy, String(n.stipend)]
      .some((v) => String(v ?? "").toLowerCase().includes(q));
  });
  filtered = sortNakaneRows(filtered, nakaneTableSort);

  const cols = [
    { key: "date", label: "Datum" },
    { key: "massTime", label: "Misa" },
    { key: "intentionFor", label: "Nakana" },
    { key: "requestedBy", label: "Naručitelj" },
    { key: "stipend", label: "Stipendij" },
    { key: "paid", label: "Status" },
    { key: "_actions", label: "" },
  ];

  mount.innerHTML = `
    <h2 class="section-title">Sve nakane</h2>
    <p class="card-sub">Kliknite red za otvaranje dana u kalendaru. Sortirajte klikom na zaglavlje.</p>
    <div class="nakane-table-toolbar">
      <input type="search" class="nakane-table-search" placeholder="Pretraži nakane…" value="${escapeHtml(nakaneTableFilter.search)}" />
      <select class="nakane-table-filter" data-nakane-status>
        <option value="all" ${nakaneTableFilter.status === "all" ? "selected" : ""}>Sve</option>
        <option value="paid" ${nakaneTableFilter.status === "paid" ? "selected" : ""}>Plaćeno</option>
        <option value="unpaid" ${nakaneTableFilter.status === "unpaid" ? "selected" : ""}>Neplaćeno</option>
      </select>
      <button type="button" class="btn btn-ghost btn-sm${nakaneTableFilter.status === "unpaid" ? " btn-secondary" : ""}" data-nakane-unpaid-quick>Neplaćeno</button>
      <span class="table-kit-meta">${filtered.length} / ${allRows.length} nakana</span>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead><tr>${cols
          .map((c) => {
            const sorted = nakaneTableSort.key === c.key;
            const cls = `nakane-th-sort${sorted ? " is-sorted" : ""}${sorted && nakaneTableSort.dir === "desc" ? " is-desc" : ""}`;
            return `<th class="${cls}" data-sort-key="${c.key}">${c.label}</th>`;
          })
          .join("")}</tr></thead>
        <tbody>${filtered.length
          ? filtered
              .map((n) => {
                const sel = n.date === selectedCalendarDay ? " is-selected" : "";
                return `<tr class="nakane-table-row${sel}" data-nakana-row="${n.id}" data-nakana-date="${escapeHtml(n.date)}">
                  <td>${escapeHtml(fmtDate(n.date))}</td>
                  <td>${escapeHtml(n.massTime || "—")}</td>
                  <td><strong>${escapeHtml(n.intentionFor || "—")}</strong>${n.gregorianDay ? ` <span class="badge">G${n.gregorianDay}/30</span>` : ""}</td>
                  <td>${escapeHtml(n.requestedBy || "—")}</td>
                  <td>${Number(n.stipend) || 0} €</td>
                  <td>${n.paid ? '<span class="badge badge-done">plaćeno</span>' : '<span class="badge badge-urgent">neplaćeno</span>'}</td>
                  <td class="nakane-table-actions">
                    <button type="button" class="btn btn-ghost btn-sm" data-edit-intent="${n.id}" title="Uredi">✎</button>
                    ${!n.paid ? `<button type="button" class="btn btn-primary btn-sm" data-pay-intent="${n.id}">Plati</button>` : ""}
                    <button type="button" class="btn btn-ghost btn-sm" data-del-intent="${n.id}">×</button>
                  </td>
                </tr>`;
              })
              .join("")
          : `<tr><td colspan="8" class="empty-state">Nema nakana za prikaz.</td></tr>`}</tbody>
      </table>
    </div>`;

  mount.querySelector(".nakane-table-search")?.addEventListener("input", (e) => {
    nakaneTableFilter.search = e.target.value;
    renderNakaneTable();
  });
  mount.querySelector("[data-nakane-status]")?.addEventListener("change", (e) => {
    nakaneTableFilter.status = e.target.value;
    renderNakaneTable();
  });
  mount.querySelector("[data-nakane-unpaid-quick]")?.addEventListener("click", () => {
    nakaneTableFilter.status = nakaneTableFilter.status === "unpaid" ? "all" : "unpaid";
    renderNakaneTable();
  });
  mount.querySelectorAll("[data-sort-key]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.sortKey;
      if (nakaneTableSort.key === key) {
        nakaneTableSort.dir = nakaneTableSort.dir === "asc" ? "desc" : "asc";
      } else {
        nakaneTableSort.key = key;
        nakaneTableSort.dir = "asc";
      }
      renderNakaneTable();
    });
  });
  mount.querySelectorAll("[data-nakana-row]").forEach((tr) => {
    tr.addEventListener("click", (e) => {
      if (e.target.closest("button")) return;
      const iso = tr.dataset.nakanaDate;
      if (!iso) return;
      selectedCalendarDay = iso;
      calendarMonth = new Date(iso + "T12:00:00");
      try {
        sessionStorage.setItem("nakane-view-mode", "calendar");
      } catch {
        /* ignore */
      }
      applyNakaneViewMode();
      refreshNakanePage();
      requestAnimationFrame(() => {
        document.getElementById("nakane-workspace")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  });
  bindNakanaRowActions(mount);
}

function bindNakanaRowActions(root) {
  root.querySelectorAll("[data-edit-intent]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      window.PastoralCrudModals?.openEditNakana(btn.dataset.editIntent, refreshNakanePage);
    });
  });
  root.querySelectorAll("[data-print-mass]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (selectedCalendarDay) printNakaneDay(selectedCalendarDay, btn.dataset.printMass);
    });
  });
  root.querySelectorAll("[data-pay-intent]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const data = getData();
      const n = data.intentions.find((x) => x.id === btn.dataset.payIntent);
      if (!n) return;
      runNakanaPayment(n, () => {
        showToast("Plaćanje zabilježeno");
        refreshNakanePage();
      });
    });
  });
  root.querySelectorAll("[data-del-intent]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const ok = await modalConfirm("Obrisati ovu nakanu?", { danger: true, title: "Brisanje nakane" });
      if (!ok) return;
      const data = getData();
      data.intentions = data.intentions.filter((n) => n.id !== btn.dataset.delIntent);
      saveData(data);
      showToast("Nakana obrisana");
      refreshNakanePage();
    });
  });
}

function refreshNakanePage() {
  applyNakaneViewMode();
  renderNakaneCommandBar();
  const mode = getNakaneViewMode();
  if (mode === "today") {
    selectedCalendarDay = new Date().toISOString().slice(0, 10);
    renderNakaneDayPanel();
  } else if (mode === "calendar") {
    if (!selectedCalendarDay) selectedCalendarDay = new Date().toISOString().slice(0, 10);
    renderNakaneCalendar();
    renderNakaneDayPanel();
  } else {
    renderNakaneStats();
    renderNakaneTable();
  }
}

function renderNakaneCalendar() {
  const d = getData();
  const y = calendarMonth.getFullYear();
  const m = calendarMonth.getMonth();
  const cells = buildMonthGrid(y, m);
  const monthLabel = calendarMonth.toLocaleDateString("hr-HR", { month: "long", year: "numeric" });
  const byDate = {};
  d.intentions.forEach((n) => {
    byDate[n.date] = byDate[n.date] || [];
    byDate[n.date].push(n);
  });

  const calEl = document.getElementById("nakane-calendar");
  if (!calEl) return;

  const L = window.PastoralLiturgical;
  const litSummaries = L ? L.summariesForMonth(y, m) : {};
  const litLoaded = Object.values(litSummaries).some((s) => s.loaded);
  const litWarn =
    L && !litLoaded
      ? `<p class="card-sub cal-lit-warn">Liturgijski kalendar se učitava… Ako ostane prazno, pokrenite stranicu preko <code>npx serve .</code> (ne <code>file://</code>).</p>`
      : "";
  const weekDays = ["Pon", "Uto", "Sri", "Čet", "Pet", "Sub", "Ned"];
  calEl.innerHTML = `
    <h2 class="section-title">Kalendar misnih nakana</h2>
    ${litWarn}
    <p class="card-sub cal-lit-legend">Svaki dan: liturgijska boja, rang, svetac/blagdan (LitCal API). Kliknite dan — detalj desno.</p>
    <div class="cal-header">
      <button type="button" class="btn btn-ghost btn-sm" id="cal-prev">‹</button>
      <strong class="cal-month-title">${escapeHtml(monthLabel)}</strong>
      <button type="button" class="btn btn-ghost btn-sm" id="cal-next">›</button>
      <button type="button" class="btn btn-secondary btn-sm" id="cal-today">Danas</button>
    </div>
    <div class="cal-weekdays">${weekDays.map((w) => `<span>${w}</span>`).join("")}</div>
    <div class="cal-grid cal-grid--lit">${cells
      .map((iso) => {
        if (!iso) return '<div class="cal-cell cal-empty"></div>';
        const sel = selectedCalendarDay === iso ? " cal-selected" : "";
        const isToday = iso === new Date().toISOString().slice(0, 10) ? " cal-today" : "";
        const sum = L ? litSummaries[iso] || L.getSummarySync(iso) : null;
        const litBgCls = sum?.loaded && sum?.color && L ? L.liturgicalCellClass(sum.color) : "";
        const litHtml = L ? L.renderCellLiturgy(sum) : "";
        const cellTip = sum?.loaded
          ? [sum.title, sum.rankLabel || sum.rank, sum.colorLabel, sum.subtitle].filter(Boolean).join(" · ")
          : "Liturgijski dan";
        return `<button type="button" class="cal-cell cal-cell--lit ${litBgCls}${sel}${isToday}" data-cal-day="${iso}" title="${escapeHtml(cellTip)}">
          <span class="cal-day-num">${parseInt(iso.slice(8), 10)}</span>
          ${litHtml}
          ${renderCalNakaneList((byDate[iso] || []).slice().sort((a, b) => String(a.massTime || "").localeCompare(String(b.massTime || ""))))}
        </button>`;
      })
      .join("")}</div>
    ${L ? L.renderCalColorLegend() : ""}`;

  document.getElementById("cal-prev")?.addEventListener("click", () => {
    calendarMonth = new Date(y, m - 1, 1);
    paintNakaneCalendarMonth();
  });
  document.getElementById("cal-next")?.addEventListener("click", () => {
    calendarMonth = new Date(y, m + 1, 1);
    paintNakaneCalendarMonth();
  });
  document.getElementById("cal-today")?.addEventListener("click", () => {
    calendarMonth = new Date();
    selectedCalendarDay = new Date().toISOString().slice(0, 10);
    renderNakaneCalendar();
    renderNakaneDayPanel();
    document.getElementById("nakane-day-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  calEl.querySelectorAll("[data-cal-day]").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedCalendarDay = btn.dataset.calDay;
      renderNakaneCalendar();
      renderNakaneDayPanel();
      document.getElementById("nakane-day-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  if (!selectedCalendarDay) {
    selectedCalendarDay = new Date().toISOString().slice(0, 10);
  }
}

async function loadNakaneLitDetail(iso) {
  const L = window.PastoralLiturgical;
  if (!L || iso !== selectedCalendarDay) return;
  const slot = document.getElementById("nakane-lit-detail");
  if (!slot) return;
  try {
    const day = await L.getDay(iso);
    if (iso !== selectedCalendarDay) return;
    slot.outerHTML = L.renderNakaneDayLiturgy(day);
  } catch {
    if (iso !== selectedCalendarDay) return;
    slot.outerHTML = L.renderNakaneDayLiturgy({
      source: "offline",
      date: iso,
      title: null,
      hilpUrl: L.hilpUrlForDate(iso),
    });
  }
}

function renderNakaneDayPanel() {
  const panelEl = document.getElementById("nakane-day-panel");
  if (!panelEl || !selectedCalendarDay) return;
  const d = getData();
  const list = d.intentions.filter((n) => n.date === selectedCalendarDay);
  const L = window.PastoralLiturgical;
  const litLoading = L ? L.renderNakaneLitLoading(selectedCalendarDay) : "";

  panelEl.innerHTML = `
    <section class="card nakane-day-card">
      ${litLoading}
      <div class="nakane-day-list">${renderNakaneDayListHtml(list)}</div>
    </section>`;

  loadNakaneLitDetail(selectedCalendarDay);

  bindNakanaRowActions(panelEl);
}

function paintNakaneCalendarMonth() {
  const y = calendarMonth.getFullYear();
  const m = calendarMonth.getMonth();
  const done = () => renderNakaneCalendar();
  const L = window.PastoralLiturgical;
  if (L?.loadLitcalYearsForMonth) {
    L.loadLitcalYearsForMonth(y, m).finally(done);
    return;
  }
  if (L?.loadLitcalYear) {
    L.loadLitcalYear(y).finally(done);
    return;
  }
  done();
}

function saveIntentionAfterPayment(fields, payment) {
  const data = getData();
  data.intentions.push({
    id: uid("n"),
    ...fields,
    paid: true,
    paymentId: payment.paymentId,
    paidAt: payment.paidAt,
  });
  saveData(data);
  showToast("Nakana dodana i plaćena");
  refreshNakanePage();
}

function addNakanaUnpaid(fields) {
  const data = getData();
  data.intentions.push({
    id: uid("n"),
    ...fields,
    paid: false,
    paymentId: "",
    paidAt: "",
  });
  saveData(data);
  showToast("Nakana spremljena — plaćanje kasnije");
  refreshNakanePage();
}

function runNakanaPayment(intent, onDone) {
  const Pay = window.PastoralPayment;
  if (!Pay) {
    showToast("Modul evidencije uplate nije učitan");
    return;
  }
  Pay.recordPayment({
    amount: intent.stipend,
    title: intent.intentionFor,
    subtitle: `${intent.massTime} · ${intent.requestedBy || "—"}`,
    onSuccess: (payment) => {
      const data = getData();
      const row = data.intentions.find((n) => n.id === intent.id);
      if (row) {
        row.paid = true;
        row.paymentId = payment.paymentId;
        row.paidAt = payment.paidAt;
        saveData(data);
      }
      onDone?.();
    },
  });
}

function initNakanePage() {
  clearNakaneLitTopbar();
  const params = new URLSearchParams(location.search);
  const dateParam = params.get("date");
  const modeParam = params.get("mode");
  if (dateParam === "today") {
    selectedCalendarDay = new Date().toISOString().slice(0, 10);
    calendarMonth = new Date();
    try {
      sessionStorage.setItem("nakane-view-mode", "today");
    } catch {
      /* ignore */
    }
  } else if (dateParam && /^\d{4}-\d{2}-\d{2}$/.test(dateParam)) {
    selectedCalendarDay = dateParam;
    calendarMonth = new Date(dateParam + "T12:00:00");
    try {
      sessionStorage.setItem("nakane-view-mode", "calendar");
    } catch {
      /* ignore */
    }
  } else {
    selectedCalendarDay = new Date().toISOString().slice(0, 10);
    calendarMonth = new Date();
  }
  if (modeParam === "evidence" || modeParam === "calendar" || modeParam === "today") {
    try {
      sessionStorage.setItem("nakane-view-mode", modeParam);
    } catch {
      /* ignore */
    }
  }
  applyNakaneViewMode();
  const topbar = document.querySelector(".topbar");
  if (topbar && !document.getElementById("nakane-extra-tools")) {
    const wrap = document.createElement("div");
    wrap.className = "topbar-actions";
    wrap.id = "nakane-extra-tools";
    wrap.innerHTML = `<span id="nakane-bulletin-slot"></span>
      <button type="button" class="btn btn-ghost btn-sm" id="nakana-gregorian-btn">Gregorijanska (30)</button>`;
    topbar.appendChild(wrap);
    window.PastoralBulletin?.mountBulletinToolbar(document.getElementById("nakane-bulletin-slot"), {
      getData,
      getSettings: () => window.PastoralParish.loadSettings(),
      showToast,
    });
    document.getElementById("nakana-gregorian-btn")?.addEventListener("click", () => {
      window.PastoralCrudModals?.openGregorianNakana(refreshNakanePage);
    });
  }
  const y = calendarMonth.getFullYear();
  const m = calendarMonth.getMonth();
  const finish = () => {
    refreshNakanePage();
  };
  if (window.PastoralLiturgical?.loadLitcalYearsForMonth) {
    window.PastoralLiturgical.loadLitcalYearsForMonth(y, m).finally(finish);
    return;
  }
  if (window.PastoralLiturgical) {
    window.PastoralLiturgical.loadLitcalYear(y).finally(finish);
    return;
  }
  finish();
}

function initMisePage() {
  const mount = document.getElementById("page-root");
  if (!mount || !window.PastoralMise) return;
  const start = () => {
    window.PastoralMise.mountMisePage(mount, {
      getData,
      saveData,
      showToast,
      fmtDate,
      pageUrl,
      confirm: (message, opts) => modalConfirm(message, opts),
      printNakaneDay: (iso, massTime) => printNakaneDay(iso, massTime),
      openNakanaForDate: (iso, massTime, onDone) => {
        selectedCalendarDay = iso;
        calendarMonth = new Date(iso + "T12:00:00");
        try {
          sessionStorage.setItem("nakane-view-mode", iso === new Date().toISOString().slice(0, 10) ? "today" : "calendar");
        } catch {
          /* ignore */
        }
        window.PastoralCrudModals?.openNakana(() => {
          onDone?.();
        });
      },
    });
  };
  const L = window.PastoralLiturgical;
  if (L?.loadLitcalYear) {
    L.loadLitcalYear(new Date().getFullYear()).finally(start);
    return;
  }
  start();
}

function renderKrizmaPage() {
  const d = getData();
  const root = document.getElementById("page-root");
  if (!root) return;
  const years = [...new Set(d.confirmations.map((c) => c.year))].sort((a, b) => b - a);
  let year = parseInt(root.dataset.year || years[0] || new Date().getFullYear(), 10);
  const conf = d.confirmations.find((c) => c.year === year) || d.confirmations[0];
  const K = window.PastoralKpi;
  const candCount = conf?.candidates?.length || 0;
  const prepCount = (conf?.candidates || []).filter((c) => c.status === "priprema" || c.status === "pristupnica").length;

  root.innerHTML = `
    ${
      K
        ? K.row([
            { tone: "sacrament", label: `Krizmanici ${year}`, value: candCount },
            { tone: "pastoral", label: "U pripremi", value: prepCount },
            { tone: conf?.groupFeePaid ? "success" : "alert", label: "Grupna naknada", value: conf?.groupFeePaid ? "Plaćeno" : "Duguje" },
          ])
        : ""
    }
    <section class="card" style="margin-bottom:16px">
      <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center">
        <label>Godina krizme <select id="krizma-year">${years.map((y) => `<option value="${y}" ${y === year ? "selected" : ""}>${y}</option>`).join("")}</select></label>
        ${conf ? `<span class="card-sub">Obred: ${fmtDate(conf.ceremonyDate)} · ${escapeHtml(conf.bishop || "")}</span>` : ""}
        <button type="button" class="btn btn-secondary btn-sm" id="krizma-add-year">+ Nova godina</button>
      </div>
    </section>
    <nav class="plan-tabs">
      <button type="button" class="plan-tab-btn active" data-krizma-tab="candidates">Krizmanici</button>
      <button type="button" class="plan-tab-btn" data-krizma-tab="catechists">Katehete / suradnici</button>
    </nav>
    <div id="krizma-panel-candidates"></div>
    <div id="krizma-panel-catechists" hidden></div>`;

  document.getElementById("krizma-year")?.addEventListener("change", (e) => {
    root.dataset.year = e.target.value;
    renderKrizmaPage();
  });

  document.getElementById("krizma-add-year")?.addEventListener("click", () => {
    window.PastoralCrudModals?.openKrizmaYear(root);
  });

  root.querySelectorAll("[data-krizma-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      root.querySelectorAll("[data-krizma-tab]").forEach((b) => b.classList.toggle("active", b === btn));
      document.getElementById("krizma-panel-candidates").hidden = btn.dataset.krizmaTab !== "candidates";
      document.getElementById("krizma-panel-catechists").hidden = btn.dataset.krizmaTab !== "catechists";
    });
  });

  const candPanel = document.getElementById("krizma-panel-candidates");
  if (conf && candPanel) {
    candPanel.innerHTML = `
      <section class="card">
        <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:12px">
          <p class="card-sub" style="margin:0">${conf.candidates.length} krizmanika · import/export · <a href="${pageUrl("pages/dokumenti.html")}">Ispis pristupnice</a></p>
          <button type="button" class="btn btn-primary btn-sm" id="krizmanik-add-btn">+ Krizmanik</button>
        </div>
        <div id="krizma-table-mount"></div>
      </section>`;

    document.getElementById("krizmanik-add-btn")?.addEventListener("click", () => {
      window.PastoralCrudModals?.openKrizmanik(year, null, () => renderKrizmaPage());
    });

    mountPaginatedTable(
      "krizma-table-mount",
      conf.candidates,
      [
        col("name", "Ime", { render: (r) => `<strong>${escapeHtml(r.name)}</strong>` }),
        col("birthDate", "Rođen", { fmt: fmtDate }),
        col("school", "Škola"),
        col("class", "Razred"),
        col("group", "Grupa"),
        col("sponsor", "Kum/ka"),
        col("status", "Status", { badge: true }),
        {
          key: "id",
          label: "",
          render: (r) => `<button type="button" class="btn btn-ghost btn-sm" data-edit-krizmanik="${r.id}">Uredi</button>`,
        },
      ],
      `krizmanici_${year}`,
      (imported) => {
        const data = getData();
        const c = data.confirmations.find((x) => x.year === year);
        if (!c) return;
        imported.forEach((row) => {
          c.candidates.push({
            id: uid("cr"),
            name: row.Ime || row.name || row["Ime i prezime"] || "—",
            birthDate: row["Datum rođenja"] || row.birthDate || "",
            school: row.Škola || row.school || "",
            class: row.Razred || row.class || "",
            group: row.Grupa || row.group || "A",
            baptized: row.Krštenje || row.baptized || "",
            sponsor: row.Kum || row.sponsor || "",
            status: row.Status || "upis",
            oib: row.OIB || "",
          });
        });
        saveData(data);
        showToast(`Uvezeno ${imported.length} krizmanika`);
        renderKrizmaPage();
      }
    );

    if (!root.dataset.krizmanikEditBound) {
      root.dataset.krizmanikEditBound = "1";
      root.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-edit-krizmanik]");
        if (!btn) return;
        const data = getData();
        const c = data.confirmations.find((x) => x.year === parseInt(root.dataset.year || year, 10));
        const cand = c?.candidates?.find((x) => x.id === btn.dataset.editKrizmanik);
        if (cand) window.PastoralCrudModals?.openKrizmanik(c.year, cand, () => renderKrizmaPage());
      });
    }
  }

  const catPanel = document.getElementById("krizma-panel-catechists");
  if (conf && catPanel) {
    catPanel.innerHTML = `
      <section class="card">
        <div style="margin-bottom:12px"><button type="button" class="btn btn-primary btn-sm" id="kateheta-add-btn">+ Suradnik</button></div>
        <div id="katehete-table-mount"></div>
      </section>`;

    document.getElementById("kateheta-add-btn")?.addEventListener("click", () => {
      window.PastoralCrudModals?.openKateheta(year, null, () => renderKrizmaPage());
    });

    mountPaginatedTable(
      "katehete-table-mount",
      conf.catechists,
      [
        col("name", "Ime", { render: (r) => `<strong>${escapeHtml(r.name)}</strong>` }),
        col("role", "Uloga"),
        col("phone", "Telefon"),
        {
          key: "id",
          label: "",
          render: (r) => `<button type="button" class="btn btn-ghost btn-sm" data-edit-kateheta="${r.id}">Uredi</button>`,
        },
      ],
      `katehete_${year}`
    );

    if (!root.dataset.katehetaEditBound) {
      root.dataset.katehetaEditBound = "1";
      root.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-edit-kateheta]");
        if (!btn) return;
        const data = getData();
        const c = data.confirmations.find((x) => x.year === parseInt(root.dataset.year || year, 10));
        const person = c?.catechists?.find((x) => x.id === btn.dataset.editKateheta);
        if (person) window.PastoralCrudModals?.openKateheta(c.year, person, () => renderKrizmaPage());
      });
    }
  }
}

function renderPrvaPricestPage() {
  const d = getData();
  const root = document.getElementById("page-root");
  if (!root) return;
  const groups = d.firstCommunion;
  root.innerHTML = groups
    .map(
      (g) => `<section class="card" style="margin-bottom:20px">
      <h2 class="section-title">Prva sv. Pričest ${g.year} — ${escapeHtml(g.groupName)}</h2>
      <p class="card-sub">Obred: ${fmtDate(g.ceremonyDate)} · ${escapeHtml(g.celebrant)}</p>
      <h3 style="font-size:0.95rem">Prvopričesnici</h3>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Ime</th><th>Škola</th><th>Razred</th><th>Roditelji</th></tr></thead>
      <tbody>${g.candidates.map((c) => `<tr><td><strong>${escapeHtml(c.name)}</strong></td><td>${escapeHtml(c.school)}</td><td>${escapeHtml(c.class)}</td><td>${escapeHtml(c.parents)}</td></tr>`).join("")}</tbody></table></div>
      <h3 style="font-size:0.95rem">Katehete</h3>
      <ul>${g.catechists.map((k) => `<li><strong>${escapeHtml(k.name)}</strong> ${escapeHtml(k.phone || "")}</li>`).join("")}</ul>
    </section>`
    )
    .join("");
}

function renderWeddingsPage() {
  renderSacramentTable("weddings", [
    { key: "couple", label: "Par" },
    { key: "weddingDate", label: "Datum", fmt: fmtDate },
    { key: "celebrant", label: "Svećenik" },
    { key: "status", label: "Status", badge: true },
  ]);
}

function renderFuneralsPage() {
  renderSacramentTable("funerals", [
    { key: "deceased", label: "Pokojnik" },
    { key: "funeralDate", label: "Pogreb", fmt: fmtDate },
    { key: "cemetery", label: "Groblje" },
    { key: "status", label: "Status", badge: true },
  ]);
}

function rerenderSacramentPage(arrayKey) {
  if (arrayKey === "baptisms") renderBaptismsPage();
  else if (arrayKey === "weddings") renderWeddingsPage();
  else if (arrayKey === "funerals") renderFuneralsPage();
}

function renderSacramentTable(arrayKey, columnDefs, exportName) {
  const d = getData();
  const root = document.getElementById("page-root");
  if (!root) return;
  root.innerHTML = `<section class="card">
    <div style="margin-bottom:12px"><button type="button" class="btn btn-primary btn-sm" data-add-sacrament="${arrayKey}">+ Dodaj</button></div>
    <div id="sacrament-table-mount"></div></section>`;
  const cols = columnDefs.map((c, i) => {
    if (c.render) return { key: c.key, label: c.label, render: c.render };
    if (c.fmt) return col(c.key, c.label, { fmt: c.fmt });
    if (c.badge) return col(c.key, c.label, { badge: true });
    return col(c.key, c.label, { strong: i === 0 });
  });
  const Prep = window.PastoralPreparation;
  if (Prep && (arrayKey === "baptisms" || arrayKey === "weddings")) {
    Prep.migrateAll(d);
    cols.push({
      key: "prep",
      label: "Priprema",
      render: (r) => {
        const p = Prep.getProgress(r, arrayKey);
        return `<span class="badge ${p.percent === 100 ? "badge-done" : ""}">${p.percent}%</span>`;
      },
    });
  }
  cols.push({
    key: "id",
    label: "Akcije",
    render: (r) => `
      ${Prep && (arrayKey === "baptisms" || arrayKey === "weddings") ? `<button type="button" class="btn btn-ghost btn-sm" data-prep-sacrament="${arrayKey}" data-id="${r.id}">Priprema</button>` : ""}
      <button type="button" class="btn btn-ghost btn-sm" data-edit-sacrament="${arrayKey}" data-id="${r.id}">Uredi</button>
      <button type="button" class="btn btn-ghost btn-sm" data-del-sacrament="${arrayKey}" data-id="${r.id}">×</button>`,
  });
  mountPaginatedTable("sacrament-table-mount", d[arrayKey] || [], cols, exportName || arrayKey);
  if (!root.dataset.sacramentCrudBound) {
    root.dataset.sacramentCrudBound = "1";
    root.addEventListener("click", async (e) => {
      const addBtn = e.target.closest("[data-add-sacrament]");
      if (addBtn) {
        window.PastoralCrudModals?.openSacrament(addBtn.dataset.addSacrament, null, () =>
          rerenderSacramentPage(addBtn.dataset.addSacrament)
        );
        return;
      }
      const prepBtn = e.target.closest("[data-prep-sacrament]");
      if (prepBtn && window.PastoralPreparation) {
        const key = prepBtn.dataset.prepSacrament;
        const data = getData();
        const row = (data[key] || []).find((x) => x.id === prepBtn.dataset.id);
        if (!row) return;
        const Prep = window.PastoralPreparation;
        window.PastoralModal?.openDetail({
          title: `Priprema — ${row.childName || row.couple}`,
          size: "md",
          body: Prep.renderChecklistHtml(row, key, escapeHtml),
          onOpen: (overlay) => {
            Prep.bindChecklist(overlay, { getData, saveData, showToast }, key, () => {
              window.PastoralModal.close();
              rerenderSacramentPage(key);
            });
          },
        });
        return;
      }
      const editBtn = e.target.closest("[data-edit-sacrament]");
      if (editBtn) {
        const key = editBtn.dataset.editSacrament;
        const data = getData();
        const row = (data[key] || []).find((x) => x.id === editBtn.dataset.id);
        if (row) window.PastoralCrudModals?.openSacrament(key, row, () => rerenderSacramentPage(key));
        return;
      }
      const delBtn = e.target.closest("[data-del-sacrament]");
      if (!delBtn) return;
      const key = delBtn.dataset.delSacrament;
      const ok = await modalConfirm("Obrisati zapis?", { danger: true, title: "Brisanje" });
      if (!ok) return;
      const data = getData();
      data[key] = (data[key] || []).filter((x) => x.id !== delBtn.dataset.id);
      saveData(data);
      showToast("Zapis obrisan");
      rerenderSacramentPage(key);
    });
  }
}

function renderBaptismsPage() {
  renderSacramentTable(
    "baptisms",
    [
      { key: "childName", label: "Dijete" },
      { key: "baptismDate", label: "Krštenje", fmt: fmtDate },
      { key: "parents", label: "Roditelji" },
      { key: "godparents", label: "Kum(ovi)" },
      { key: "registryNo", label: "Matica" },
      { key: "status", label: "Status", badge: true },
    ],
    "krsenja"
  );
}

function findFamily(data, familyId) {
  return (data.families || []).find((f) => f.id === familyId);
}

function persistFamilies(data, familyId, root) {
  if (window.PastoralFamilyCrud) window.PastoralFamilyCrud.migrateAllFamilies(data);
  syncParishionersFromFamilies(data);
  saveData(data);
  if (root && familyId) root.dataset.family = familyId;
}

function renderContributionsSection(fam, data) {
  const FC = window.PastoralFamilyCrud;
  if (!FC) return "";
  FC.sortContributions(fam);
  const defAmt = data.luknoDefaultAmount ?? FC.DEFAULT_LUKNO;
  const rows = (fam.contributions || [])
    .map(
      (c) => `<tr data-contrib-id="${c.id}">
        <td><strong>${c.year}</strong></td>
        <td>${c.luknoPaid ? '<span class="badge badge-done">plaćeno</span>' : '<span class="badge badge-urgent">neplaćeno</span>'}</td>
        <td>${c.luknoAmount ?? defAmt} €</td>
        <td>${c.luknoPaidAt ? fmtDate(c.luknoPaidAt) : "—"}</td>
        <td>${c.churchDonation || 0} €</td>
        <td>${c.donationDate ? fmtDate(c.donationDate) : "—"}</td>
        <td>${escapeHtml(c.notes || "—")}</td>
        <td class="crud-actions">
          <button type="button" class="btn btn-ghost btn-sm" data-action="edit-year" data-fam="${fam.id}" data-year="${c.year}">Uredi</button>
          <button type="button" class="btn btn-ghost btn-sm" data-action="delete-year" data-fam="${fam.id}" data-year="${c.year}">×</button>
        </td>
      </tr>`
    )
    .join("");
  return `
    <h3 class="karton-subtitle">Lukno i davanja za crkvu (po godinama)</h3>
    <p class="card-sub">Evidencija kroz sve godine — uređivanje kroz modal.</p>
    <button type="button" class="btn btn-secondary btn-sm" data-action="add-year" data-fam="${fam.id}" style="margin-bottom:12px">+ Dodaj godinu</button>
    <div class="table-wrap"><table class="data-table contrib-table">
      <thead><tr><th>God.</th><th>Lukno</th><th>Iznos</th><th>Datum uplate</th><th>Davanje</th><th>Datum davanja</th><th>Napomena</th><th></th></tr></thead>
      <tbody>${rows || '<tr><td colspan="8" class="empty-state">Nema zapisa — dodajte godinu.</td></tr>'}</tbody>
    </table></div>`;
}

function familyDetailApi(root) {
  return {
    escapeHtml,
    fmtDate,
    pageUrl,
    getData,
    saveData,
    showToast,
    getStreetName,
    renderContributions: renderContributionsSection,
    refreshDetail: () => refreshFamilyDetailModal(root),
    confirm: modalConfirm,
  };
}

function renderFamilyDetailHtml(fam, data) {
  if (!fam) return "";
  const FL = window.PastoralFamilyList;
  if (FL) {
    window.PastoralFamilyCrud?.migrateFamily(fam);
    return FL.renderDetailHtml(fam, data, familyDetailApi(document.getElementById("page-root")));
  }
  return "";
}

function bindFamilyDetailModalActions(overlay, root) {
  if (overlay.dataset.detailBound) return;
  overlay.dataset.detailBound = "1";
  overlay.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn || !overlay.contains(btn)) return;
    e.stopPropagation();
    handleObiteljiAction(btn.dataset.action, btn, root);
  });
  window.PastoralFamilyList?.bindDetail(overlay, root, familyDetailApi(root));
}

function openFamilyDetailModal(famId, root) {
  const data = getData();
  const fam = findFamily(data, famId);
  const M = window.PastoralModal;
  if (!fam || !M) return;
  root.dataset.family = famId;
  window.PastoralPriestTools?.trackRecentFamily(famId);
  M.openDetail({
    title: `Obitelj ${fam.surname}`,
    size: "xl",
    body: renderFamilyDetailHtml(fam, data),
    onOpen: (overlay) => {
      familyDetailOverlay = overlay;
      overlay.dataset.familyDetail = famId;
      bindFamilyDetailModalActions(overlay, root);
    },
    onClose: () => {
      familyDetailOverlay = null;
      root.dataset.family = "";
    },
  });
}

function refreshFamilyDetailModal(root) {
  if (!familyDetailOverlay?.dataset.familyDetail) return;
  const famId = familyDetailOverlay.dataset.familyDetail;
  const fam = findFamily(getData(), famId);
  const M = window.PastoralModal;
  if (!fam) {
    M?.close();
    familyDetailOverlay = null;
    root.dataset.family = "";
    return;
  }
  const body = familyDetailOverlay.querySelector(".pastoral-modal-body--detail");
  if (body) body.innerHTML = renderFamilyDetailHtml(fam, getData());
  const title = familyDetailOverlay.querySelector(".pastoral-modal-title");
  if (title) title.textContent = `Obitelj ${fam.surname}`;
}

function handleObiteljiAction(action, btn, root) {
  const data = getData();

  if (action === "new-family") {
    window.PastoralCrudModals?.openFamilyCreate(root);
    return;
  }
  if (action === "edit-family") {
    window.PastoralCrudModals?.openFamilyEdit(btn.dataset.fam, root);
    return;
  }
  if (action === "delete-family") {
    const fam = findFamily(data, btn.dataset.fam);
    if (!fam) return;
    modalConfirm(`Obrisati obitelj ${fam.surname}?`, { danger: true, title: "Brisanje obitelji" }).then((ok) => {
      if (!ok) return;
      data.families = data.families.filter((f) => f.id !== fam.id);
      root.dataset.family = "";
      persistFamilies(data, null, root);
      showToast("Obitelj obrisana");
      window.PastoralModal?.close();
      familyDetailOverlay = null;
      renderObiteljiPage();
    });
    return;
  }
  if (action === "add-year") {
    window.PastoralCrudModals?.openYear(btn.dataset.fam, null, root);
    return;
  }
  if (action === "edit-year") {
    window.PastoralCrudModals?.openYear(btn.dataset.fam, Number(btn.dataset.year), root);
    return;
  }
  if (action === "delete-year") {
    const fam = findFamily(data, btn.dataset.fam);
    if (!fam) return;
    modalConfirm(`Obrisati evidenciju za ${btn.dataset.year}.?`, { danger: true }).then((ok) => {
      if (!ok) return;
      fam.contributions = (fam.contributions || []).filter((c) => c.year !== Number(btn.dataset.year));
      persistFamilies(data, fam.id, root);
      showToast("Godina uklonjena");
      renderObiteljiPage();
      refreshFamilyDetailModal(root);
    });
    return;
  }
  if (action === "add-member") {
    window.PastoralCrudModals?.openMember(btn.dataset.fam, null, root);
    return;
  }
  if (action === "delete-member") {
    const fam = findFamily(data, btn.dataset.fam);
    if (!fam) return;
    modalConfirm("Ukloniti člana?", { danger: true }).then((ok) => {
      if (!ok) return;
      fam.members = (fam.members || []).filter((m) => m.id !== btn.dataset.member);
      persistFamilies(data, fam.id, root);
      showToast("Član uklonjen");
      renderObiteljiPage();
      refreshFamilyDetailModal(root);
    });
    return;
  }
  if (action === "edit-member") {
    window.PastoralCrudModals?.openMember(btn.dataset.fam, btn.dataset.member, root);
  }
}

function bindObiteljiPage(root) {
  if (root.dataset.obiteljiBound) return;
  root.dataset.obiteljiBound = "1";

  root.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (btn) {
      handleObiteljiAction(btn.dataset.action, btn, root);
      return;
    }
    const row = e.target.closest("tr[data-family-id]");
    if (row?.dataset.familyId) {
      openFamilyDetailModal(row.dataset.familyId, root);
    }
  });
}

function obiteljiIsChildMember(m) {
  return /dijete|kć|sin|unuk/i.test(m.relation || "");
}

function obiteljiScanFamilies(families) {
  let members = 0;
  let children = 0;
  families.forEach((f) => {
    const mems = f.members || [];
    members += mems.length;
    children += mems.filter(obiteljiIsChildMember).length;
  });
  const count = families.length;
  const avg = count ? Math.round((members / count) * 10) / 10 : 0;
  return { count, members, children, avg };
}

function obiteljiFormatAvg(n) {
  return Number(n).toLocaleString("hr-HR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

function obiteljiComputeSummary(data, filtered) {
  const all = data.families || [];
  const parish = obiteljiScanFamilies(all);
  const view = obiteljiScanFamilies(filtered);
  return {
    total: all.length,
    shown: filtered.length,
    streets: (data.streets || []).length,
    members: parish.members,
    avgMembers: parish.avg,
    children: parish.children,
    viewAvg: view.avg,
    viewMembers: view.members,
    viewChildren: view.children,
  };
}

function bindObiteljiTopbar(root) {
  const btn = document.getElementById("obitelji-new-top");
  if (!btn || btn.dataset.bound) return;
  btn.dataset.bound = "1";
  btn.addEventListener("click", () => {
    window.PastoralCrudModals?.openFamilyCreate(root);
  });
}

function renderObiteljiPage() {
  const root = document.getElementById("page-root");
  if (!root) return;
  const data = getData();
  if (window.PastoralFamilyCrud) window.PastoralFamilyCrud.migrateAllFamilies(data);
  const streets = data.streets || [];
  const streetFilter = root.dataset.street || "";
  const q = root.dataset.q || "";
  const openAfterRender = root.dataset.family || "";
  const FC = window.PastoralFamilyCrud;
  const curYear = new Date().getFullYear();
  const K = window.PastoralKpi;

  let families = [...(data.families || [])];
  if (streetFilter) families = families.filter((f) => f.streetId === streetFilter);
  if (q.trim()) {
    const s = q.toLowerCase();
    families = families.filter(
      (f) =>
        f.surname?.toLowerCase().includes(s) ||
        f.address?.toLowerCase().includes(s) ||
        (f.members || []).some((m) => m.name?.toLowerCase().includes(s))
    );
  }

  const filterActive = !!(q.trim() || streetFilter);

  const summary = obiteljiComputeSummary(data, families);
  const streetName = streetFilter ? getStreetName(data, streetFilter) : "";
  const avgDisplay = filterActive ? summary.viewAvg : summary.avgMembers;
  const avgSub = filterActive
    ? `u prikazu (${summary.shown} obitelji, ${summary.viewMembers} članova)`
    : "članova po domaćinstvu u župi";
  const obiteljiHref = pageUrl("pages/obitelji.html");
  const krizmaHref = pageUrl("pages/krizma.html");

  const tableRows = families.map((f) => {
    const st = getStreetName(data, f.streetId);
    const luk = FC ? FC.currentYearStatus(f, curYear) : {};
    const addrLine = [f.address, st !== "—" ? st : ""].filter(Boolean).join(" · ") || "—";
    return {
      id: f.id,
      surname: f.surname,
      addressLine: addrLine,
      memberCount: (f.members || []).length,
      luknoBadge: luk.paid
        ? `<span class="badge badge-done">Plaćeno</span>`
        : `<span class="badge badge-urgent">Duguje</span>`,
      phone: f.phone || "—",
      openHint: `<span class="family-row-open">Otvori karton →</span>`,
    };
  });

  const activeFiltersHtml = filterActive
    ? `<div class="families-active-filters">
        ${q.trim() ? `<span class="ui-pill">Pretraga: <strong>${escapeHtml(q.trim())}</strong></span>` : ""}
        ${streetFilter ? `<span class="ui-pill">Ulica: <strong>${escapeHtml(streetName)}</strong></span>` : ""}
        <button type="button" class="btn btn-ghost btn-sm" id="fam-clear-filters">Poništi filtere</button>
      </div>`
    : "";

  root.innerHTML = `
    ${
      K
        ? K.row(
            [
              {
                tone: "pastoral",
                label: "Obitelji u župi",
                value: summary.total,
                sub: `${summary.streets} ulica / kvartova`,
                href: obiteljiHref,
              },
              { tone: "neutral", label: "Članova ukupno", value: summary.members, href: obiteljiHref },
              {
                tone: "accent",
                label: "Prosječno po obitelji",
                value: obiteljiFormatAvg(avgDisplay),
                sub: avgSub,
                href: obiteljiHref,
              },
              {
                tone: "sacrament",
                label: "Djeca u popisu",
                value: filterActive ? summary.viewChildren : summary.children,
                sub: filterActive ? "u prikazanom odabiru" : "u kartonima obitelji",
                href: krizmaHref,
              },
            ],
            { stackClass: "page-kpi-stack--obitelji", rowClass: "kpi-row--obitelji" }
          )
        : ""
    }
    <section class="card families-toolbar-card" data-no-stagger>
      <div class="families-toolbar">
        <div class="families-toolbar-search">
          <label class="families-toolbar-label" for="fam-search">Pretraga</label>
          <input type="search" id="fam-search" class="families-search-input" placeholder="Prezime, adresa ili ime člana…" value="${escapeHtml(q)}" autocomplete="off" />
        </div>
        <div class="families-toolbar-filter">
          <label class="families-toolbar-label" for="fam-street-filter">Ulica</label>
          <select id="fam-street-filter" class="families-street-select">
            <option value="">Sve ulice (${(data.families || []).length})</option>
            ${streets
              .slice()
              .sort((a, b) => (a.sortOrder || 99) - (b.sortOrder || 99))
              .map((st) => {
                const cnt = (data.families || []).filter((f) => f.streetId === st.id).length;
                return `<option value="${st.id}" ${streetFilter === st.id ? "selected" : ""}>${escapeHtml(st.name)} (${cnt})</option>`;
              })
              .join("")}
          </select>
        </div>
      </div>
      ${activeFiltersHtml}
      <p class="families-toolbar-hint">Kliknite red u tablici za obiteljski list — muž/žena, djeca, lukno i bilješke.</p>
    </section>
    <section class="card families-table-card" data-no-stagger>
      <div class="families-table-head">
        <h2 class="section-title" style="margin:0">Popis domaćinstava</h2>
        <span class="card-sub">${summary.shown} od ${summary.total} obitelji</span>
      </div>
      <div id="families-table-mount"></div>
    </section>`;

  mountPaginatedTable(
    "families-table-mount",
    tableRows,
    [
      col("surname", "Prezime", { strong: true }),
      { key: "addressLine", label: "Adresa · ulica", render: (r) => `<span class="family-addr-cell">${escapeHtml(r.addressLine)}</span>` },
      { key: "memberCount", label: "Članovi", render: (r) => `<strong>${r.memberCount}</strong>` },
      { key: "luknoBadge", label: `Lukno ${curYear}`, render: (r) => r.luknoBadge },
      col("phone", "Telefon"),
      { key: "openHint", label: "", render: (r) => r.openHint },
    ],
    "obitelji",
    null,
    (row) => ({ "data-family-id": row.id, class: "family-table-row", title: "Otvori obiteljski list" }),
    { hideToolbarSearch: true, hideImport: true, pageSize: 15 }
  );

  document.getElementById("fam-search")?.addEventListener("input", (e) => {
    root.dataset.q = e.target.value;
    renderObiteljiPage();
  });
  document.getElementById("fam-street-filter")?.addEventListener("change", (e) => {
    root.dataset.street = e.target.value;
    renderObiteljiPage();
  });
  document.getElementById("fam-clear-filters")?.addEventListener("click", () => {
    root.dataset.q = "";
    root.dataset.street = "";
    renderObiteljiPage();
  });

  bindObiteljiPage(root);
  bindObiteljiTopbar(root);

  const params = new URLSearchParams(location.search);
  if (params.get("action") === "new-family") {
    setTimeout(() => window.PastoralCrudModals?.openFamilyCreate(root), 0);
  } else if (openAfterRender && findFamily(data, openAfterRender)) {
    const famId = openAfterRender;
    root.dataset.family = "";
    setTimeout(() => openFamilyDetailModal(famId, root), 0);
  }
}

function renderUlicePage() {
  const root = document.getElementById("page-root");
  if (!root) return;
  const data = getData();
  const selectedStreet = root.dataset.street || "";

  const rows = (data.streets || [])
    .slice()
    .sort((a, b) => (a.sortOrder || 99) - (b.sortOrder || 99))
    .map((st) => {
      const fams = (data.families || []).filter((f) => f.streetId === st.id);
      return { ...st, familyCount: fams.length, families: fams };
    });

  root.innerHTML = `
    <section class="card" style="margin-bottom:16px">
      <h2 class="section-title">Ulice i kvartovi župe</h2>
      <p class="card-sub">Pregled po ulicama olakšava obilazak i pastoralno planiranje. Kliknite ulicu za obitelji na toj adresi.</p>
      <button type="button" class="btn btn-primary btn-sm" id="street-add-btn" style="margin-top:12px">+ Dodaj ulicu</button>
    </section>
    <div class="ulice-layout">
      <section class="card">
        <div id="streets-table-mount"></div>
      </section>
      <section class="card" id="street-families-panel">
        ${selectedStreet ? renderStreetFamiliesPanel(data, selectedStreet) : '<p class="empty-state">Odaberite ulicu u tablici.</p>'}
      </section>
    </div>`;

  mountPaginatedTable(
    "streets-table-mount",
    rows,
    [
      col("name", "Ulica", { strong: true }),
      col("zone", "Kvart"),
      { key: "familyCount", label: "Obitelji", render: (r) => `<strong>${r.familyCount}</strong>` },
      col("notes", "Napomena"),
      {
        key: "id",
        label: "Akcije",
        render: (r) => `
          <button type="button" class="btn btn-primary btn-sm" data-open-street="${r.id}">Prikaži</button>
          <button type="button" class="btn btn-ghost btn-sm" data-edit-street="${r.id}">Uredi</button>
          <button type="button" class="btn btn-ghost btn-sm" data-delete-street="${r.id}">×</button>`,
      },
    ],
    "ulice"
  );

  document.getElementById("street-add-btn")?.addEventListener("click", () => {
    window.PastoralCrudModals?.openStreet(null, () => renderUlicePage());
  });

  if (!root.dataset.streetDelegate) {
    root.dataset.streetDelegate = "1";
    root.addEventListener("click", (e) => {
      const openBtn = e.target.closest("[data-open-street]");
      if (openBtn) {
        root.dataset.street = openBtn.dataset.openStreet;
        renderUlicePage();
        return;
      }
      const editBtn = e.target.closest("[data-edit-street]");
      if (editBtn) {
        window.PastoralCrudModals?.openStreet(editBtn.dataset.editStreet, () => renderUlicePage());
        return;
      }
      const delBtn = e.target.closest("[data-delete-street]");
      if (delBtn) {
        const d = getData();
        const st = d.streets.find((s) => s.id === delBtn.dataset.deleteStreet);
        const used = (d.families || []).some((f) => f.streetId === delBtn.dataset.deleteStreet);
        if (!st) return;
        const msg = `Obrisati ulicu ${st.name}?${used ? " Neke obitelji su još na njoj." : ""}`;
        modalConfirm(msg, { danger: true, title: "Brisanje ulice" }).then((ok) => {
          if (!ok) return;
          d.streets = d.streets.filter((s) => s.id !== delBtn.dataset.deleteStreet);
          saveData(d);
          root.dataset.street = "";
          showToast("Ulica obrisana");
          renderUlicePage();
        });
        return;
      }
      const fam = e.target.closest("[data-goto-family]");
      if (fam) {
        location.href = `${pageUrl("pages/obitelji.html")}?family=${encodeURIComponent(fam.dataset.gotoFamily)}`;
      }
    });
  }
}

function renderStreetFamiliesPanel(data, streetId) {
  const st = data.streets.find((s) => s.id === streetId);
  const fams = (data.families || []).filter((f) => f.streetId === streetId);
  if (!st) return "";
  return `
    <h2 class="section-title">${escapeHtml(st.name)}</h2>
    <p class="card-sub">${escapeHtml(st.zone)} · ${fams.length} obitelji</p>
    ${st.notes ? `<p>${escapeHtml(st.notes)}</p>` : ""}
    <ul class="street-family-list">
      ${fams.map((f) => `<li><button type="button" class="btn btn-ghost" style="width:100%;text-align:left" data-goto-family="${f.id}"><strong>${escapeHtml(f.surname)}</strong> — ${escapeHtml(f.address || "")} (${(f.members || []).length} čl.)</button></li>`).join("") || "<li class='empty-state'>Nema upisanih obitelji.</li>"}
    </ul>
    <a href="${pageUrl("pages/obitelji.html")}?street=${streetId}" class="btn btn-primary btn-sm">Sve obitelji na ulici</a>`;
}

function importPublicSubmission(sub) {
  const data = getData();
  const PF = window.PastoralPublicForms;
  const d = sub.data || {};
  const year = new Date().getFullYear();

  if (sub.type === "krizma") {
    let conf = data.confirmations.find((c) => c.year === year);
    if (!conf) {
      conf = { id: uid("conf"), year, bishop: "", ceremonyDate: "", catechists: [], candidates: [] };
      data.confirmations.unshift(conf);
    }
    conf.candidates.push({
      id: uid("cr"),
      name: `${d.ime || ""} ${d.prezime || ""}`.trim(),
      birthDate: d.datum_rodjenja || "",
      school: d.skola || "",
      class: d.razred || "",
      group: "A",
      baptized: d.datum_krstenja || "",
      sponsor: d.kum || "",
      status: "upis",
      oib: "",
    });
  } else if (sub.type === "krstenje") {
    data.baptisms.push({
      id: uid("b"),
      childName: d.ime_djeteta || "—",
      birthDate: d.datum_rodjenja || "",
      baptismDate: d.zeljeni_termin || "",
      parents: d.roditelji || "",
      godparents: d.kumovi || "",
      celebrant: "",
      registryNo: "",
      status: "upis",
    });
  } else if (sub.type === "pricest") {
    let grp = data.firstCommunion.find((g) => g.year === year);
    if (!grp) {
      grp = { id: uid("fc"), year, groupName: "Nova skupina", celebrant: "", ceremonyDate: "", candidates: [], catechists: [] };
      data.firstCommunion.unshift(grp);
    }
    grp.candidates.push({
      id: uid("c"),
      name: d.ime_djeteta || "—",
      school: d.skola || "",
      class: d.razred || "",
      parents: d.roditelji || "",
    });
  } else if (sub.type === "ukop") {
    data.funerals.push({
      id: uid("f"),
      deceased: d.pokojnik || "—",
      deathDate: d.datum_smrti || "",
      funeralDate: d.zeljeni_datum || "",
      cemetery: d.groblje || "",
      celebrant: "",
      familyContact: `${d.kontakt || ""} ${d.telefon || ""}`.trim(),
      status: "upis",
    });
  }

  sub.status = "preuzeto";
  window.PastoralPublicForms?.ensurePublicSubmissions(data);
  saveData(data);
}

function renderJavnePrijavePage() {
  const PF = window.PastoralPublicForms;
  const root = document.getElementById("page-root");
  if (!root || !PF) return;

  const data = getData();
  PF.ensurePublicSubmissions(data);
  const subs = data.publicSubmissions || [];
  const filter = root.dataset.filter || "sve";

  const filtered = filter === "sve" ? subs : subs.filter((s) => s.status === filter);

  const nova = subs.filter((s) => s.status === "nova").length;
  const preuzeto = subs.filter((s) => s.status === "preuzeto").length;
  const K = window.PastoralKpi;

  root.innerHTML = `
    ${
      K
        ? K.row([
            { tone: "alert", label: "Nove prijave", value: nova },
            { tone: "success", label: "Preuzete", value: preuzeto },
            { tone: "neutral", label: "Ukupno", value: subs.length },
          ])
        : ""
    }
    <section class="card" style="margin-bottom:16px">
      <div class="plan-tabs">
        <button type="button" class="plan-tab ${filter === "sve" ? "active" : ""}" data-filter="sve">Sve (${subs.length})</button>
        <button type="button" class="plan-tab ${filter === "nova" ? "active" : ""}" data-filter="nova">Nove (${nova})</button>
        <button type="button" class="plan-tab ${filter === "preuzeto" ? "active" : ""}" data-filter="preuzeto">Preuzete</button>
      </div>
    </section>
    <section class="card">
      <div id="javne-prijave-table"></div>
    </section>
    <div id="javne-prijave-detail"></div>`;

  root.querySelectorAll("[data-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      root.dataset.filter = btn.dataset.filter;
      renderJavnePrijavePage();
    });
  });

  const rows = filtered.map((s) => ({
    ...s,
    typeLabel: PF.TYPE_LABELS[s.type] || s.type,
    submittedLabel: new Date(s.submittedAt).toLocaleString("hr-HR"),
    summary:
      s.type === "krizma"
        ? `${s.data?.ime || ""} ${s.data?.prezime || ""}`.trim()
        : s.data?.ime_djeteta || s.data?.pokojnik || "—",
  }));

  mountPaginatedTable(
    "javne-prijave-table",
    rows,
    [
      col("submittedLabel", "Datum"),
      col("typeLabel", "Vrsta", { badge: true }),
      col("summary", "Podnositelj", { strong: true }),
      col("status", "Status", { badge: true }),
      {
        key: "id",
        label: "",
        render: (r) =>
          r.status !== "preuzeto"
            ? `<button type="button" class="btn btn-primary btn-sm" data-import-pub="${r.id}">U evidenciju</button>`
            : '<span class="card-sub">preuzeto</span>',
      },
    ],
    "javne_prijave"
  );

  if (!root.dataset.pubDelegate) {
    root.dataset.pubDelegate = "1";
    root.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-import-pub]");
      if (!btn) return;
      const data = getData();
      const sub = (data.publicSubmissions || []).find((s) => s.id === btn.dataset.importPub);
      if (!sub) return;
      modalConfirm("Preuzeti prijavu u župnu evidenciju?", { title: "Preuzimanje prijave" }).then((ok) => {
        if (!ok) return;
        importPublicSubmission(sub);
        showToast("Prijava preuzeta u evidenciju");
        renderJavnePrijavePage();
      });
    });
  }
}

function initDocumentsPage() {
  const Doc = window.PastoralDocuments;
  const TK = window.PastoralTableKit;
  const root = document.getElementById("page-root");
  const settings = window.PastoralParish.loadSettings();
  if (!root || !Doc) return;

  let loadedRows = [];
  let loadedHeaders = [];
  let currentMapping = {};
  let currentFileName = "";

  root.innerHTML = Doc.renderDocumentsPageHtml(settings);

  function parishDefaults() {
    return {
      zupa: settings.name,
      zupnik: settings.pastor,
      danas: new Date().toLocaleDateString("hr-HR"),
    };
  }

  function getSelectedTemplate() {
    return Doc.getTemplate(document.getElementById("doc-template-select")?.value);
  }

  function readMappingFromUi() {
    const map = {};
    document.querySelectorAll("[data-map-field]").forEach((sel) => {
      if (sel.value) map[sel.dataset.mapField] = sel.value;
    });
    return map;
  }

  function buildMappingUI(tpl, headers) {
    const area = document.getElementById("doc-mapping-area");
    if (!area || !tpl) return;
    area.innerHTML = `
      <h3 class="section-title" style="font-size:0.95rem;margin-top:12px">Mapiranje stupaca → predložak</h3>
      <div class="doc-mapping-grid">${tpl.fields
        .map(
          (f) => `
        <div class="form-group">
          <label><code>{{${f}}}</code></label>
          <select data-map-field="${f}">
            <option value="">— odaberi stupac —</option>
            ${headers.map((h) => `<option value="${escapeHtml(h)}" ${currentMapping[f] === h ? "selected" : ""}>${escapeHtml(h)}</option>`).join("")}
          </select>
        </div>`
        )
        .join("")}</div>`;
    area.querySelectorAll("[data-map-field]").forEach((sel) => {
      sel.addEventListener("change", () => {
        currentMapping[sel.dataset.mapField] = sel.value;
      });
    });
  }

  function fillRowSelect() {
    const sel = document.getElementById("doc-row-select");
    if (!sel) return;
    if (!loadedRows.length) {
      sel.innerHTML = '<option value="">— učitaj datoteku —</option>';
      return;
    }
    sel.innerHTML = loadedRows
      .map((r, i) => {
        const label = r["Ime i prezime"] || r.Ime || r.name || r.Dijete || Object.values(r).find(Boolean) || `Red ${i + 1}`;
        return `<option value="${i}">${escapeHtml(String(label))}</option>`;
      })
      .join("");
  }

  function renderPreview() {
    const tpl = getSelectedTemplate();
    const box = document.getElementById("doc-preview-box");
    const rowIdx = Number(document.getElementById("doc-row-select")?.value);
    if (!tpl || !box || !loadedRows[rowIdx]) {
      if (box) box.innerHTML = '<p class="empty-state">Učitajte datoteku i odaberite red.</p>';
      return;
    }
    const mapping = readMappingFromUi();
    const values = Doc.mapRowToFields(loadedRows[rowIdx], mapping, parishDefaults());
    if (tpl.id === "raspored_nakana") {
      const d = getData();
      const weekStart = values.tjedan_od || d.intentions[0]?.date || "";
      const rows = d.intentions.filter((n) => !weekStart || n.date >= weekStart).slice(0, 14);
      values.tablica_nakana = rows
        .map(
          (n) =>
            `<tr><td>${fmtDate(n.date)}</td><td>${escapeHtml(n.massTime)}</td><td>${escapeHtml(n.intentionFor)}</td><td>${escapeHtml(n.requestedBy)}</td><td>${n.stipend || "—"} €</td></tr>`
        )
        .join("");
    }
    box.innerHTML = Doc.mergeTemplate(tpl.body, values);
  }

  async function handleDocFile(file) {
    if (!file || !TK) return;
    let parsed;
    if (file.name.match(/\.xlsx?$/i)) parsed = await TK.parseExcelFile(file);
    else parsed = TK.parseCsv(await file.text());
    loadedRows = parsed.rows;
    loadedHeaders = parsed.headers;
    currentFileName = file.name;
    document.getElementById("doc-file-status").textContent = `${file.name} — ${loadedRows.length} redova`;
    const tpl = getSelectedTemplate();
    buildMappingUI(tpl, loadedHeaders);
    fillRowSelect();
    renderPreview();
  }

  function refreshTemplateUi() {
    const tpl = getSelectedTemplate();
    const fieldsEl = document.getElementById("doc-template-fields");
    if (tpl && fieldsEl) {
      fieldsEl.innerHTML = `<p class="card-sub">Polja: ${tpl.fields.map((f) => `<code>{{${f}}}</code>`).join(" · ")}</p>`;
    }
    const binding = Doc.loadBindings().find((b) => b.templateId === tpl?.id);
    if (binding) {
      loadedRows = binding.rows || [];
      loadedHeaders = binding.headers || (loadedRows[0] ? Object.keys(loadedRows[0]) : []);
      currentMapping = { ...(binding.mapping || {}) };
      currentFileName = binding.fileName;
      document.getElementById("doc-file-status").textContent = `Spremljeno: ${binding.fileName} (${binding.rowCount} redova)`;
      buildMappingUI(tpl, loadedHeaders);
      fillRowSelect();
    } else if (tpl) {
      buildMappingUI(tpl, loadedHeaders);
    }
    renderPreview();
  }

  document.getElementById("doc-template-select")?.addEventListener("change", () => {
    loadedRows = [];
    loadedHeaders = [];
    currentMapping = {};
    currentFileName = "";
    document.getElementById("doc-file-status").textContent = "Nema učitane datoteke za ovaj predložak.";
    refreshTemplateUi();
  });

  document.getElementById("doc-file-upload")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (file) await handleDocFile(file);
  });

  document.getElementById("doc-save-binding")?.addEventListener("click", () => {
    const tpl = getSelectedTemplate();
    if (!tpl || !loadedRows.length) {
      showToast("Učitajte Excel/CSV prije spremanja");
      return;
    }
    const mapping = readMappingFromUi();
    const list = Doc.loadBindings().filter((b) => b.templateId !== tpl.id);
    list.push({
      id: uid("bind"),
      templateId: tpl.id,
      templateName: tpl.name,
      fileName: currentFileName || "datoteka.csv",
      rowCount: loadedRows.length,
      mapping,
      headers: loadedHeaders,
      rows: loadedRows,
    });
    Doc.saveBindings(list);
    showToast("Povezivanje spremljeno");
    initDocumentsPage();
  });

  document.getElementById("doc-preview-btn")?.addEventListener("click", renderPreview);
  document.getElementById("doc-row-select")?.addEventListener("change", renderPreview);

  document.getElementById("doc-print-btn")?.addEventListener("click", () => {
    renderPreview();
    const tpl = getSelectedTemplate();
    const html = document.getElementById("doc-preview-box")?.innerHTML;
    if (tpl && html) Doc.printHtml(html, tpl.name);
  });

  root.querySelectorAll("[data-del-binding]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-del-binding");
      Doc.saveBindings(Doc.loadBindings().filter((b) => b.id !== id));
      showToast("Povezivanje uklonjeno");
      initDocumentsPage();
    });
  });

  refreshTemplateUi();
}

function mountCanonCompliance(page) {
  const C = window.PastoralCanon;
  if (!C || page === "login" || page === "index") return;
  setTimeout(() => {
    C.mountIntoPage(page, { getData, pageUrl, escapeHtml });
  }, 0);
}

function initLoginPage() {
  window.PastoralParish.applyTheme();
  if (window.PastoralTheme) window.PastoralTheme.initThemePicker({ fixed: true });
  const secNote = document.getElementById("login-security-mount");
  if (secNote && window.PastoralSecurity) {
    secNote.innerHTML = window.PastoralSecurity.enhanceLoginHtml();
    const link = document.getElementById("login-security-link");
    if (link) link.href = pageUrl("pages/sigurnost.html");
    document.getElementById("login-gdpr-privacy-btn")?.addEventListener("click", () => window.PastoralGdpr?.openPrivacyModal());
  }
  const gdprMount = document.getElementById("login-gdpr-mount");
  if (gdprMount && window.PastoralGdpr) {
    gdprMount.innerHTML = window.PastoralGdpr.renderStaffLoginBlock();
    const cb = document.getElementById("gdpr-staff-consent");
    if (cb && window.PastoralGdpr.staffAccepted()) cb.checked = true;
    window.PastoralGdpr.bindPrivacyTriggers(gdprMount);
  }
  if (parseSession()) {
    location.href = pageUrl("app.html");
    return;
  }
  document.getElementById("login-forgot")?.addEventListener("click", (e) => {
    e.preventDefault();
    window.PastoralModal?.openDetail({
      title: "Oporavak pristupa (demo)",
      body: `<p class="card-sub">Kod za prijavu šalje se na e-mail administratora (OTP). Zaboravljena lozinka: kontakt župnog ureda.</p><p>U produkciji: oporavak putem servera i HTTPS, kao u <a href="https://zupni-ured.com.hr/manual.pdf" target="_blank" rel="noopener">župni-ured</a> priručniku.</p>`,
    });
  });

  function completeStaffLogin({ email, legacyRole }) {
    window.PastoralData.ensureSeed();
    const data = getData();
    const now = Date.now();
    const permPayload = window.PastoralPermissions
      ? window.PastoralPermissions.buildSessionPayload({ email, legacyRole, data })
      : {};
    localStorage.setItem(
      window.PastoralParish.SESSION_KEY,
      JSON.stringify({
        email,
        role: legacyRole,
        loginAt: now,
        expiresAt: now + SESSION_HOURS * 3600000,
        ...permPayload,
      })
    );
    showToast("Dobrodošli");
    window.PastoralLoginReveal?.scheduleAfterLogin();
    location.href = pageUrl("app.html");
  }

  if (window.PastoralOtpAuth) {
    window.PastoralOtpAuth.initLoginFlow({
      showToast,
      validateGdpr: () => !window.PastoralGdpr || window.PastoralGdpr.validateStaffConsent(),
      completeLogin: completeStaffLogin,
    });
  } else {
    document.getElementById("login-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      if (window.PastoralGdpr && !window.PastoralGdpr.validateStaffConsent()) {
        showToast("Potvrdite povjerljivost podataka župljana (GDPR)");
        return;
      }
      completeStaffLogin({
        email: document.getElementById("login-email")?.value,
        legacyRole: document.getElementById("login-role")?.value,
      });
    });
  }
}

function initPostavkePage() {
  const P = window.PastoralParish;
  const s = P.loadSettings();
  document.getElementById("settings-name").value = s.name || "";
  document.getElementById("settings-pastor").value = s.pastor || "";
  document.getElementById("settings-phone").value = s.phone || "";
  document.getElementById("settings-email").value = s.email || "";
  document.getElementById("settings-logo").value = s.logoUrl || "";
  const prev = document.getElementById("branding-preview");
  if (prev) prev.innerHTML = P.renderLogoHtml(true);

  const hw = document.getElementById("settings-handwriting-font");
  const prn = document.getElementById("settings-printer");
  const cur = P.loadSettings();
  if (hw) hw.checked = !!cur.handwritingPrint;
  if (prn) prn.value = cur.printerName || "";

  document.getElementById("settings-save")?.addEventListener("click", () => {
    P.saveSettings({
      name: document.getElementById("settings-name").value.trim(),
      shortName: document.getElementById("settings-name").value.trim().slice(0, 20),
      pastor: document.getElementById("settings-pastor").value.trim(),
      phone: document.getElementById("settings-phone").value.trim(),
      email: document.getElementById("settings-email").value.trim(),
      logoUrl: document.getElementById("settings-logo").value.trim(),
      handwritingPrint: !!document.getElementById("settings-handwriting-font")?.checked,
      printerName: document.getElementById("settings-printer")?.value.trim() || "",
    });
    P.applyTheme();
    showToast("Postavke spremljene");
  });

  document.getElementById("settings-export")?.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(getData(), null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "zupa-export.json";
    a.click();
  });

  document.getElementById("settings-onboarding-restart")?.addEventListener("click", () => {
    window.PastoralOnboarding?.restart();
  });

  document.getElementById("settings-reset")?.addEventListener("click", () => {
    modalConfirm("Vratiti demo podatke? Briše trenutnu evidenciju.", { danger: true, title: "Reset demo podataka" }).then((ok) => {
      if (!ok) return;
      localStorage.removeItem("pastoral_data");
      window.PastoralData.save(window.PastoralData.defaultData());
      showToast("Demo podaci učitani");
      setTimeout(() => location.reload(), 400);
    });
  });

  const secMount = document.getElementById("settings-security-mount");
  if (secMount) {
    secMount.innerHTML = `
      <p class="card-sub">Pristup po ulogama, GDPR, odvojen javni portal — priprema za razgovor s župom.</p>
      <a href="${pageUrl("pages/sigurnost.html")}" class="btn btn-primary btn-sm">Otvori Sigurnost</a>
      <a href="${pageUrl("public/index.html")}" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Javni portal ↗</a>`;
  }

  const decree = getData().parishDecree;
  const decreeEl = document.getElementById("settings-parish-decree");
  if (decreeEl && decree) {
    decreeEl.innerHTML = `<p class="card-sub">${escapeHtml(decree.decreeRef || "")} · ${escapeHtml(decree.territory || "")}</p>`;
  }
}

async function initPage() {
  await loadCanonComplianceScript();
  const page = document.body.dataset.page;
  if (page !== "login") {
    await loadPermissionsEngine();
    await loadSidebarNav();
    await loadGdprEngine();
    await loadUiPolish();
    await loadKpiTheme();
    if (page === "dashboard") {
      await loadAnalyticsEngine();
    } else {
      document.getElementById("ui-nav-charts-strip")?.remove();
    }
  }
  initCrudModalsApi();

  if (page === "index") {
    location.href = pageUrl("login.html");
    return;
  }

  if (page === "login") {
    initLoginPage();
    return;
  }

  if (!requireSession()) return;
  window.PastoralData.ensureSeed();
  const sess = parseSession();
  if (page && window.PastoralPermissions && !window.PastoralPermissions.canAccessPage(page, sess)) {
    showToast("Nemate pristup ovom modulu");
    location.href = pageUrl("app.html");
    return;
  }
  initShell();

  if (page === "dashboard") renderDashboard();
  if (page === "nakane") initNakanePage();
  if (page === "krizma") renderKrizmaPage();
  if (page === "prva-pricest") renderPrvaPricestPage();
  if (page === "krsenja") renderBaptismsPage();
  if (page === "vjencanja") renderWeddingsPage();
  if (page === "pogrebi") renderFuneralsPage();
  if (page === "mise") initMisePage();
  if (page === "pomazanje") {
    const d = getData();
    const el = document.getElementById("page-root");
    if (el) {
      el.innerHTML = `<section class="card"><div id="pomazanje-table-mount"></div></section>`;
      mountPaginatedTable(
        "pomazanje-table-mount",
        d.anointing,
        [
          col("person", "Osoba", { strong: true }),
          col("address", "Adresa"),
          col("scheduled", "Datum", { fmt: fmtDate }),
          col("priest", "Svećenik"),
          { key: "done", label: "Obavljeno", render: (r) => (r.done ? '<span class="badge badge-done">✓</span>' : "—") },
        ],
        "pomazanje"
      );
    }
  }
  if (page === "vjernici") {
    location.href = pageUrl("pages/obitelji.html");
    return;
  }
  if (page === "obitelji") {
    const root = document.getElementById("page-root");
    const params = new URLSearchParams(location.search);
    if (root) {
      if (params.get("street")) root.dataset.street = params.get("street");
      if (params.get("family")) root.dataset.family = params.get("family");
    }
    renderObiteljiPage();
  }
  if (page === "ulice") renderUlicePage();
  if (page === "kalendar") {
    const d = getData();
    const el = document.getElementById("page-root");
    if (el && window.PastoralLiturgical) {
      window.PastoralLiturgical.renderKalendarPage(el, d.events || []);
    } else if (el) {
      el.innerHTML = `<section class="card">${(d.events || []).map((e) => `<div class="list-item"><strong>${escapeHtml(e.title)}</strong><br><small>${fmtDate(e.date)} · ${escapeHtml(e.place)}</small></div>`).join("")}</section>`;
    }
  }
  if (page === "zadaci") {
    const el = document.getElementById("page-root");
    if (!el) return;
    const d = getData();
    el.innerHTML = `
      <section class="card">
        <div style="margin-bottom:12px"><button type="button" class="btn btn-primary btn-sm" id="task-add-btn">+ Dodaj zadatak</button></div>
        <div id="zadaci-table-mount"></div>
      </section>`;
    mountPaginatedTable(
      "zadaci-table-mount",
      d.tasks,
      [
        col("title", "Zadatak", { strong: true }),
        col("category", "Kategorija", { badge: true }),
        col("due", "Rok", { fmt: fmtDate }),
        col("priority", "Prioritet"),
        {
          key: "done",
          label: "Status",
          render: (r) => (r.done ? '<span class="badge badge-done">gotovo</span>' : '<span class="badge">otvoreno</span>'),
        },
        {
          key: "id",
          label: "Akcije",
          render: (r) => `
            <button type="button" class="btn btn-ghost btn-sm" data-edit-task="${r.id}">Uredi</button>
            <button type="button" class="btn btn-ghost btn-sm" data-del-task="${r.id}">×</button>`,
        },
      ],
      "zadaci"
    );
    document.getElementById("task-add-btn")?.addEventListener("click", () => {
      window.PastoralCrudModals?.openTask(null, () => initPage());
    });
    if (!el.dataset.taskCrud) {
      el.dataset.taskCrud = "1";
      el.addEventListener("click", async (ev) => {
        const del = ev.target.closest("[data-del-task]");
        const edit = ev.target.closest("[data-edit-task]");
        const data = getData();
        if (edit) {
          const t = data.tasks.find((x) => x.id === edit.dataset.editTask);
          if (t) window.PastoralCrudModals?.openTask(t, () => initPage());
          return;
        }
        if (del) {
          const ok = await modalConfirm("Obrisati zadatak?", { danger: true });
          if (!ok) return;
          data.tasks = data.tasks.filter((t) => t.id !== del.dataset.delTask);
          saveData(data);
          showToast("Zadatak obrisan");
          initPage();
        }
      });
    }
  }
  if (page === "dokumenti") initDocumentsPage();
  if (page === "javne-prijave") renderJavnePrijavePage();
  if (page === "komunikacija") {
    const d = getData();
    const el = document.getElementById("page-root");
    if (el) {
      el.innerHTML = `<div id="msg-section-mount"></div>${d.announcements.map((a) => `<section class="card" style="margin-bottom:12px"><h3 class="section-title">${escapeHtml(a.title)}</h3><p>${escapeHtml(a.body)}</p></section>`).join("")}`;
      window.PastoralMessages?.mountMessagesSection(document.getElementById("msg-section-mount"), {
        getData,
        getSettings: () => window.PastoralParish.loadSettings(),
        showToast,
      });
    }
  }
  if (page === "podsjetnici") {
    const el = document.getElementById("page-root");
    window.PastoralReminders?.mountPodsjetniciPage(el, { getData, pageUrl, escapeHtml, showToast });
  }
  if (page === "posjete") {
    const el = document.getElementById("page-root");
    window.PastoralVisits?.mountVisitsPage(el, {
      getData,
      saveData,
      uid,
      pageUrl,
      escapeHtml,
      fmtDate,
      showToast,
    });
  }
  if (page === "blagajna") {
    const el = document.getElementById("page-root");
    window.PastoralCashbook?.mountCashbookPage(el, {
      getData,
      saveData,
      uid,
      pageUrl,
      escapeHtml,
      fmtDate,
      showToast,
      getSettings: () => window.PastoralParish.loadSettings(),
    });
  }
  if (page === "korisnici") {
    await loadUsersGroupsEngine();
    const el = document.getElementById("page-root");
    window.PastoralUsersGroups?.mountKorisniciPage(el, {
      getData,
      saveData,
      pageUrl,
      escapeHtml,
      showToast,
    });
  }
  if (page === "postavke") initPostavkePage();
  if (page === "sigurnost") {
    const el = document.getElementById("page-root");
    if (el && window.PastoralSecurity) {
      window.PastoralSecurity.mountSecurityPage(el, { escapeHtml, showToast, pageUrl });
    }
  }
  if (page === "dugovanja") {
    const el = document.getElementById("page-root");
    if (el && window.PastoralDebts) {
      window.PastoralDebts.mountDebtsPage(el, {
        getData,
        saveData,
        pageUrl,
        escapeHtml,
        fmtDate,
        showToast,
      });
    }
  }
  if (page === "zupni-listic") {
    const el = document.getElementById("page-root");
    if (el && window.PastoralZupniListic) {
      window.PastoralZupniListic.mountZupniListicPage(el, {
        getData,
        saveData,
        getSettings: () => window.PastoralParish.loadSettings(),
        pageUrl,
        escapeHtml,
        showToast,
        uid,
      });
    }
  }
  if (page === "potvrde") {
    const el = document.getElementById("page-root");
    if (el && window.PastoralPotvrde) {
      window.PastoralPotvrde.mountPotvrdePage(el, {
        getData,
        getSettings: () => window.PastoralParish.loadSettings(),
        pageUrl,
        escapeHtml,
      });
    }
  }
  if (page === "racuni") {
    const el = document.getElementById("page-root");
    if (el && window.PastoralInvoices) {
      window.PastoralInvoices.mountInvoicesPage(el, {
        getData,
        saveData,
        uid,
        pageUrl,
        escapeHtml,
        fmtDate,
        showToast,
      });
    }
  }
  if (page === "maticne-knjige") {
    const el = document.getElementById("page-root");
    if (el && window.PastoralCanon) {
      window.PastoralCanon.mountMaticneKnjigePage(el, { getData, pageUrl, escapeHtml, fmtDate });
    }
  }
  if (page === "vijeca") {
    const el = document.getElementById("page-root");
    if (el && window.PastoralCanon) {
      window.PastoralCanon.mountVijecaPage(el, { getData, pageUrl, escapeHtml, fmtDate });
    }
  }
  if (page === "formulari") {
    const el = document.getElementById("page-root");
    window.PastoralZupniForms?.mountFormulariPage(el, {
      getSettings: () => window.PastoralParish.loadSettings(),
      getData,
      pageUrl,
      escapeHtml,
      showToast,
    });
  }
  if (page === "poruke") {
    const el = document.getElementById("page-root");
    window.PastoralStaffMessages?.mountPorukePage(el, { getData, saveData, pageUrl, escapeHtml, showToast });
  }
  if (page === "financijska-izvjestaja") {
    const el = document.getElementById("page-root");
    window.PastoralFinanceAdv?.mountFinanceReportsPage(el, { getData, pageUrl, escapeHtml, showToast });
  }
  if (page === "admin-paket") {
    const el = document.getElementById("page-root");
    window.PastoralAdminDocs?.mountAdminPaketPage(el, {
      getData,
      getSettings: () => window.PastoralParish.loadSettings(),
      pageUrl,
      escapeHtml,
      fmtDate,
      showToast,
    });
  }

  mountCanonCompliance(page);

  requestAnimationFrame(() => {
    window.PastoralUiPolish?.refresh();
  });
}

document.addEventListener("DOMContentLoaded", initPage);
