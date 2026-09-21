/**
 * Katolički liturgijski kalendar
 *
 * U aplikaciji čita Django API koji vraća retke iz baze
 * (`LiturgicalCalendarEntry`). HILP ostaje poveznica na puni tekst čitanja.
 */
(function (global) {
  const HILP_LITURGY = "https://hilp.hr/liturgija-dana/";
  const CACHE_PREFIX = "pastoral_litcal_v5_";

  const GRADE_HR = {
    SOLEMNITY: "Svetkovina",
    FEAST: "Blagdan",
    MEMORIAL: "Spomen",
    "OPTIONAL MEMORIAL": "Izborni spomen",
    FERIAL: "Radni dan",
    WEEKDAY: "Radni dan",
    "WEEKDAY OF ADVENT": "Radni dan adventa",
    "WEEKDAY OF LENT": "Radni dan korizme",
    "WEEKDAY OF EASTER": "Radni dan Uskrsa",
    "WEEKDAY OF ORDINARY TIME": "Radni dan",
  };

  let yearIndexCache = {};
  const mappedDayCache = {};
  const yearLoadInFlight = {};
  const djangoYearInFlight = {};
  const djangoMonthInFlight = {};

  async function fetchDjangoLiturgicalYear(year) {
    if (mappedDayCache[year]) return mappedDayCache[year];
    if (djangoYearInFlight[year]) return djangoYearInFlight[year];
    djangoYearInFlight[year] = fetch(`/api/liturgical/year/${year}/`, { credentials: "same-origin" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`Django liturgical HTTP ${res.status}`);
        const data = await res.json();
        mappedDayCache[year] = data.days || {};
        return mappedDayCache[year];
      })
      .finally(() => {
        delete djangoYearInFlight[year];
      });
    return djangoYearInFlight[year];
  }

  function isTranslatedDay(day) {
    return day && day.translated !== false && day.title;
  }

  function djangoYearIsLoaded(year) {
    return Object.prototype.hasOwnProperty.call(mappedDayCache, year);
  }

  function emptyStoredDay(date) {
    return {
      source: "offline",
      empty: true,
      date,
      title: "Nema unosa",
      shortTitle: "Nema unosa",
      subtitle: "Uvezite kalendar u tehničkoj administraciji.",
      color: null,
      colorLabel: "",
      observances: [],
      celebrations: [],
      hilpUrl: hilpUrlForDate(date),
      loaded: true,
      translated: true,
    };
  }

  function getMappedDay(iso) {
    const y = parseYear(iso);
    for (const calYear of [y, y + 1, y - 1]) {
      const day = mappedDayCache[calYear]?.[iso];
      if (isTranslatedDay(day)) {
        return {
          ...day,
          shortTitle: truncate(day.title, 38),
          loaded: true,
        };
      }
    }
    return null;
  }

  const GRADE_NUM_HR = {
    0: "Radni dan",
    1: "Izborni spomen",
    2: "Spomen",
    3: "Spomen",
    4: "Blagdan",
    5: "Blagdan",
    6: "Svetkovina",
    7: "Svetkovina",
  };

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function isoToday() {
    return new Date().toISOString().slice(0, 10);
  }

  function parseYear(iso) {
    return Number(iso.slice(0, 4));
  }

  function hilpUrlForDate(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return `${HILP_LITURGY}?god=${y}&mj=${m}&dan=${d}`;
  }

  async function prefetchMonthHr(civilYear, month) {
    const monthNum = month + 1;
    const key = `${civilYear}-${monthNum}`;
    if (djangoMonthInFlight[key]) return djangoMonthInFlight[key];

    djangoMonthInFlight[key] = fetch(`/api/liturgical/month/${civilYear}/${monthNum}/`, {
      credentials: "same-origin",
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`Django liturgical month HTTP ${res.status}`);
        const data = await res.json();
        const days = data.days || {};
        if (!mappedDayCache[civilYear]) mappedDayCache[civilYear] = {};
        Object.assign(mappedDayCache[civilYear], days);
        notifyYearReady(civilYear);
        return days;
      })
      .catch((e) => {
        console.warn("[PastoralLiturgical] Django mjesec:", e.message);
        return null;
      })
      .finally(() => {
        delete djangoMonthInFlight[key];
      });

    return djangoMonthInFlight[key];
  }

  async function fetchAndIndexLitcalYear(year) {
    if (yearIndexCache[year]) return yearIndexCache[year];
    try {
      await fetchDjangoLiturgicalYear(year);
    } catch (djangoError) {
      console.warn(
        "[PastoralLiturgical] Kalendar iz baze nije dostupan:",
        djangoError.message
      );
    }
    yearIndexCache[year] = {};
    return yearIndexCache[year];
  }

  async function getDay(iso) {
    const date = iso || isoToday();
    try {
      await loadLitcalYearsForDate(date);
      const mapped = getMappedDay(date);
      if (mapped) return mapped;
      const res = await fetch(`/api/liturgical/day/${date}/`, { credentials: "same-origin" });
      if (res.ok) {
        const day = await res.json();
        const y = parseYear(date);
        if (!mappedDayCache[y]) mappedDayCache[y] = {};
        mappedDayCache[y][date] = day;
        return { ...day, shortTitle: truncate(day.title, 38), loaded: true };
      }
    } catch (e) {
      console.warn("[PastoralLiturgical] Dan iz baze:", e.message);
    }
    return {
      source: "offline",
      date,
      title: "Nema unosa",
      subtitle: "Uvezite kalendar u tehničkoj administraciji.",
      readings: null,
      hilpUrl: hilpUrlForDate(date),
    };
  }

  function liturgicalColorClass(color) {
    const c = String(color || "green").toLowerCase();
    if (c === "purple" || c === "violet") return "lit-color--violet";
    if (c === "white" || c === "gold") return "lit-color--white";
    if (c === "red") return "lit-color--red";
    if (c === "rose") return "lit-color--rose";
    return "lit-color--green";
  }

  function liturgicalCellClass(color) {
    if (!color) return "";
    return liturgicalColorClass(color).replace("lit-color--", "cal-cell--lit-");
  }

  function formatRankHr(rank) {
    if (rank === 0 || rank === "0") return GRADE_NUM_HR[0];
    if (typeof rank === "number" || /^\d+$/.test(String(rank))) {
      const n = Number(rank);
      if (GRADE_NUM_HR[n]) return GRADE_NUM_HR[n];
    }
    if (!rank) return "";
    const raw = String(rank).trim();
    const key = raw.toUpperCase();
    if (GRADE_HR[key]) return GRADE_HR[key];
    if (/ferial|weekday|radni/i.test(raw)) return "Radni dan";
    if (/memorial|spomen/i.test(raw)) return raw.includes("Optional") || raw.includes("Izborn") ? "Izborni spomen" : "Spomen";
    if (/feast|blagdan/i.test(raw)) return "Blagdan";
    if (/solemnity|svetkovina/i.test(raw)) return "Svetkovina";
    return raw;
  }

  function renderDayCard(day, opts = {}) {
    const compact = !!opts.compact;
    const readings = day.readings || [];
    const readingsHtml = readings.length
      ? `<ul class="lit-readings">${readings
          .map((r) => `<li><span class="lit-readings-label">${esc(r.label)}</span> ${esc(r.text)}</li>`)
          .join("")}</ul>`
      : `<p class="card-sub">Puni tekst čitanja i časoslov na <a href="${esc(day.hilpUrl)}" target="_blank" rel="noopener">HILP — Liturgija dana</a> (hrvatski).</p>`;

    const extras =
      day.celebrations?.length && !compact
        ? `<p class="card-sub">Također: ${day.celebrations.map(esc).join(" · ")}</p>`
        : "";

    const meta = [day.subtitle, day.seasonWeek, day.liturgicalYear, day.rank].filter(Boolean).join(" · ");

    return `
      <section class="card lit-card ${compact ? "lit-card--compact" : ""}" data-lit-date="${esc(day.date)}">
        <div class="lit-card-head">
          <div>
            <h2 class="section-title">${compact ? "Liturgija danas" : `Liturgijski dan — ${esc(fmtHrDate(day.date))}`}</h2>
            <p class="lit-card-feast">${esc(day.title)}</p>
            ${day.temporalTitle ? `<p class="card-sub"><strong>Liturgijsko vrijeme:</strong> ${esc(day.temporalTitle)}</p>` : ""}
            ${meta ? `<p class="card-sub">${esc(meta)}</p>` : ""}
            ${extras}
          </div>
          <span class="lit-color-badge ${liturgicalColorClass(day.color)}" title="${esc(day.colorLabel || day.color)}">${esc(day.colorLabel || day.color || "—")}</span>
        </div>
        ${readingsHtml}
        <div class="lit-card-links">
          <a href="${esc(day.hilpUrl)}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Liturgija dana (HILP)</a>
          <a href="https://www.i-breviary.com/" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Časoslov (iBrevijar)</a>
          ${!compact ? `<button type="button" class="btn btn-ghost btn-sm" data-lit-refresh>↻ Osvježi</button>` : ""}
        </div>
      </section>`;
  }

  function fmtHrDate(iso) {
    try {
      return new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      });
    } catch {
      return iso;
    }
  }

  async function mountInto(el, iso, opts) {
    if (!el) return;
    const date = iso || isoToday();
    el.innerHTML = `<section class="card lit-card lit-card--loading"><p class="card-sub">Učitavam liturgijski kalendar…</p></section>`;
    try {
      const day = await getDay(date);
      el.innerHTML = renderDayCard(day, opts);
      el.querySelector("[data-lit-refresh]")?.addEventListener("click", async () => {
        const y = parseYear(date);
        delete yearIndexCache[y];
        delete mappedDayCache[y];
        localStorage.removeItem(`${CACHE_PREFIX}${y}`);
        await mountInto(el, date, opts);
      });
    } catch (e) {
      el.innerHTML = `<section class="card lit-card"><p class="empty-state">Nije moguće učitati kalendar. <a href="${esc(hilpUrlForDate(date))}" target="_blank" rel="noopener">Otvori HILP</a></p></section>`;
    }
  }

  function truncate(str, max) {
    const t = String(str || "").trim();
    if (!t) return "";
    return t.length > max ? `${t.slice(0, max - 1)}…` : t;
  }

  function calendarYearsForMonth(civilYear, month) {
    const years = new Set([civilYear, civilYear + 1]);
    if (month <= 1) years.add(civilYear - 1);
    return [...years];
  }

  async function loadLitcalYears(years) {
    const unique = [...new Set((years || []).filter((y) => Number.isFinite(y)))];
    await Promise.all(unique.map((y) => loadLitcalYear(y).catch(() => null)));
  }

  async function loadLitcalYearsForDate(iso) {
    const y = parseYear(iso || isoToday());
    return loadLitcalYears([y - 1, y, y + 1]);
  }

  async function loadLitcalYearsForMonth(civilYear, month) {
    const result = await loadLitcalYears(calendarYearsForMonth(civilYear, month));
    prefetchMonthHr(civilYear, month);
    return result;
  }

  /** Sažetak dana iz cachea (bez mreže) — uvijek ima hilpUrl */
  function getSummarySync(iso) {
    const date = iso || isoToday();
    const mapped = getMappedDay(date);
    if (mapped) return mapped;
    if (djangoYearIsLoaded(parseYear(date))) {
      return emptyStoredDay(date);
    }
    return {
      source: "pending",
      date,
      title: null,
      shortTitle: null,
      subtitle: "",
      color: null,
      colorLabel: "",
      hilpUrl: hilpUrlForDate(date),
      loaded: false,
    };
  }

  function summariesForMonth(year, month) {
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const out = {};
    for (let d = 1; d <= daysInMonth; d++) {
      const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const pre = getMappedDay(iso);
      if (pre) {
        out[iso] = pre;
        continue;
      }
      if (djangoYearIsLoaded(year)) {
        out[iso] = emptyStoredDay(iso);
        continue;
      }
      out[iso] = getSummarySync(iso);
    }
    return out;
  }

  /** U ćeliji kalendara: rang, svetac, boja + link na HILP */
  function renderCellLiturgy(summary) {
    const s = summary || {};
    const colorCls = liturgicalColorClass(s.color);
    const rankLabel = s.rankLabel || formatRankHr(s.rank);
    const feast = s.shortTitle || s.title;
    const tip = [s.title, rankLabel, s.colorLabel || s.color, s.subtitle].filter(Boolean).join(" · ");
    const observanceColors = Array.isArray(s.observances) && s.observances.length > 1
      ? `<span class="cal-lit-observance-colors" aria-label="Boje slavlja dana">${s.observances
          .map((o) => `<span class="cal-lit-observance-dot ${liturgicalColorClass(o.color)}" title="${esc(`${o.title} — ${o.colorLabel || o.color}`)}"></span>`)
          .join("")}</span>`
      : "";

    if (!s.loaded) {
      return `
        <span class="cal-lit-block cal-lit-block--pending">
          <span class="cal-lit-feast cal-lit-feast--muted">Učitavam…</span>
          <span class="cal-lit-meta">
            <a class="cal-lit-link" href="${esc(s.hilpUrl || hilpUrlForDate(s.date))}" target="_blank" rel="noopener" title="Liturgija dana (HILP)" onclick="event.stopPropagation()">HILP</a>
          </span>
        </span>`;
    }

    return `
      <span class="cal-lit-block" title="${esc(tip)}">
        ${rankLabel ? `<span class="cal-lit-rank">${esc(rankLabel)}</span>` : ""}
        <span class="cal-lit-feast">${esc(feast || "—")}</span>
        <span class="cal-lit-meta">
          <span class="cal-lit-color-tag ${colorCls}">${esc(s.colorLabel || s.color || "—")}</span>
          ${observanceColors}
          <a class="cal-lit-link" href="${esc(s.hilpUrl || hilpUrlForDate(s.date))}" target="_blank" rel="noopener" title="Liturgija dana (HILP)" onclick="event.stopPropagation()">HILP</a>
        </span>
      </span>`;
  }

  function renderCalColorLegend() {
    const items = [
      { cls: "lit-color--green", label: "Zelena" },
      { cls: "lit-color--violet", label: "Ljubičasta" },
      { cls: "lit-color--white", label: "Bijela" },
      { cls: "lit-color--red", label: "Crvena" },
      { cls: "lit-color--rose", label: "Ružičasta" },
    ];
    return `<div class="cal-lit-color-legend" aria-hidden="true">
      ${items.map((i) => `<span class="cal-lit-legend-item"><span class="cal-lit-legend-swatch ${i.cls}"></span>${i.label}</span>`).join("")}
    </div>`;
  }

  /** Desni panel nakana — puni liturgijski dan nakon API poziva */
  function renderNakaneDayLiturgy(day) {
    const d = day || {};
    const colorCls = liturgicalColorClass(d.color);
    const bgCls = liturgicalCellClass(d.color);
    const rank = d.rankLabel || formatRankHr(d.rank);
    const meta = [d.subtitle, d.seasonWeek, d.liturgicalYear].filter(Boolean);
    const extras =
      d.celebrations?.length
        ? `<p class="card-sub">Također: ${d.celebrations.map(esc).join(" · ")}</p>`
        : "";
    const observances = Array.isArray(d.observances) ? d.observances : [];
    const observancesHtml = observances.length > 1
      ? `<div class="lit-observances">
          <p class="card-label">Slavlja dana</p>
          ${observances.map((o) => `
            <div class="lit-observance-row">
              <span class="cal-lit-observance-dot ${liturgicalColorClass(o.color)}" aria-hidden="true"></span>
              <span class="lit-observance-title">${esc(o.title)}</span>
              <span class="badge">${esc(o.rankLabel || o.rank)}</span>
              <span class="cal-lit-color-tag ${liturgicalColorClass(o.color)}">${esc(o.colorLabel || o.color)}</span>
              ${o.primary ? `<span class="badge">Glavno slavlje</span>` : ""}
            </div>`).join("")}
        </div>`
      : "";

    if (d.source === "offline" || d.empty || !d.title) {
      return `<div class="nakane-lit-detail" id="nakane-lit-detail">
        <p class="card-sub">Nema unosa u liturgijskom kalendaru za ovaj dan. Uvezite paket u tehničkoj administraciji ili otvorite HILP.</p>
        <div class="nakane-lit-detail-actions">
          <a href="${esc(d.hilpUrl || hilpUrlForDate(d.date))}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Liturgija dana (HILP)</a>
        </div>
      </div>`;
    }

    return `<div class="nakane-lit-detail ${bgCls}" id="nakane-lit-detail">
      <div class="nakane-lit-detail-head">
        <span class="nakane-lit-swatch nakane-lit-swatch--lg ${colorCls}" title="${esc(d.colorLabel || d.color || "")}"></span>
        <div>
          ${rank ? `<span class="cal-lit-rank">${esc(rank)}</span>` : ""}
          <h3 class="nakane-lit-feast">${esc(d.title)}</h3>
          ${d.temporalTitle ? `<p class="card-sub"><strong>Liturgijsko vrijeme:</strong> ${esc(d.temporalTitle)}</p>` : ""}
          ${meta.length ? `<p class="card-sub">${esc(meta.join(" · "))}</p>` : ""}
          ${extras}
        </div>
        <span class="lit-color-badge ${colorCls}">${esc(d.colorLabel || d.color || "—")}</span>
      </div>
      ${observancesHtml}
      <div class="nakane-lit-detail-actions">
        <a href="${esc(d.hilpUrl || hilpUrlForDate(d.date))}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Liturgija dana (HILP)</a>
      </div>
    </div>`;
  }

  function renderNakaneLitLoading(iso) {
    return `<div class="nakane-lit-detail nakane-lit-detail--loading" id="nakane-lit-detail">
      <p class="card-sub">Učitavam liturgijski dan…</p>
      <a href="${esc(hilpUrlForDate(iso))}" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Liturgija dana (HILP)</a>
    </div>`;
  }

  /** Traka iznad panela dana (nakane, kalendar, …) */
  function renderDayStrip(summary, opts = {}) {
    const s = summary || getSummarySync(opts.date || isoToday());
    const async = opts.async !== false;
    if (!s.loaded && async) {
      return `<div class="lit-day-strip lit-day-strip--loading" data-lit-strip-date="${esc(s.date)}">
        <p class="card-sub">Učitavam liturgijski dan… · <a href="${esc(s.hilpUrl)}" target="_blank" rel="noopener">Liturgija dana (HILP)</a></p>
      </div>`;
    }
    if (!s.loaded) {
      return `<div class="lit-day-strip">
        <a href="${esc(s.hilpUrl)}" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Liturgija dana (HILP)</a>
      </div>`;
    }
    return `<div class="lit-day-strip">
      <div class="lit-day-strip-main">
        <span class="lit-color-badge ${liturgicalColorClass(s.color)}">${esc(s.colorLabel || s.color)}</span>
        <div>
          ${s.rankLabel || s.rank ? `<span class="cal-lit-rank">${esc(s.rankLabel || formatRankHr(s.rank))}</span> ` : ""}
          <strong class="lit-day-strip-feast">${esc(s.title)}</strong>
          ${s.temporalTitle || s.subtitle ? `<span class="card-sub"> · ${esc(s.temporalTitle || s.subtitle)}</span>` : ""}
        </div>
      </div>
      <a href="${esc(s.hilpUrl)}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Liturgija dana (HILP)</a>
    </div>`;
  }

  async function hydrateDayStrip(container, iso) {
    if (!container) return;
    const date = iso || isoToday();
    try {
      const day = await getDay(date);
      container.outerHTML = renderDayStrip(day, { async: false });
    } catch {
      container.innerHTML = `<a href="${esc(hilpUrlForDate(date))}" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Liturgija dana (HILP)</a>`;
    }
  }

  function notifyYearReady(year) {
    try {
      global.dispatchEvent(new CustomEvent("pastoral-liturgical-ready", { detail: { year } }));
    } catch {
      /* IE */
    }
  }

  async function loadLitcalYear(year) {
    if (yearLoadInFlight[year]) return yearLoadInFlight[year];
    yearLoadInFlight[year] = fetchAndIndexLitcalYear(year)
      .then((byDay) => {
        notifyYearReady(year);
        return byDay;
      })
      .finally(() => {
        delete yearLoadInFlight[year];
      });
    return yearLoadInFlight[year];
  }

  async function renderKalendarPage(root, parishEvents, onSelectDate) {
    if (!root) return;
    const today = isoToday();
    let viewMonth = new Date();
    let selected = today;

    async function paint() {
      const y = viewMonth.getFullYear();
      const m = viewMonth.getMonth();
      const monthLabel = viewMonth.toLocaleDateString("hr-HR", { month: "long", year: "numeric" });

      try {
        await loadLitcalYear(y);
      } catch {
        /* prikaz s linkom na HILP */
      }
      const monthSummaries = summariesForMonth(y, m);

      const first = new Date(y, m, 1);
      const startPad = (first.getDay() + 6) % 7;
      const daysInMonth = new Date(y, m + 1, 0).getDate();
      const cells = [];
      for (let i = 0; i < startPad; i++) cells.push(null);
      for (let d = 1; d <= daysInMonth; d++) cells.push(d);

      const parishByDate = {};
      for (const e of parishEvents || []) {
        if (!e.date) continue;
        if (!parishByDate[e.date]) parishByDate[e.date] = [];
        parishByDate[e.date].push(e);
      }

      root.innerHTML = `
        <div class="lit-kal-layout">
          <section class="card">
            <div class="cal-toolbar">
              <button type="button" class="btn btn-ghost btn-sm" data-lit-prev>←</button>
              <strong>${esc(monthLabel)}</strong>
              <button type="button" class="btn btn-ghost btn-sm" data-lit-next>→</button>
              <button type="button" class="btn btn-ghost btn-sm" data-lit-today">Danas</button>
            </div>
            <div class="cal-grid lit-cal-grid">
              ${["Pon", "Uto", "Sri", "Čet", "Pet", "Sub", "Ned"]
                .map((w) => `<div class="cal-dow">${w}</div>`)
                .join("")}
              ${cells
                .map((d) => {
                  if (!d) return `<div class="cal-cell cal-cell--empty"></div>`;
                  const iso = `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
                  const sel = iso === selected ? " cal-selected" : "";
                  const hasParish = parishByDate[iso]?.length ? " cal-has-event" : "";
                  const sum = monthSummaries[iso] || getSummarySync(iso);
                  const isToday = iso === isoToday() ? " cal-today" : "";
                  return `<button type="button" class="cal-cell cal-cell--btn cal-cell--lit${sel}${hasParish}${isToday}" data-lit-day="${iso}">
                    <span class="cal-day-num">${d}</span>
                    ${renderCellLiturgy(sum)}
                  </button>`;
                })
                .join("")}
            </div>
            <p class="card-sub">U svakoj ćeliji: blagdan/svetac i poveznica <strong>Liturgija</strong> (HILP). Župni događaji ispod.</p>
          </section>
          <div id="lit-day-detail"></div>
          <section class="card">
            <h2 class="section-title">Župni događaji</h2>
            ${(parishEvents || []).length
              ? parishEvents
                  .map(
                    (e) =>
                      `<div class="list-item">
                        <strong>${esc(e.title)}</strong><br>
                        <small>${esc(fmtHrDate(e.date))} · ${esc(e.place || "")}</small><br>
                        <a href="${esc(hilpUrlForDate(e.date))}" target="_blank" rel="noopener" class="cal-lit-link">Liturgija dana</a>
                      </div>`
                  )
                  .join("")
              : '<p class="empty-state">Nema unesenih događaja.</p>'}
          </section>
        </div>`;

      const detail = root.querySelector("#lit-day-detail");
      await mountInto(detail, selected, { compact: false });

      root.querySelector("[data-lit-prev]")?.addEventListener("click", () => {
        viewMonth = new Date(y, m - 1, 1);
        paint();
      });
      root.querySelector("[data-lit-next]")?.addEventListener("click", () => {
        viewMonth = new Date(y, m + 1, 1);
        paint();
      });
      root.querySelector("[data-lit-today]")?.addEventListener("click", () => {
        viewMonth = new Date();
        selected = isoToday();
        paint();
        onSelectDate?.(selected);
      });
      root.querySelectorAll("[data-lit-day]").forEach((btn) => {
        btn.addEventListener("click", () => {
          selected = btn.dataset.litDay;
          paint();
          onSelectDate?.(selected);
        });
      });
    }

    await paint();
  }

  global.PastoralLiturgical = {
    getDay,
    getSummarySync,
    summariesForMonth,
    renderCellLiturgy,
    renderNakaneDayLiturgy,
    renderNakaneLitLoading,
    renderDayStrip,
    hydrateDayStrip,
    loadLitcalYear,
    loadLitcalYearsForMonth,
    loadLitcalYearsForDate,
    prefetchMonthHr,
    renderDayCard,
    mountInto,
    liturgicalColorClass,
    liturgicalCellClass,
    formatRankHr,
    renderCalColorLegend,
    renderKalendarPage,
    hilpUrlForDate,
    fmtHrDate,
  };
})(typeof window !== "undefined" ? window : global);
