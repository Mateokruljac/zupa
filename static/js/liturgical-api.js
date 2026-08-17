/**
 * Katolički liturgijski kalendar — vanjski API-ji
 *
 * Izvori:
 * - Romcal Croatia + LitCal VA — slavlja, liturgijsko vrijeme, boja i čitanja
 * - Church Calendar API (http://calapi.inadiutorium.cz) — rezerva za dan (bez čitanja)
 * - HILP liturgija dana — puni hrvatski tekst (poveznica, nema javnog API-ja)
 */
(function (global) {
  const LITCAL_BASE = "https://litcal.johnromanodorazio.com/api/v5/calendar";
  const CALAPI_BASE = "http://calapi.inadiutorium.cz/api/v0/en/calendars/default";
  const HILP_LITURGY = "https://hilp.hr/liturgija-dana/";
  const CACHE_PREFIX = "pastoral_litcal_v5_";

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

  function useDjangoLiturgical() {
    return typeof location !== "undefined" && location.pathname.startsWith("/");
  }

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
      const byDay = parsed?.byDay;
      if (byDay && parsed?.fetchedAt && Object.keys(byDay).length > 30) return byDay;
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
    const data = await res.json();
    if (data?.status >= 400 || data?.title === "Too Many Requests") {
      throw new Error(data.detail || data.title || `HTTP ${data.status}`);
    }
    return data;
  }

  function litcalBundleUrl(year) {
    try {
      if (global.PastoralBase?.asset) {
        return global.PastoralBase.asset(`data/litcal/${year}.json`);
      }
      const path = global.location?.pathname || "";
      const base = path.includes("/pages/") ? "../data/litcal" : "data/litcal";
      return `${base}/${year}.json`;
    } catch {
      return `data/litcal/${year}.json`;
    }
  }

  async function fetchLocalLitcalBundle(year) {
    const data = await fetchJson(litcalBundleUrl(year));
    const events = data.litcal || data.Litcal || [];
    if (!events.length) throw new Error("Prazan lokalni kalendar");
    return events;
  }

  async function fetchRemoteLitcalYear(year) {
    const url = `${LITCAL_BASE}?year=${year}&return_type=JSON`;
    const data = await fetchJson(url);
    const events = data.litcal || data.Litcal || [];
    if (!events.length) throw new Error("Prazan API odgovor");
    return events;
  }

  async function prefetchMonthHr(civilYear, month) {
    if (!useDjangoLiturgical()) return;
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

    if (useDjangoLiturgical()) {
      try {
        await fetchDjangoLiturgicalYear(year);
        yearIndexCache[year] = {};
        return yearIndexCache[year];
      } catch (djangoError) {
        console.warn(
          "[PastoralLiturgical] Django kalendar nije dostupan, koristim postojeću rezervu:",
          djangoError.message
        );
      }
    }

    const stored = loadYearFromStorage(year);
    if (stored) {
      yearIndexCache[year] = stored;
      return stored;
    }

    let events;
    try {
      events = await fetchLocalLitcalBundle(year);
    } catch (localErr) {
      console.warn("[PastoralLiturgical] Lokalni kalendar:", localErr.message);
      events = await fetchRemoteLitcalYear(year);
    }

    const byDay = buildIndexFromLitcal(events);
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

    const rankRaw = main?.rank || "";
    return {
      source: "calapi",
      date: day.date || iso,
      title: main?.title || formatCalapiFerial(day),
      subtitle: CALAPI_SEASON_HR[day.season] || day.season,
      seasonWeek: day.season_week,
      color: main?.colour || "green",
      colorLabel: COLOR_HR[main?.colour] || main?.colour,
      rank: rankRaw,
      rankLabel: formatRankHr(CALAPI_RANK_HR[rankRaw] || rankRaw),
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
    const candidates = events.filter((e) => !e.is_vigil_mass);
    if (!candidates.length) return events[0];
    return candidates.sort((a, b) => (b.grade || 0) - (a.grade || 0))[0];
  }

  function eventColor(ev) {
    if (!ev) return null;
    const c = ev.color;
    if (Array.isArray(c) && c.length) return String(c[0]).toLowerCase();
    if (typeof c === "string" && c) return c.toLowerCase();
    return null;
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

    const rankRaw = primary.grade ?? primary.grade_lcl ?? "";
    return {
      source: "litcal",
      date: iso,
      title: primary.name,
      subtitle: seasonLabel(primary.liturgical_season_lcl || primary.liturgical_season),
      seasonWeek: primary.psalter_week ? `Tjedan psaltira ${primary.psalter_week}` : "",
      liturgicalYear: primary.liturgical_year || "",
      color: eventColor(primary) || "green",
      colorLabel: colorLabel(primary.color_lcl || primary.color),
      rank: rankRaw,
      rankLabel: formatRankHr(rankRaw),
      celebrations: others,
      readings,
      hilpUrl: hilpUrlForDate(iso),
    };
  }

  async function getDay(iso) {
    const date = iso || isoToday();

    if (useDjangoLiturgical()) {
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
        console.warn("[PastoralLiturgical] Django dan:", e.message);
      }
    }

    try {
      await loadLitcalYearsForDate(date);
      const mapped = getMappedDay(date);
      if (mapped) return mapped;
      const events = resolveEventsForDate(date);
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
    const calKey = raw.toLowerCase();
    if (CALAPI_RANK_HR[calKey]) return CALAPI_RANK_HR[calKey];
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

  function getByDaySync(year) {
    return yearIndexCache[year] || loadYearFromStorage(year) || null;
  }

  /** LitCal calendar/Y pokriva advent (god. Y−1) do kasnog studenog (god. Y) — traži u susjednim godinama */
  function resolveEventsForDate(iso) {
    const y = parseYear(iso);
    for (const calYear of [y, y + 1, y - 1]) {
      const byDay = getByDaySync(calYear);
      const events = byDay?.[iso];
      if (events?.length) return events;
    }
    return null;
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
    if (!useDjangoLiturgical()) {
      const events = resolveEventsForDate(date);
      if (events?.length) {
        const local = mapLitcalDay(date, events);
        if (local) {
          return {
            ...local,
            shortTitle: truncate(local.title, 38),
            loaded: true,
          };
        }
      }
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
      if (!useDjangoLiturgical()) {
        const events = resolveEventsForDate(iso);
        if (events?.length) {
          const mapped = mapLitcalDay(iso, events);
          if (mapped) {
            out[iso] = { ...mapped, shortTitle: truncate(mapped.title, 38), loaded: true };
            continue;
          }
        }
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
    const sourceNote =
      d.source === "romcal+litcal-va"
        ? "Romcal Croatia + LitCal VA"
        : d.source === "litcal"
          ? "LitCal API"
        : d.source === "calapi"
          ? "Church Calendar API"
          : d.source === "offline"
            ? "—"
            : "LitCal (lokalna kopija)";

    if (d.source === "offline" || !d.title) {
      return `<div class="nakane-lit-detail" id="nakane-lit-detail">
        <p class="card-sub">Liturgijski podaci nisu učitani. Otvorite stranicu preko lokalnog poslužitelja (<code>npx serve .</code>) ili provjerite mrežu.</p>
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
      <p class="card-sub">Učitavam liturgijski dan (Romcal + LitCal)…</p>
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
    renderNakaneDayLiturgy,
    renderNakaneLitLoading,
    renderDayStrip,
    hydrateDayStrip,
    loadLitcalYear,
    loadLitcalYearsForMonth,
    loadLitcalYearsForDate,
    prefetchMonthHr,
    resolveEventsForDate,
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
