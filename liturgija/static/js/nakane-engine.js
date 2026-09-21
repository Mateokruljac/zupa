/**
 * Misne nakane — klijentski prikaz (Danas / Kalendar / Sve nakane).
 *
 * Podaci dolaze iz Django bootstrap JSON-a (#nakane-bootstrap-data),
 * a CRUD ide preko PastoralApi.action() (server vraća osvježene podatke).
 * Liturgijski sadržaj puni PastoralLiturgical iz baze (HILP je poveznica).
 */
(function (global) {
  "use strict";

  const VIEW_MODES = ["today", "calendar", "evidence"];
  const MODE_KEY = "nakane-view-mode";

  const state = {
    intentions: [],
    massSchedule: [],
    massExceptions: [],
    selectedDate: isoToday(),
    calendarMonth: new Date(),
    defaultStipend: 0,
    tableSort: { key: "date", dir: "asc" },
    tableFilter: { search: "", status: "all" },
    tablePage: 1,
  };

  const TABLE_PAGE_SIZE = 15;

  /* ---------- pomoćne ---------- */

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function isoToday() {
    return new Date().toISOString().slice(0, 10);
  }

  function fmtDate(iso) {
    if (!iso) return "—";
    return new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  function fmtLongDate(iso) {
    return new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  function toMins(t) {
    const [h, m] = String(t || "0:0").split(":").map(Number);
    return (h || 0) * 60 + (m || 0);
  }

  function num(v) {
    return Number(v) || 0;
  }

  function showToast(msg) {
    if (typeof global.showToast === "function") {
      global.showToast(msg);
      return;
    }
    document.querySelector(".toast")?.remove();
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2800);
  }

  /* ---------- podaci / CRUD ---------- */

  function readBootstrap() {
    const el = document.getElementById("nakane-bootstrap-data");
    if (!el) return {};
    try {
      return JSON.parse(el.textContent);
    } catch {
      return {};
    }
  }

  function syncFromData(data) {
    if (!data) return;
    if (Array.isArray(data.intentions)) state.intentions = data.intentions;
    if (Array.isArray(data.massSchedule)) state.massSchedule = data.massSchedule;
    if (Array.isArray(data.massExceptions)) state.massExceptions = data.massExceptions;
  }

  async function runAction(name, payload) {
    const Api = global.PastoralApi;
    if (!Api?.action) {
      showToast("API nije učitan");
      throw new Error("no_api");
    }
    const res = await Api.action(name, payload);
    if (res?.data) syncFromData(res.data);
    return res;
  }

  function dayIntentions(iso) {
    return state.intentions
      .filter((n) => n.date === iso)
      .sort((a, b) => String(a.massTime || "").localeCompare(String(b.massTime || "")));
  }

  function scheduleEntryAppliesOnDate(entry, iso) {
    if (entry.validFrom && iso < entry.validFrom) return false;
    if (entry.validUntil && iso > entry.validUntil) return false;
    return true;
  }

  function weekdaysFromScheduleEntry(entry) {
    if (Array.isArray(entry.weekdays) && entry.weekdays.length) return entry.weekdays.map(Number);
    return [];
  }

  function massesForDate(iso) {
    const schedule = state.massSchedule || [];
    const exceptions = state.massExceptions || [];
    const exc = exceptions.find((e) => e.date === iso);
    const dow = new Date(iso + "T12:00:00").getDay();

    const noMassPeriod = schedule.some((entry) => {
      if (!entry.noMass) return false;
      if (!scheduleEntryAppliesOnDate(entry, iso)) return false;
      return weekdaysFromScheduleEntry(entry).includes(dow);
    });
    if (noMassPeriod) return [];

    const slots = [];
    if (!exc?.cancelAll) {
      schedule.forEach((entry) => {
        if (entry.noMass) return;
        if (!scheduleEntryAppliesOnDate(entry, iso)) return;
        if (!weekdaysFromScheduleEntry(entry).includes(dow)) return;
        if ((exc?.cancelTimes || []).includes(entry.time)) return;
        if (entry.time) slots.push({ time: entry.time });
      });
    }
    (exc?.addSlots || []).forEach((add) => {
      if (add.time) slots.push({ time: add.time });
    });
    slots.sort((a, b) => String(a.time).localeCompare(String(b.time)));
    return slots;
  }

  function massTimeOptions(iso) {
    return massesForDate(iso).map((slot) => slot.time).filter(Boolean);
  }

  function nextMassHint(iso, list) {
    if (iso !== isoToday()) return "";
    const times = massTimeOptions(iso);
    if (!times.length) return "Danas nema upisanih misa.";
    const now = new Date().getHours() * 60 + new Date().getMinutes();
    const upcoming = times
      .filter((t) => toMins(t) >= now - 30)
      .sort((a, b) => toMins(a) - toMins(b))[0];
    if (!upcoming) return "Sve mise za danas su prošle.";
    const count = list.filter((n) => n.massTime === upcoming).length;
    return `Sljedeća misa: ${upcoming} — ${count} nakana`;
  }

  /* ---------- mod prikaza ---------- */

  function getMode() {
    try {
      const m = sessionStorage.getItem(MODE_KEY);
      if (VIEW_MODES.includes(m)) return m;
    } catch {
      /* ignore */
    }
    return "today";
  }

  function setMode(mode, opts = {}) {
    if (!VIEW_MODES.includes(mode)) return;
    try {
      sessionStorage.setItem(MODE_KEY, mode);
    } catch {
      /* ignore */
    }
    if (mode === "today") {
      state.selectedDate = isoToday();
      state.calendarMonth = new Date();
    }
    applyMode();
    refresh();
    if (opts.scrollTo) {
      requestAnimationFrame(() => {
        document.getElementById(opts.scrollTo)?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }

  function applyMode() {
    const layout = document.getElementById("nakane-root");
    if (!layout) return;
    const mode = getMode();
    layout.classList.remove("nakane-mode-today", "nakane-mode-calendar", "nakane-mode-evidence");
    layout.classList.add(`nakane-mode-${mode}`);
  }

  /* ---------- naredbena traka ---------- */

  function renderCommandBar() {
    const layout = document.getElementById("nakane-root");
    if (!layout) return;
    let bar = document.getElementById("nakane-command-bar");
    if (!bar) {
      bar = document.createElement("section");
      bar.id = "nakane-command-bar";
      bar.className = "card nakane-command-bar";
      layout.insertBefore(bar, layout.firstChild);
    }

    const mode = getMode();
    const today = isoToday();
    if (mode === "today") state.selectedDate = today;
    const activeIso = mode === "today" ? today : state.selectedDate || today;
    const list = dayIntentions(activeIso);
    const unrecordedContributions = list.filter((n) => !n.paid).length;
    const hint = mode === "evidence" ? "" : nextMassHint(activeIso, list);

    let meta;
    if (mode === "evidence") {
      const s = computeStats();
      meta = `<strong class="nakane-command-date">Sve nakane</strong>
        <span class="card-sub">${s.total} ukupno · ${s.unpaid} bez evidentiranog stipendija · ${num(s.paidRevenue)} € od plaćenih</span>`;
    } else {
      meta = `<strong class="nakane-command-date">${esc(fmtDate(activeIso))}</strong>
        <span class="card-sub">${list.length} nakana${unrecordedContributions ? ` · ${unrecordedContributions} bez evidentiranog stipendija` : ""}</span>
        ${hint ? `<span class="nakane-next-mass">${esc(hint)}</span>` : ""}`;
    }

    const tabs = [
      ["today", "Danas"],
      ["calendar", "Kalendar"],
      ["evidence", "Sve nakane"],
    ]
      .map(
        ([id, label]) =>
          `<button type="button" class="nakane-mode-tab${mode === id ? " is-active" : ""}" data-nakane-mode="${id}" role="tab" aria-selected="${mode === id}">${label}</button>`
      )
      .join("");

    const canAddIntention = mode === "evidence" || massTimeOptions(activeIso).length > 0;

    bar.innerHTML = `
      <div class="nakane-command-inner">
        <div class="nakane-mode-tabs" role="tablist" aria-label="Prikaz nakana">${tabs}</div>
        <div class="nakane-command-meta">${meta}</div>
        <div class="nakane-command-actions">
          ${mode !== "evidence" ? `<button type="button" class="btn btn-secondary btn-sm" id="nakane-cmd-print">Ispis</button>` : ""}
          ${canAddIntention ? `<button type="button" class="btn btn-primary btn-sm" id="nakane-cmd-add">+ Nova nakana</button>` : `<span class="card-sub">Nema mise — nakane se ne upisuju</span>`}
        </div>
      </div>`;

    bar.querySelectorAll("[data-nakane-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const next = btn.dataset.nakaneMode;
        setMode(next, { scrollTo: next === "evidence" ? "nakane-evidence" : "nakane-workspace" });
      });
    });
    bar.querySelector("#nakane-cmd-print")?.addEventListener("click", () => {
      const printDate =
        getMode() === "today" ? isoToday() : state.selectedDate || isoToday();
      printDay(printDate);
    });
    bar.querySelector("#nakane-cmd-add")?.addEventListener("click", () => {
      if (mode === "evidence" && !state.selectedDate) state.selectedDate = today;
      openAddModal(mode === "today" ? today : state.selectedDate || today);
    });
  }

  /* ---------- dnevni panel ---------- */

  function renderDayList(list) {
    if (!list.length) return '<p class="empty-state">Nema nakana za ovaj dan.</p>';
    const byMass = {};
    list.forEach((n) => {
      const t = n.massTime || "—";
      (byMass[t] = byMass[t] || []).push(n);
    });
    return Object.keys(byMass)
      .sort()
      .map((massTime) => {
        const items = byMass[massTime];
        return `<div class="nakane-mass-group">
          <div class="nakane-mass-group-head">
            <h3 class="nakane-mass-time">Misa ${esc(massTime)}</h3>
            <button type="button" class="btn btn-ghost btn-sm" data-print-mass="${esc(massTime)}" title="Ispis ove mise">Ispis</button>
          </div>
          ${items
            .map(
              (n) => `<div class="list-item nakane-day-item" data-intent-id="${n.id}">
            <div>
              <strong>${esc(n.intentionFor)}</strong>
              <br><small>${num(n.stipend)} €</small>
              ${n.notes ? `<br><small class="nakane-day-notes">📝 ${esc(n.notes)}</small>` : ""}
              ${n.paid && n.paymentId ? `<br><small class="card-sub">Ref: ${esc(n.paymentId)}</small>` : ""}
            </div>
            <div class="nakana-item-actions">
              ${n.paid ? '<span class="badge badge-done">stipendij evidentiran</span>' : '<span class="badge badge-urgent">stipendij nije evidentiran</span>'}
              <button type="button" class="btn btn-ghost btn-sm" data-edit-intent="${n.id}">Uredi</button>
              ${!n.paid ? `<button type="button" class="btn btn-primary btn-sm" data-pay-intent="${n.id}">Evidentiraj stipendij</button>` : ""}
              <button type="button" class="btn btn-ghost btn-sm" data-del-intent="${n.id}">Obriši</button>
            </div>
          </div>`
            )
            .join("")}
        </div>`;
      })
      .join("");
  }

  function renderDayPanel() {
    const panel = document.getElementById("nakane-day-panel");
    if (!panel) return;
    const iso = state.selectedDate || isoToday();
    const L = global.PastoralLiturgical;
    const litLoading = L ? L.renderNakaneLitLoading(iso) : "";
    panel.innerHTML = `
      <section class="card nakane-day-card">
        ${litLoading}
        <div class="nakane-day-list">${renderDayList(dayIntentions(iso))}</div>
      </section>`;
    loadDayLiturgy(iso);
    bindRowActions(panel);
  }

  async function loadDayLiturgy(iso) {
    const L = global.PastoralLiturgical;
    if (!L || iso !== state.selectedDate) return;
    const slot = document.getElementById("nakane-lit-detail");
    if (!slot) return;
    try {
      const day = await L.getDay(iso);
      if (iso !== state.selectedDate) return;
      slot.outerHTML = L.renderNakaneDayLiturgy(day);
    } catch {
      if (iso !== state.selectedDate) return;
      slot.outerHTML = L.renderNakaneDayLiturgy({
        source: "offline",
        date: iso,
        title: null,
        hilpUrl: L.hilpUrlForDate(iso),
      });
    }
  }

  /* ---------- kalendar ---------- */

  function buildMonthGrid(year, month) {
    const first = new Date(year, month, 1);
    const startPad = (first.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cells = [];
    for (let i = 0; i < startPad; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) {
      cells.push(`${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`);
    }
    return cells;
  }

  function renderCalNakaneList(list, maxVisible = 3) {
    if (!list?.length) return "";
    const shown = list.slice(0, maxVisible);
    const rest = list.length - shown.length;
    return `<div class="cal-nakane-list">
      ${shown.map((n) => `<span class="cal-nakane-item" title="${esc(n.intentionFor)}">${esc(n.intentionFor)}</span>`).join("")}
      ${rest > 0 ? `<span class="cal-nakane-more">+ ${rest} više</span>` : ""}
    </div>`;
  }

  function renderCalendar() {
    const calEl = document.getElementById("nakane-calendar");
    if (!calEl) return;
    const y = state.calendarMonth.getFullYear();
    const m = state.calendarMonth.getMonth();
    const cells = buildMonthGrid(y, m);
    const monthLabel = state.calendarMonth.toLocaleDateString("hr-HR", { month: "long", year: "numeric" });

    const byDate = {};
    state.intentions.forEach((n) => {
      (byDate[n.date] = byDate[n.date] || []).push(n);
    });

    const L = global.PastoralLiturgical;
    const litSummaries = L ? L.summariesForMonth(y, m) : {};
    const litLoaded = Object.values(litSummaries).some((s) => s.loaded);
    const litWarn =
      L && !litLoaded
        ? `<p class="card-sub cal-lit-warn">Liturgijski kalendar se učitava…</p>`
        : "";
    const weekDays = ["Pon", "Uto", "Sri", "Čet", "Pet", "Sub", "Ned"];

    calEl.innerHTML = `
      <h2 class="section-title">Kalendar misnih nakana</h2>
      ${litWarn}
      <div class="cal-header">
        <button type="button" class="btn btn-ghost btn-sm" id="cal-prev">‹</button>
        <strong class="cal-month-title">${esc(monthLabel)}</strong>
        <button type="button" class="btn btn-ghost btn-sm" id="cal-next">›</button>
        <button type="button" class="btn btn-secondary btn-sm" id="cal-today">Danas</button>
      </div>
      <div class="cal-weekdays">${weekDays.map((w) => `<span>${w}</span>`).join("")}</div>
      <div class="cal-grid cal-grid--lit">${cells
        .map((iso) => {
          if (!iso) return '<div class="cal-cell cal-empty"></div>';
          const sel = state.selectedDate === iso ? " cal-selected" : "";
          const isToday = iso === isoToday() ? " cal-today" : "";
          const sum = L ? litSummaries[iso] || L.getSummarySync(iso) : null;
          const litBgCls = sum?.loaded && sum?.color && L ? L.liturgicalCellClass(sum.color) : "";
          const litHtml = L ? L.renderCellLiturgy(sum) : "";
          const tip = sum?.loaded
            ? [sum.title, sum.rankLabel || sum.rank, sum.colorLabel, sum.subtitle].filter(Boolean).join(" · ")
            : "Liturgijski dan";
          const dayList = (byDate[iso] || [])
            .slice()
            .sort((a, b) => String(a.massTime || "").localeCompare(String(b.massTime || "")));
          return `<button type="button" class="cal-cell cal-cell--lit ${litBgCls}${sel}${isToday}" data-cal-day="${iso}" title="${esc(tip)}">
            <span class="cal-day-num">${parseInt(iso.slice(8), 10)}</span>
            ${litHtml}
            ${renderCalNakaneList(dayList)}
          </button>`;
        })
        .join("")}</div>
      ${L ? L.renderCalColorLegend() : ""}`;

    calEl.querySelector("#cal-prev")?.addEventListener("click", () => {
      state.calendarMonth = new Date(y, m - 1, 1);
      paintCalendarMonth();
    });
    calEl.querySelector("#cal-next")?.addEventListener("click", () => {
      state.calendarMonth = new Date(y, m + 1, 1);
      paintCalendarMonth();
    });
    calEl.querySelector("#cal-today")?.addEventListener("click", () => {
      state.calendarMonth = new Date();
      state.selectedDate = isoToday();
      renderCommandBar();
      renderCalendar();
      renderDayPanel();
    });
    calEl.querySelectorAll("[data-cal-day]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedDate = btn.dataset.calDay;
        renderCommandBar();
        renderCalendar();
        renderDayPanel();
        document.getElementById("nakane-day-panel")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    });
  }

  function paintCalendarMonth() {
    const y = state.calendarMonth.getFullYear();
    const m = state.calendarMonth.getMonth();
    const L = global.PastoralLiturgical;
    const done = () => renderCalendar();
    if (L?.loadLitcalYearsForMonth) {
      L.loadLitcalYearsForMonth(y, m).finally(done);
    } else if (L?.loadLitcalYear) {
      L.loadLitcalYear(y).finally(done);
    } else {
      done();
    }
  }

  /* ---------- evidencija (statistika + tablica) ---------- */

  function lastSixMonths() {
    const now = new Date();
    const months = [];
    for (let offset = 5; offset >= 0; offset -= 1) {
      const date = new Date(now.getFullYear(), now.getMonth() - offset, 1);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      const label = date
        .toLocaleDateString("hr-HR", { month: "short" })
        .replace(".", "")
        .trim();
      months.push({ key, label, count: 0 });
    }
    return months;
  }

  function computeStats() {
    const intentions = state.intentions || [];
    const total = intentions.length;
    const paid = intentions.filter((intention) => intention.paid).length;
    const unpaid = total - paid;
    const paidPct = total ? Math.round((paid / total) * 100) : 0;
    const unpaidStipend = intentions.reduce((sum, intention) => {
      if (intention.paid) return sum;
      return sum + num(intention.stipend);
    }, 0);
    const totalStipend = intentions.reduce(
      (sum, intention) => sum + num(intention.stipend),
      0
    );
    const paidRevenue = intentions.reduce((sum, intention) => {
      if (!intention.paid) return sum;
      return sum + num(intention.stipend);
    }, 0);
    const months = lastSixMonths();
    intentions.forEach((intention) => {
      const month = months.find((item) => item.key === (intention.date || "").slice(0, 7));
      if (month) month.count += 1;
    });
    return {
      total,
      paid,
      unpaid,
      paidPct,
      unpaidStipend,
      totalStipend,
      paidRevenue,
      months,
    };
  }

  function visiblePages(page, pageCount) {
    if (pageCount <= 7) {
      return Array.from({ length: pageCount }, (_, index) => index + 1);
    }
    const marks = new Set([1, pageCount, page - 1, page, page + 1]);
    const pages = [...marks].filter((item) => item >= 1 && item <= pageCount).sort((a, b) => a - b);
    const withGaps = [];
    pages.forEach((item, index) => {
      if (index && item - pages[index - 1] > 1) withGaps.push("gap");
      withGaps.push(item);
    });
    return withGaps;
  }

  function paginateRows(rows, page) {
    const total = rows.length;
    const pageCount = Math.max(1, Math.ceil(total / TABLE_PAGE_SIZE) || 1);
    const current = Math.min(Math.max(page || 1, 1), pageCount);
    const start = (current - 1) * TABLE_PAGE_SIZE;
    const end = start + TABLE_PAGE_SIZE;
    return {
      items: rows.slice(start, end),
      page: current,
      pageCount,
      total,
      start: total ? start + 1 : 0,
      end: Math.min(end, total),
      hasPrevious: current > 1,
      hasNext: current < pageCount,
      pages: visiblePages(current, pageCount),
    };
  }

  function renderStats() {
    const mount = document.getElementById("nakane-stats");
    if (!mount) return;
    const s = computeStats();
    const yMax = Math.max(1, ...s.months.map((month) => month.count));
    const ticks = [];
    for (let tick = yMax; tick >= 0; tick -= 1) ticks.push(tick);
    const paidDeg = s.total ? (s.paid / s.total) * 100 : 0;

    mount.innerHTML = `
      <h2 class="section-title">Pregled i statistika</h2>
      <p class="card-sub">Ukupna evidencija nakana — tablicu ispod sortirajte i filtrirajte.</p>
      <div class="kpi-row nakane-stats-kpis">
        <article class="card kpi-card kpi-tone--liturgy">
          <p class="card-label">Ukupno</p>
          <p class="card-value">${s.total}</p>
          <p class="card-sub">svih nakana u evidenciji</p>
        </article>
        <article class="card kpi-card kpi-tone--success">
          <p class="card-label">Plaćeno</p>
          <p class="card-value">${s.paid}</p>
          <p class="card-sub">${s.paidPct}% od ukupnog broja</p>
        </article>
        <article class="card kpi-card kpi-tone--alert">
          <p class="card-label">Neplaćeno</p>
          <p class="card-value">${s.unpaid}</p>
          <p class="card-sub">${num(s.unpaidStipend)} € stipendija</p>
        </article>
        <article class="card kpi-card kpi-tone--accent">
          <p class="card-label">Stipendiji</p>
          <p class="card-value">${num(s.totalStipend)} €</p>
          <p class="card-sub">ukupno u evidenciji</p>
        </article>
      </div>
      <div class="nakane-stats-charts">
        <article class="nakane-chart-panel">
          <p class="card-label">Evidencija plaćenih i neplaćenih misnih nakana</p>
          <div class="nakane-donut-wrap">
            <div class="nakane-donut" style="--paid-pct: ${paidDeg}" aria-hidden="true"></div>
            <div class="nakane-donut-legend">
              <span><i class="legend-paid"></i> Plaćeno</span>
              <span><i class="legend-unpaid"></i> Neplaćeno</span>
            </div>
          </div>
        </article>
        <article class="nakane-chart-panel">
          <p class="card-label">Nakane — zadnjih 6 mjeseci</p>
          <div class="nakane-month-chart">
            <div class="nakane-month-axis" aria-hidden="true">${ticks.map((tick) => `<span>${tick}</span>`).join("")}</div>
            <div class="nakane-month-bars">
              ${s.months
                .map((month) => {
                  const height = yMax ? (month.count / yMax) * 100 : 0;
                  return `<div class="nakane-month-col" title="${esc(month.label)}: ${month.count}">
                    <span class="nakane-month-bar" style="height:${height}%"></span>
                    <small>${esc(month.label)}</small>
                  </div>`;
                })
                .join("")}
            </div>
          </div>
        </article>
      </div>`;
  }

  function sortRows(rows, sort) {
    const mul = sort.dir === "desc" ? -1 : 1;
    return [...rows].sort((a, b) => {
      let va;
      let vb;
      switch (sort.key) {
        case "stipend":
          return (num(a.stipend) - num(b.stipend)) * mul;
        case "paid":
          return ((a.paid ? 1 : 0) - (b.paid ? 1 : 0)) * mul;
        case "massTime":
          va = a.massTime || "";
          vb = b.massTime || "";
          break;
        case "intentionFor":
          va = a.intentionFor || "";
          vb = b.intentionFor || "";
          break;
        default:
          va = a.date || "";
          vb = b.date || "";
      }
      return String(va).localeCompare(String(vb), "hr") * mul;
    });
  }

  function renderTable() {
    const mount = document.getElementById("nakane-table");
    if (!mount) return;
    const allRows = state.intentions || [];
    const q = state.tableFilter.search.trim().toLowerCase();
    let filtered = allRows.filter((n) => {
      if (state.tableFilter.status === "paid" && !n.paid) return false;
      if (state.tableFilter.status === "unpaid" && n.paid) return false;
      if (!q) return true;
      return [n.date, n.massTime, n.intentionFor, String(n.stipend)].some((v) =>
        String(v ?? "").toLowerCase().includes(q)
      );
    });
    filtered = sortRows(filtered, state.tableSort);
    const stats = computeStats();
    const pager = paginateRows(filtered, state.tablePage);
    state.tablePage = pager.page;
    const pageRows = pager.items;

    const cols = [
      { key: "date", label: "Datum" },
      { key: "massTime", label: "Misa" },
      { key: "intentionFor", label: "Nakana" },
      { key: "stipend", label: "Stipendij" },
      { key: "paid", label: "Status" },
      { key: "_actions", label: "" },
    ];

    const searchEl = mount.querySelector(".nakane-table-search");
    const searchFocused = document.activeElement === searchEl;
    const caret = searchEl?.selectionStart;

    mount.innerHTML = `
      <h2 class="section-title">Sve nakane</h2>
      <p class="card-sub">Kliknite red za otvaranje dana u kalendaru. Sortirajte klikom na zaglavlje.</p>
      <div class="nakane-table-toolbar">
        <input type="search" class="nakane-table-search" placeholder="Pretraži nakane…" value="${esc(state.tableFilter.search)}" />
        <select class="nakane-table-filter" data-nakane-status>
          <option value="all" ${state.tableFilter.status === "all" ? "selected" : ""}>Sve</option>
          <option value="paid" ${state.tableFilter.status === "paid" ? "selected" : ""}>Stipendij evidentiran</option>
          <option value="unpaid" ${state.tableFilter.status === "unpaid" ? "selected" : ""}>Stipendij nije evidentiran</option>
        </select>
        <span class="table-kit-meta">${pager.total} / ${allRows.length} nakana · ${num(stats.paidRevenue)} € od plaćenih</span>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr>${cols
            .map((c) => {
              if (c.key === "_actions") return `<th>${c.label}</th>`;
              const sorted = state.tableSort.key === c.key;
              const cls = `nakane-th-sort${sorted ? " is-sorted" : ""}${sorted && state.tableSort.dir === "desc" ? " is-desc" : ""}`;
              return `<th class="${cls}" data-sort-key="${c.key}">${c.label}</th>`;
            })
            .join("")}</tr></thead>
          <tbody>${
            pageRows.length
              ? pageRows
                  .map((n) => {
                    const sel = n.date === state.selectedDate ? " is-selected" : "";
                    return `<tr class="nakane-table-row${sel}" data-nakana-row="${n.id}" data-nakana-date="${esc(n.date)}">
                      <td>${esc(fmtDate(n.date))}</td>
                      <td>${esc(n.massTime || "—")}</td>
                      <td><strong>${esc(n.intentionFor || "—")}</strong></td>
                      <td>${num(n.stipend)} €</td>
                      <td>${n.paid ? '<span class="badge badge-done">evidentiran</span>' : '<span class="badge badge-urgent">nije evidentiran</span>'}</td>
                      <td class="nakane-table-actions">
                        <button type="button" class="btn btn-ghost btn-sm" data-edit-intent="${n.id}">Uredi</button>
                        ${!n.paid ? `<button type="button" class="btn btn-primary btn-sm" data-pay-intent="${n.id}">Evidentiraj stipendij</button>` : ""}
                        <button type="button" class="btn btn-ghost btn-sm" data-del-intent="${n.id}">Obriši</button>
                      </td>
                    </tr>`;
                  })
                  .join("")
              : `<tr><td colspan="6" class="empty-state">Nema nakana za prikaz.</td></tr>`
          }</tbody>
        </table>
      </div>
      ${
        pager.total
          ? `<nav class="family-pagination" aria-label="Stranice popisa nakana">
        <p class="family-pagination-meta">Prikaz ${pager.start}–${pager.end} od ${pager.total}</p>
        ${
          pager.pageCount > 1
            ? `<div class="family-pagination-pages">
          ${pager.hasPrevious ? `<button type="button" class="btn btn-ghost btn-sm" data-nakane-page="${pager.page - 1}">Prethodna</button>` : `<span></span>`}
          ${pager.pages
            .map((item) =>
              item === "gap"
                ? `<span class="family-pagination-gap" aria-hidden="true">…</span>`
                : item === pager.page
                  ? `<span class="family-pagination-current" aria-current="page">${item}</span>`
                  : `<button type="button" class="btn btn-ghost btn-sm" data-nakane-page="${item}">${item}</button>`
            )
            .join("")}
          ${pager.hasNext ? `<button type="button" class="btn btn-ghost btn-sm" data-nakane-page="${pager.page + 1}">Sljedeća</button>` : ""}
        </div>`
            : ""
        }
      </nav>`
          : ""
      }`;

    const nextSearch = mount.querySelector(".nakane-table-search");
    nextSearch?.addEventListener("input", (e) => {
      state.tableFilter.search = e.target.value;
      state.tablePage = 1;
      renderTable();
    });
    if (searchFocused && nextSearch) {
      nextSearch.focus();
      const pos = typeof caret === "number" ? caret : nextSearch.value.length;
      nextSearch.setSelectionRange(pos, pos);
    }
    mount.querySelector("[data-nakane-status]")?.addEventListener("change", (e) => {
      state.tableFilter.status = e.target.value;
      state.tablePage = 1;
      renderTable();
    });
    mount.querySelectorAll("[data-sort-key]").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.dataset.sortKey;
        if (state.tableSort.key === key) {
          state.tableSort.dir = state.tableSort.dir === "asc" ? "desc" : "asc";
        } else {
          state.tableSort.key = key;
          state.tableSort.dir = "asc";
        }
        state.tablePage = 1;
        renderTable();
      });
    });
    mount.querySelectorAll("[data-nakane-page]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.tablePage = Number(btn.dataset.nakanePage) || 1;
        renderTable();
      });
    });
    mount.querySelectorAll("[data-nakana-row]").forEach((tr) => {
      tr.addEventListener("click", (e) => {
        if (e.target.closest("button")) return;
        const iso = tr.dataset.nakanaDate;
        if (!iso) return;
        state.selectedDate = iso;
        state.calendarMonth = new Date(iso + "T12:00:00");
        try {
          sessionStorage.setItem(MODE_KEY, "calendar");
        } catch {
          /* ignore */
        }
        applyMode();
        refresh();
        requestAnimationFrame(() => {
          document.getElementById("nakane-workspace")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });
    });
    bindRowActions(mount);
  }

  /* ---------- akcije na redovima ---------- */

  function bindRowActions(root) {
    root.querySelectorAll("[data-edit-intent]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        openEditModal(btn.dataset.editIntent);
      });
    });
    root.querySelectorAll("[data-print-mass]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        printDay(state.selectedDate, btn.dataset.printMass);
      });
    });
    root.querySelectorAll("[data-pay-intent]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        try {
          await runAction("mark_intention_paid", { id: btn.dataset.payIntent });
          showToast("Plaćanje zabilježeno");
          refresh();
        } catch {
          showToast("Greška pri spremanju");
        }
      });
    });
    root.querySelectorAll("[data-del-intent]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = btn.dataset.delIntent;
        const doDelete = async () => {
          try {
            await runAction("delete_intention", { id });
            showToast("Nakana obrisana");
            refresh();
          } catch {
            showToast("Greška pri brisanju");
          }
        };
        const M = global.PastoralModal;
        if (M?.confirm) {
          M.confirm({
            title: "Brisanje nakane",
            message: "Obrisati ovu nakanu?",
            danger: true,
            confirmLabel: "Obriši",
            onConfirm: doDelete,
          });
        } else if (global.confirm("Obrisati ovu nakanu?")) {
          doDelete();
        }
      });
    });
  }

  /* ---------- modali ---------- */

  function massSelect(iso, selected) {
    const available = massTimeOptions(iso);
    const opts = [...available, selected]
      .filter((v, i, a) => v && a.indexOf(v) === i)
      .map((t) => `<option ${selected === t ? "selected" : ""}>${esc(t)}</option>`)
      .join("");
    if (!opts) {
      return `<select name="massTime" disabled><option value="">Nema mise</option></select>`;
    }
    return `<select name="massTime">${opts}</select>`;
  }

  function nakanaFormBody(record, iso, { editableDate = false } = {}) {
    const paidSlot = record
      ? record.paid
        ? `<p class="card-sub nakana-form__paid-status">Stipendij evidentiran${record.paymentId ? ` · ref. ${esc(record.paymentId)}` : ""}.</p>`
        : ""
      : `<label class="nakana-form__paid"><input type="checkbox" name="paid" /> Stipendij evidentiran</label>`;
    return `
      <div class="nakana-form form-wide">
        <div class="nakana-form__meta${editableDate ? " nakana-form__meta--with-date" : ""}">
          ${editableDate ? `<div class="form-group"><label>Datum *</label><input name="date" type="date" value="${record?.date || iso || ""}" required /></div>` : ""}
          <div class="form-group"><label>Misa (sat)</label>${massSelect(iso, record?.massTime)}</div>
          <div class="form-group"><label>Stipendij (€)</label><input name="stipend" type="number" min="0" step="0.01" value="${record?.stipend ?? state.defaultStipend}" /></div>
          ${paidSlot}
        </div>
        <div class="form-group"><label>Za koga / namjera *</label><input name="intentionFor" required placeholder="Pokoj duše…" value="${esc(record?.intentionFor || "")}" /></div>
        <div class="form-group"><label>Bilješka (samo za svećenika)</label><textarea name="notes" rows="2" placeholder="Interna bilješka…">${esc(record?.notes || "")}</textarea></div>
      </div>`;
  }

  function readForm(form, iso, { editableDate = false, originalRecord = null } = {}) {
    const fd = new FormData(form);
    const intentionFor = (fd.get("intentionFor") || "").trim();
    if (!intentionFor) {
      showToast("Unesite namjeru molitve");
      return null;
    }
    const date = editableDate ? fd.get("date") : iso;
    if (!date) {
      showToast("Unesite datum");
      return null;
    }
    const massTime = fd.get("massTime") || "";
    const availableTimes = massTimeOptions(date);
    const keepingSameSlot =
      originalRecord &&
      originalRecord.date === date &&
      (originalRecord.massTime || "") === massTime;
    if (!keepingSameSlot && !availableTimes.includes(massTime)) {
      showToast("Za taj dan nema mise — nakana se ne može upisati");
      return null;
    }
    return {
      date,
      mass_time: massTime,
      intention_for: intentionFor,
      stipend: Number(fd.get("stipend")) || 0,
      notes: (fd.get("notes") || "").trim(),
      paid: !!form.querySelector('[name="paid"]')?.checked,
    };
  }

  function openAddModal(iso) {
    const M = global.PastoralModal;
    if (!M?.openForm) return;
    const day = iso || state.selectedDate || isoToday();
    if (!massTimeOptions(day).length) {
      showToast("Za taj dan nema mise — nakana se ne može upisati");
      return;
    }
    M.openForm({
      title: `Nova nakana — ${fmtDate(day)}`,
      size: "lg",
      body: nakanaFormBody(null, day),
      submitLabel: "Spremi",
      onSubmit: (form) => {
        const fields = readForm(form, day);
        if (!fields) return false;
        (async () => {
          try {
            await runAction("create_intention", fields);
            M.close();
            showToast(fields.paid ? "Nakana i stipendij su evidentirani" : "Nakana spremljena");
            refresh();
          } catch (error) {
            const code = error?.details?.error || error?.message;
            if (code === "no_mass_on_date" || code === "mass_not_on_date") {
              showToast("Za taj dan nema mise — nakana se ne može upisati");
            } else {
              showToast("Greška pri spremanju");
            }
          }
        })();
        return false;
      },
    });
  }

  function openEditModal(id) {
    const M = global.PastoralModal;
    if (!M?.openForm) return;
    const record = state.intentions.find((n) => n.id === id);
    if (!record) {
      showToast("Nakana nije pronađena");
      return;
    }
    M.openForm({
      title: `Uredi nakanu — ${fmtDate(record.date)}`,
      size: "lg",
      body: nakanaFormBody(record, record.date, { editableDate: true }),
      submitLabel: "Spremi",
      onSubmit: (form) => {
        const fields = readForm(form, record.date, {
          editableDate: true,
          originalRecord: record,
        });
        if (!fields) return false;
        (async () => {
          try {
            await runAction("update_intention", { id: record.id, ...fields });
            M.close();
            showToast("Nakana ažurirana");
            refresh();
          } catch (error) {
            const code = error?.details?.error || error?.message;
            if (code === "no_mass_on_date" || code === "mass_not_on_date") {
              showToast("Za taj dan nema mise — nakana se ne može upisati");
            } else {
              showToast("Greška pri spremanju");
            }
          }
        })();
        return false;
      },
    });
  }

  /* ---------- ispis ---------- */

  function nakanePrintStyles(accent) {
    const color = accent || "#5c2e3a";
    return `
      *,*::before,*::after{box-sizing:border-box}
      body{
        font-family:"Segoe UI",system-ui,-apple-system,sans-serif;
        font-size:11pt;line-height:1.45;color:#1c1c1c;
        max-width:210mm;margin:0 auto;padding:28px 32px 40px;
        background:#fff;
      }
      .sheet-header{
        text-align:center;padding-bottom:18px;margin-bottom:24px;
        border-bottom:2px solid ${color};
      }
      .sheet-header__parish{
        margin:0 0 4px;font-family:Georgia,"Times New Roman",serif;
        font-size:1.35rem;font-weight:600;letter-spacing:0.02em;color:${color};
      }
      .sheet-header__subtitle{
        margin:0 0 10px;font-size:0.72rem;text-transform:uppercase;
        letter-spacing:0.14em;color:#6b6560;
      }
      .sheet-header__title{
        margin:0;font-family:Georgia,"Times New Roman",serif;
        font-size:1.05rem;font-weight:600;color:#2a2a2a;
      }
      .sheet-header__date{
        margin:6px 0 0;font-size:0.95rem;color:#444;
      }
      .sheet-header__meta{
        margin:10px 0 0;font-size:0.8rem;color:#777;
      }
      .mass-block{
        margin-bottom:22px;page-break-inside:avoid;
      }
      .mass-block__head{
        display:flex;align-items:baseline;justify-content:space-between;
        gap:12px;margin-bottom:8px;padding:8px 12px;
        background:linear-gradient(90deg,${color}12,transparent);
        border-left:3px solid ${color};
      }
      .mass-block__time{
        font-family:Georgia,"Times New Roman",serif;
        font-size:1rem;font-weight:600;color:${color};
      }
      .mass-block__count{
        font-size:0.75rem;color:#6b6560;white-space:nowrap;
      }
      .nakane-print-table{
        width:100%;border-collapse:collapse;font-size:0.88rem;
      }
      .nakane-print-table th{
        padding:7px 10px;text-align:left;font-size:0.68rem;
        font-weight:600;text-transform:uppercase;letter-spacing:0.06em;
        color:#5c574f;border-bottom:2px solid #e0dbd2;
        background:#faf8f5;
      }
      .nakane-print-table td{
        padding:9px 10px;vertical-align:top;
        border-bottom:1px solid #ebe6de;
      }
      .nakane-print-table tbody tr:last-child td{border-bottom:none}
      .nakane-print-table tbody tr:nth-child(even){background:#fcfaf7}
      .col-intention{font-weight:500;color:#1a1a1a}
      .col-requester{color:#444}
      .col-stipend,.col-paid{text-align:right;white-space:nowrap}
      .col-paid{text-align:center}
      .col-notes{font-size:0.82rem;color:#555;font-style:italic}
      .col-notes .muted{color:#aaa;font-style:normal}
      .badge{
        display:inline-block;min-width:1.4em;text-align:center;
        font-size:0.75rem;font-weight:600;
      }
      .badge--paid{color:#2d6a3e}
      .badge--unpaid{color:#bbb}
      .empty{
        margin:0;padding:16px;text-align:center;font-size:0.9rem;
        color:#888;background:#faf8f5;border:1px dashed #ddd;border-radius:4px;
      }
      .sheet-footer{
        margin-top:28px;padding-top:12px;border-top:1px solid #e8e4dc;
        font-size:0.72rem;color:#999;text-align:center;
      }
      .print-bar{
        position:sticky;top:0;z-index:10;display:flex;align-items:center;
        justify-content:space-between;gap:16px;margin:-28px -32px 24px;
        padding:12px 32px;background:#f5f3ef;border-bottom:1px solid #e0dbd2;
      }
      .print-bar__hint{font-size:0.82rem;color:#666}
      .print-bar__btn{
        font:inherit;font-size:0.85rem;font-weight:600;
        padding:8px 18px;border:none;border-radius:6px;cursor:pointer;
        color:#fff;background:${color};
      }
      .print-bar__btn:hover{filter:brightness(1.08)}
      @page{margin:14mm}
      @media print{
        body{padding:0}
        .no-print{display:none!important}
        .nakane-print-table th{background:#f5f2ec!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
        .mass-block__head,.nakane-print-table tbody tr:nth-child(even){
          -webkit-print-color-adjust:exact;print-color-adjust:exact;
        }
      }`;
  }

  function nakanePrintRow(n) {
    const paid = n.paid
      ? '<span class="badge badge--paid" title="Stipendij evidentiran">✓</span>'
      : '<span class="badge badge--unpaid" title="Stipendij nije evidentiran">·</span>';
    const notes = n.notes
      ? esc(n.notes)
      : '<span class="muted">—</span>';
    return `<tr>
      <td class="col-intention">${esc(n.intentionFor)}</td>
      <td class="col-stipend">${num(n.stipend)} €</td>
      <td class="col-paid">${paid}</td>
      <td class="col-notes">${notes}</td>
    </tr>`;
  }

  function nakanePrintTable(rows) {
    if (!rows.length) {
      return '<p class="empty">Nema nakana za ovu misu.</p>';
    }
    return `<table class="nakane-print-table">
      <thead><tr>
        <th>Za koga</th>
        <th>Stipendij</th>
        <th>Pl.</th>
        <th>Bilješka</th>
      </tr></thead>
      <tbody>${rows.map(nakanePrintRow).join("")}</tbody>
    </table>`;
  }

  function nakanePrintMassBlock(time, rows) {
    const countLabel = rows.length === 1 ? "1 nakana" : `${rows.length} nakane`;
    return `<section class="mass-block">
      <header class="mass-block__head">
        <span class="mass-block__time">Misa ${esc(time)}</span>
        <span class="mass-block__count">${countLabel}</span>
      </header>
      ${nakanePrintTable(rows)}
    </section>`;
  }

  function printDay(iso, massTimeFilter) {
    const settings = global.PastoralParish?.loadSettings?.() || {};
    const accent = settings.primaryColor || "#5c2e3a";
    let list = state.intentions.filter((n) => n.date === iso);
    if (massTimeFilter) list = list.filter((n) => n.massTime === massTimeFilter);
    list = list.slice().sort((a, b) => String(a.massTime || "").localeCompare(String(b.massTime || "")));

    const longDate = fmtLongDate(iso);
    const docTitle = massTimeFilter
      ? `Misne nakane — ${longDate} · ${massTimeFilter}`
      : `Misne nakane — ${longDate}`;
    const parishLine = [settings.city, settings.diocese].filter(Boolean).join(" · ");

    let body;
    if (!list.length) {
      body = '<p class="empty">Nema nakana za ispis na odabrani dan.</p>';
    } else if (massTimeFilter) {
      body = nakanePrintMassBlock(massTimeFilter, list);
    } else {
      const byMass = {};
      list.forEach((n) => {
        const t = n.massTime || "—";
        (byMass[t] = byMass[t] || []).push(n);
      });
      body = Object.keys(byMass)
        .sort()
        .map((t) => nakanePrintMassBlock(t, byMass[t]))
        .join("");
    }

    const countNote = list.length
      ? `${list.length} ${list.length === 1 ? "nakana" : "nakane"} ukupno`
      : "";

    const html = `<!DOCTYPE html><html lang="hr"><head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>${esc(docTitle)}</title>
      <style>${nakanePrintStyles(accent)}</style>
      </head><body>
      <div class="print-bar no-print">
        <span class="print-bar__hint">Pregled prije ispisa · ${esc(docTitle)}</span>
        <button type="button" class="print-bar__btn" onclick="window.print()">Ispis / PDF</button>
      </div>
      <header class="sheet-header">
        <p class="sheet-header__subtitle">Misne nakane</p>
        <h1 class="sheet-header__parish">${esc(settings.name || "Župa")}</h1>
        ${parishLine ? `<p class="sheet-header__meta">${esc(parishLine)}</p>` : ""}
        <p class="sheet-header__title">${massTimeFilter ? `Misa ${esc(massTimeFilter)}` : "Raspored nakana"}</p>
        <p class="sheet-header__date">${esc(longDate)}</p>
        ${countNote ? `<p class="sheet-header__meta">${esc(countNote)}</p>` : ""}
      </header>
      ${body}
      <footer class="sheet-footer">
        ${settings.pastor ? `${esc(settings.pastor)} · ` : ""}Pastoral · ${new Date().toLocaleString("hr-HR")}
      </footer>
      </body></html>`;

    const w = global.open("", "_blank");
    if (!w) {
      showToast("Omogućite skočne prozore za ispis");
      return;
    }
    w.document.write(html);
    w.document.close();
  }

  /* ---------- glavni render ---------- */

  function refresh() {
    applyMode();
    renderCommandBar();
    const mode = getMode();
    if (mode === "today") {
      state.selectedDate = isoToday();
      renderDayPanel();
    } else if (mode === "calendar") {
      if (!state.selectedDate) state.selectedDate = isoToday();
      renderCalendar();
      renderDayPanel();
    } else {
      renderStats();
      renderTable();
    }
  }

  function init() {
    const root = document.getElementById("nakane-root");
    if (!root) return;

    const boot = readBootstrap();
    state.intentions = boot.intentions || [];
    state.massSchedule = boot.massSchedule || [];
    state.defaultStipend = Number(boot.defaultStipend) || 0;

    const params = new URLSearchParams(location.search);
    const dateParam = params.get("date");
    const modeParam = params.get("mode");

    if (dateParam === "today") {
      state.selectedDate = isoToday();
      state.calendarMonth = new Date();
      safeSetMode("today");
    } else if (dateParam && /^\d{4}-\d{2}-\d{2}$/.test(dateParam)) {
      state.selectedDate = dateParam;
      state.calendarMonth = new Date(dateParam + "T12:00:00");
      safeSetMode("calendar");
    } else {
      state.selectedDate = boot.filterDate && /^\d{4}-\d{2}-\d{2}$/.test(boot.filterDate) ? boot.filterDate : isoToday();
      state.calendarMonth = new Date(state.selectedDate + "T12:00:00");
    }
    if (VIEW_MODES.includes(modeParam)) safeSetMode(modeParam);

    applyMode();

    const y = state.calendarMonth.getFullYear();
    const m = state.calendarMonth.getMonth();
    const L = global.PastoralLiturgical;
    const finish = () => refresh();
    if (L?.loadLitcalYearsForMonth) {
      L.loadLitcalYearsForMonth(y, m).finally(finish);
    } else if (L?.loadLitcalYear) {
      L.loadLitcalYear(y).finally(finish);
    } else {
      finish();
    }
  }

  function safeSetMode(mode) {
    try {
      sessionStorage.setItem(MODE_KEY, mode);
    } catch {
      /* ignore */
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  global.PastoralNakane = { refresh, setMode };
})(typeof window !== "undefined" ? window : global);
