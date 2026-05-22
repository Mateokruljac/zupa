/**
 * Katolički liturgijski kalendar — vanjski API-ji
 *
 * Izvori:
 * - LitCal API (https://litcal.johnromanodorazio.com) — blagdani, boja, čitanja (referenca)
 * - Church Calendar API (http://calapi.inadiutorium.cz) — rezerva za dan (bez čitanja)
 * - HILP liturgija dana — puni hrvatski tekst (poveznica, nema javnog API-ja)
 */
(function (global) {
  const LITCAL_BASE = "https://litcal.johnromanodorazio.com/api/dev";
  const CALAPI_BASE = "http://calapi.inadiutorium.cz/api/v0/en/calendars/default";
  const HILP_LITURGY = "https://hilp.hr/liturgija-dana/";
  const CACHE_PREFIX = "pastoral_litcal_";

  const SEASON_HR = {
    ADVENT: "Advent",
    CHRISTMASTIDE: "Božićno razdoblje",
    "CHRISTMAS TIME": "Božićno razdoblje",
    LENT: "Korizma",
    "EASTER TRIDUUM": "Veliki tjedan / Triduum",
    EASTERTIDE: "Uskrsno razdoblje",
    "ORDINARY TIME": "Obično vrijeme",
    ORDINARY_TIME: "Obično vrijeme",
  };

  const COLOR_HR = {
    purple: "Ljubičasta",
    violet: "Ljubičasta",
    white: "Bijela",
    red: "Crvena",
    green: "Zelena",
    rose: "Ružičasta",
    black: "Crna",
  };

  const CALAPI_SEASON_HR = {
    advent: "Advent",
    christmas: "Božićno razdoblje",
    lent: "Korizma",
    easter: "Uskrsno razdoblje",
    ordinary: "Obično vrijeme",
  };

  const CALAPI_RANK_HR = {
    solemnity: "Svetkovina",
    feast: "Blagdan",
    memorial: "Spomen",
    "optional memorial": "Izborni spomen",
    ferial: "Radni dan",
  };

  let yearIndexCache = {};

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

  function seasonLabel(raw) {
    if (!raw) return "";
    const key = String(raw).toUpperCase().replace(/\s+/g, " ");
    return SEASON_HR[key] || SEASON_HR[key.replace(/ /g, "_")] || raw;
  }

  function colorLabel(colors) {
    const c = Array.isArray(colors) ? colors[0] : colors;
    if (!c) return "";
    return COLOR_HR[String(c).toLowerCase()] || c;
  }

  function loadYearFromStorage(year) {
    try {
      const raw = localStorage.getItem(`${CACHE_PREFIX}${year}`);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (parsed?.byDay && parsed?.fetchedAt) return parsed.byDay;
    } catch {
      /* ignore */
    }
    return null;
  }

  function saveYearToStorage(year, byDay) {
    try {
      localStorage.setItem(
        `${CACHE_PREFIX}${year}`,
        JSON.stringify({ fetchedAt: new Date().toISOString(), byDay })
      );
    } catch {
      /* quota */
    }
  }

  function buildIndexFromLitcal(events) {
    const byDay = {};
    for (const ev of events || []) {
      const d = (ev.date || "").slice(0, 10);
      if (!d) continue;
      if (!byDay[d]) byDay[d] = [];
      byDay[d].push(ev);
    }
    for (const d of Object.keys(byDay)) {
      byDay[d].sort((a, b) => (b.grade || 0) - (a.grade || 0));
    }
    return byDay;
  }

  async function fetchJson(url) {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function loadLitcalYear(year) {
    if (yearIndexCache[year]) return yearIndexCache[year];

    const stored = loadYearFromStorage(year);
    if (stored) {
      yearIndexCache[year] = stored;
      return stored;
    }

    const url = `${LITCAL_BASE}/calendar/${year}?return_type=JSON&locale=en`;
    const data = await fetchJson(url);
    const byDay = buildIndexFromLitcal(data.litcal || data.Litcal || []);
    yearIndexCache[year] = byDay;
    saveYearToStorage(year, byDay);
    return byDay;
  }

  /** Rezerva: Church Calendar API (može pasti zbog CORS-a u pregledniku) */
  async function fetchCalapiDay(iso) {
    const [y, m, d] = iso.split("-");
    const url = `${CALAPI_BASE}/${y}/${Number(m)}/${Number(d)}`;
    const day = await fetchJson(url);
    const main =
      (day.celebrations || [])
        .filter((c) => c.title)
        .sort((a, b) => (a.rank_num || 99) - (b.rank_num || 99))[0] || (day.celebrations || [])[0];

    return {
      source: "calapi",
      date: day.date || iso,
      title: main?.title || formatCalapiFerial(day),
      subtitle: CALAPI_SEASON_HR[day.season] || day.season,
      seasonWeek: day.season_week,
      color: main?.colour || "green",
      colorLabel: COLOR_HR[main?.colour] || main?.colour,
      rank: CALAPI_RANK_HR[main?.rank] || main?.rank,
      celebrations: (day.celebrations || []).filter((c) => c.title).map((c) => c.title),
      readings: null,
      lectionary: null,
      hilpUrl: hilpUrlForDate(iso),
    };
  }

  function formatCalapiFerial(day) {
    const sw = day.season_week ? `, ${day.season_week}. tjedan` : "";
    const season = CALAPI_SEASON_HR[day.season] || day.season || "";
    const wd = day.weekday ? ` (${day.weekday})` : "";
    return `${season}${sw}${wd}`.trim() || "Liturgijski dan";
  }

  function pickPrimaryEvent(events) {
    if (!events?.length) return null;
    return events.find((e) => !e.is_vigil_mass) || events[0];
  }

  function mapLitcalDay(iso, events) {
    const primary = pickPrimaryEvent(events);
    if (!primary) return null;

    const others = (events || [])
      .filter((e) => e !== primary && e.name && !e.is_vigil_mass)
      .map((e) => e.name)
      .slice(0, 4);

    const r = primary.readings || {};
    const readings = [];
    if (r.first_reading) readings.push({ label: "Prvo čitanje", text: r.first_reading });
    if (r.responsorial_psalm) readings.push({ label: "Otpjevni psalam", text: r.responsorial_psalm });
    if (r.second_reading) readings.push({ label: "Drugo čitanje", text: r.second_reading });
    if (r.gospel_acclamation) readings.push({ label: "Aleluja", text: r.gospel_acclamation });
    if (r.gospel) readings.push({ label: "Evanđelje", text: r.gospel });

    return {
      source: "litcal",
      date: iso,
      title: primary.name,
      subtitle: seasonLabel(primary.liturgical_season_lcl || primary.liturgical_season),
      seasonWeek: primary.psalter_week ? `Tjedan psaltira ${primary.psalter_week}` : "",
      liturgicalYear: primary.liturgical_year || "",
      color: (primary.color && primary.color[0]) || "green",
      colorLabel: colorLabel(primary.color_lcl || primary.color),
      rank: primary.grade_lcl || primary.grade,
      celebrations: others,
      readings,
      hilpUrl: hilpUrlForDate(iso),
    };
  }

  async function getDay(iso) {
    const date = iso || isoToday();
    const year = parseYear(date);

    try {
      const byDay = await loadLitcalYear(year);
      const events = byDay[date];
      if (events?.length) return mapLitcalDay(date, events);
    } catch (e) {
      console.warn("[PastoralLiturgical] LitCal:", e.message);
    }

    try {
      return await fetchCalapiDay(date);
    } catch (e) {
      console.warn("[PastoralLiturgical] CalAPI:", e.message);
    }

    return {
      source: "offline",
      date,
      title: "Liturgijski podaci nisu učitani",
      subtitle: "Provjerite mrežu ili pokušajte kasnije.",
      readings: null,
      hilpUrl: hilpUrlForDate(date),
    };
  }

  function liturgicalColorClass(color) {
    const c = String(color || "green").toLowerCase();
    if (c === "purple" || c === "violet") return "lit-color--violet";
    if (c === "white") return "lit-color--white";
    if (c === "red") return "lit-color--red";
    if (c === "rose") return "lit-color--rose";
    return "lit-color--green";
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
            ${meta ? `<p class="card-sub">${esc(meta)}</p>` : ""}
            ${extras}
          </div>
          <span class="lit-color-badge ${liturgicalColorClass(day.color)}" title="${esc(day.colorLabel || day.color)}">${esc(day.colorLabel || day.color || "—")}</span>
        </div>
        ${compact ? "" : `<h3 class="lit-readings-title">Čitanja (referenca — latinski opći kalendar)</h3>`}
        ${readingsHtml}
        <div class="lit-card-links">
          <a href="${esc(day.hilpUrl)}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Liturgija dana (HILP)</a>
          <a href="https://www.i-breviary.com/" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Časoslov (iBrevijar)</a>
          ${!compact ? `<button type="button" class="btn btn-ghost btn-sm" data-lit-refresh>↻ Osvježi</button>` : ""}
        </div>
        <p class="lit-source-note">Izvor: ${day.source === "litcal" ? "LitCal API" : day.source === "calapi" ? "Church Calendar API" : "—"} · Imena blagdana na engleskom; za hrvatsku liturgiju koristite HILP.</p>
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
        delete yearIndexCache[parseYear(date)];
        localStorage.removeItem(`${CACHE_PREFIX}${parseYear(date)}`);
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

  function getByDaySync(year) {
    return yearIndexCache[year] || loadYearFromStorage(year) || null;
  }

  /** Sažetak dana iz cachea (bez mreže) — uvijek ima hilpUrl */
  function getSummarySync(iso) {
    const date = iso || isoToday();
    const year = parseYear(date);
    const byDay = getByDaySync(year);
    const events = byDay?.[date];
    if (events?.length) {
      const mapped = mapLitcalDay(date, events);
      if (mapped) {
        return {
          ...mapped,
          shortTitle: truncate(mapped.title, 26),
          loaded: true,
        };
      }
    }
    return {
      source: "pending",
      date,
      title: null,
      shortTitle: null,
      subtitle: "",
      color: "green",
      colorLabel: "",
      hilpUrl: hilpUrlForDate(date),
      loaded: false,
    };
  }

  function summariesForMonth(year, month) {
    const byDay = getByDaySync(year);
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const out = {};
    for (let d = 1; d <= daysInMonth; d++) {
      const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const events = byDay?.[iso];
      if (events?.length) {
        const mapped = mapLitcalDay(iso, events);
        if (mapped) {
          out[iso] = { ...mapped, shortTitle: truncate(mapped.title, 26), loaded: true };
          continue;
        }
      }
      out[iso] = getSummarySync(iso);
    }
    return out;
  }

  /** U ćeliji kalendara: svetac + boja + link na HILP */
  function renderCellLiturgy(summary) {
    const s = summary || {};
    const colorCls = liturgicalColorClass(s.color);
    const feast = s.shortTitle || s.title;
    const feastHtml = feast
      ? `<span class="cal-lit-feast" title="${esc(s.title)}">${esc(feast)}</span>`
      : `<span class="cal-lit-feast cal-lit-feast--muted">—</span>`;
    return `
      <span class="cal-lit-block">
        ${feastHtml}
        <span class="cal-lit-meta">
          ${s.loaded ? `<span class="lit-dot-mark ${colorCls}" aria-hidden="true"></span>` : ""}
          <a class="cal-lit-link" href="${esc(s.hilpUrl || hilpUrlForDate(s.date))}" target="_blank" rel="noopener" title="Liturgija dana (HILP)" onclick="event.stopPropagation()">Liturgija</a>
        </span>
      </span>`;
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
          <strong class="lit-day-strip-feast">${esc(s.title)}</strong>
          ${s.subtitle ? `<span class="card-sub"> · ${esc(s.subtitle)}</span>` : ""}
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

  const _loadLitcalYear = loadLitcalYear;
  async function loadLitcalYear(year) {
    const byDay = await _loadLitcalYear(year);
    notifyYearReady(year);
    return byDay;
  }

  function monthDayDots(byDay, year, month) {
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const dots = {};
    for (let d = 1; d <= daysInMonth; d++) {
      const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const ev = byDay[iso];
      if (ev?.length) {
        const p = pickPrimaryEvent(ev);
        dots[iso] = (p?.color && p.color[0]) || "green";
      }
    }
    return dots;
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
                  const dot = dots[iso] ? ` lit-dot ${liturgicalColorClass(dots[iso])}` : "";
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
    renderDayStrip,
    hydrateDayStrip,
    loadLitcalYear,
    renderDayCard,
    mountInto,
    renderKalendarPage,
    hilpUrlForDate,
    fmtHrDate,
  };
})(typeof window !== "undefined" ? window : global);
