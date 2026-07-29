/**
 * Olakšice za župni ured — pretraga, brzi pristup, ispisi, značke u izborniku
 */
(function (global) {
  const RECENT_KEY = "pastoral_recent_families";
  const MAX_RECENT = 8;
  let api = null;

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }

  function getMassesForToday(dataOrSchedule) {
    const schedule = Array.isArray(dataOrSchedule) ? dataOrSchedule : dataOrSchedule?.massSchedule || [];
    const dow = new Date().getDay();
    const label = dow === 0 ? "Nedjelja" : dow === 6 ? "Subota" : "Pon–Pet";
    return schedule.filter((m) => m.day === label).map((m) => ({ time: m.time, celebrant: m.celebrant || "" }));
  }

  function luknoUnpaidCount(data, year) {
    let n = 0;
    for (const fam of data.families || []) {
      const row = (fam.contributions || []).find((c) => c.year === year);
      if (!row || !row.luknoPaid) n += 1;
    }
    return n;
  }

  const FORM_LABELS = {
    "prijava-krizma": "Krizma",
    "prijava-krsenje": "Krštenje",
    "prijava-pricest": "Prva pričest",
    "prijava-ukop": "Ukop",
  };

  function readOfficeStats() {
    return global.PastoralApi?.readOfficeStats?.() || null;
  }

  function getOfficeStats(data) {
    const fromServer = readOfficeStats();
    if (fromServer && !data?.families?.length) {
      return {
        novaPrijave: fromServer.nova_prijave || 0,
        unpaidNakane: fromServer.unpaid_nakane || 0,
        todayNakane: fromServer.today_nakane || 0,
        overdueTasks: fromServer.overdue_tasks || 0,
        dueTodayTasks: fromServer.due_today_tasks || 0,
        luknoUnpaid: fromServer.lukno_unpaid || 0,
        debtsUnpaid: fromServer.debts_unpaid || 0,
        remindersCount: fromServer.reminders_count || 0,
        visitsDue: fromServer.visits_due || 0,
        openTasks: fromServer.open_tasks || 0,
        upcomingBaptisms: 0,
        unreadMessages: 0,
      };
    }
    const today = todayIso();
    const y = new Date().getFullYear();
    const novaPrijave = (data.publicSubmissions || []).filter((s) => s.status === "nova").length;
    const unpaidNakane = (data.intentions || []).filter((n) => !n.paid).length;
    const todayNakane = (data.intentions || []).filter((n) => n.date === today).length;
    const overdueTasks = (data.tasks || []).filter((t) => !t.done && t.due && t.due < today).length;
    const dueTodayTasks = (data.tasks || []).filter((t) => !t.done && t.due === today).length;
    const luknoUnpaid = luknoUnpaidCount(data, y);
    const upcomingBaptisms = (data.baptisms || []).filter((b) => b.baptismDate && b.baptismDate >= today).length;
    const debtsUnpaid = unpaidNakane + luknoUnpaid + (data.parishDebts || []).filter((d) => !d.paid).length;
    const remindersCount = (data.publicSubmissions || []).filter((s) => s.status === "nova").length + overdueTasks;
    const visitsDue = (data.visits || []).filter((v) => !v.done && v.scheduled && v.scheduled <= today).length;
    return {
      novaPrijave,
      unpaidNakane,
      todayNakane,
      overdueTasks,
      dueTodayTasks,
      luknoUnpaid,
      debtsUnpaid,
      remindersCount,
      visitsDue,
      openTasks: (data.tasks || []).filter((t) => !t.done).length,
      upcomingBaptisms,
      unreadMessages: 0,
    };
  }

  function getRecentFamilyIds() {
    try {
      return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
    } catch {
      return [];
    }
  }

  function trackRecentFamily(familyId) {
    if (!familyId) return;
    let ids = getRecentFamilyIds().filter((id) => id !== familyId);
    ids.unshift(familyId);
    ids = ids.slice(0, MAX_RECENT);
    localStorage.setItem(RECENT_KEY, JSON.stringify(ids));
  }

  function enhanceNavBadges(stats) {
    /* Badgeovi u sidebaru dolaze s servera (nav_badges u base.html). */
    void stats;
  }

  function resolveSearchHref(href) {
    if (!href) return api.pageUrl("app");
    if (href.startsWith("http") || href.startsWith("/")) return href;
    const [slug, qs] = href.split("?");
    const clean = slug.replace(/^\/?pages\//, "").replace(/\.html$/, "");
    const base = global.PastoralBase?.isDjango?.()
      ? `/pages/${clean}/`
      : api.pageUrl(`pages/${clean}.html`);
    return qs ? `${base}?${qs}` : base;
  }

  function openGlobalSearch() {
    const M = global.PastoralModal;
    if (!M) return;

    let debounce = null;

    const openModal = () => {
      M.openDetail({
        title: "Brza pretraga",
        size: "lg",
        body: `
        <div class="priest-search-modal">
          <input type="search" id="priest-search-input" class="priest-search-input" placeholder="Prezime, nakana, zadatak, dijete…" autocomplete="off" />
          <p class="card-sub">Upišite najmanje 2 znaka. Odaberite red za otvaranje stranice.</p>
          <ul class="priest-search-results" id="priest-search-results"></ul>
        </div>`,
        onOpen: (overlay) => {
          const input = overlay.querySelector("#priest-search-input");
          const list = overlay.querySelector("#priest-search-results");
          const render = (hits) => {
            const q = input?.value.trim() || "";
            if (q.length < 2) {
              list.innerHTML = `<li class="priest-search-hint">Npr. „Horvat”, „pokoj”, „krizma”, „ŽPV”…</li>`;
              return;
            }
            list.innerHTML = hits.length
              ? hits
                  .map(
                    (it) =>
                      `<li><a href="${esc(resolveSearchHref(it.href))}" class="priest-search-hit"><span class="badge">${esc(it.type)}</span><strong>${esc(it.label)}</strong><small>${esc(it.sub || "")}</small></a></li>`
                  )
                  .join("")
              : `<li class="priest-search-hint">Nema rezultata za „${esc(q)}”.</li>`;
          };
          const fetchHits = () => {
            const q = input?.value.trim() || "";
            if (q.length < 2) {
              render([]);
              return;
            }
            fetch(`/api/search/?q=${encodeURIComponent(q)}`, { credentials: "same-origin" })
              .then((r) => r.json())
              .then((data) => render(data.results || []))
              .catch(() => render([]));
          };
          input?.addEventListener("input", () => {
            clearTimeout(debounce);
            debounce = setTimeout(fetchHits, 200);
          });
          render([]);
          setTimeout(() => input?.focus(), 80);
        },
      });
    };

    openModal();
  }


  function printTodaySheet(data) {
    const today = todayIso();
    const settings = api.getSettings?.() || {};
    const masses = getMassesForToday(data);
    const intentions = (data.intentions || []).filter((n) => n.date === today);
    const tasks = (data.tasks || []).filter((t) => !t.done && (t.due === today || (t.due && t.due < today)));
    const dateLabel = new Date(today + "T12:00:00").toLocaleDateString("hr-HR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });

    const html = `<!DOCTYPE html><html lang="hr"><head><meta charset="UTF-8"><title>Župa — ${dateLabel}</title>
      <style>
        body{font-family:Georgia,serif;padding:24px;color:#222;max-width:720px;margin:0 auto}
        h1{font-size:1.4rem;margin:0 0 4px} h2{font-size:1rem;margin:24px 0 8px;border-bottom:1px solid #ccc}
        table{width:100%;border-collapse:collapse;font-size:0.9rem}
        th,td{border:1px solid #ddd;padding:8px;text-align:left}
        th{background:#f5f0e8}
        .meta{color:#555;font-size:0.85rem;margin-bottom:20px}
        @media print{body{padding:12px}}
      </style></head><body>
      <h1>${esc(settings.name || "Župa")}</h1>
      <p class="meta">${esc(dateLabel)} · ${esc(settings.pastor || "")}</p>
      <h2>Mise danas</h2>
      ${masses.length ? `<ul>${masses.map((m) => `<li><strong>${esc(m.time)}</strong></li>`).join("")}</ul>` : "<p>—</p>"}
      <h2>Misne nakane (${intentions.length})</h2>
      ${intentions.length
        ? `<table><thead><tr><th>Misa</th><th>Za koga</th><th>Naručitelj</th><th>Stipendij</th><th>Plaćeno</th></tr></thead><tbody>
        ${intentions
          .sort((a, b) => a.massTime.localeCompare(b.massTime))
          .map(
            (n) =>
              `<tr><td>${esc(n.massTime)}</td><td>${esc(n.intentionFor)}</td><td>${esc(n.requestedBy || "—")}</td><td>${n.stipend} €</td><td>${n.paid ? "da" : "ne"}</td></tr>`
          )
          .join("")}</tbody></table>`
        : "<p>Nema nakana za danas.</p>"}
      <h2>Zadaci (danas / zakašnjeli)</h2>
      ${tasks.length
        ? `<ul>${tasks.map((t) => `<li>${esc(t.title)} — rok ${esc(t.due || "—")} <em>(${esc(t.priority)})</em></li>`).join("")}</ul>`
        : "<p>Nema hitnih zadataka.</p>"}
      <p class="meta" style="margin-top:32px">Ispis iz Pastoral · ${new Date().toLocaleString("hr-HR")}</p>
      <script>window.onload=function(){window.print();}</script>
      </body></html>`;

    const w = window.open("", "_blank");
    if (!w) {
      api.showToast("Omogućite skočne prozore za ispis");
      return;
    }
    w.document.write(html);
    w.document.close();
  }


  function renderTodayMassesHtml(data) {
    const masses = getMassesForToday(data);
    const today = todayIso();
    const dayLabel = new Date(today + "T12:00:00").toLocaleDateString("hr-HR", { weekday: "long" });
    return `
      <section class="card">
        <h2 class="section-title">Mise danas — ${esc(dayLabel)}</h2>
        ${masses.length
          ? `<div class="mass-schedule">${masses
              .map(
                (m) =>
                  `<div class="mass-chip mass-chip--today"><strong>${esc(m.time)}</strong>${m.celebrant ? `<br><small>${esc(m.celebrant)}</small>` : ""}</div>`
              )
              .join("")}</div>`
          : '<p class="empty-state">Nema upisanih misa za ovaj dan u tjednom rasporedu.</p>'}
        <a href="${api.pageUrl("pages/mise.html")}?mode=today" class="btn btn-secondary btn-sm">Raspored misa</a>
        <a href="${api.pageUrl("pages/nakane.html")}?date=today" class="btn btn-primary btn-sm">Nakane za danas</a>
      </section>`;
  }

  function renderRecentFamiliesHtml(data) {
    const ids = getRecentFamilyIds();
    const fams = ids.map((id) => (data.families || []).find((f) => f.id === id)).filter(Boolean);
    if (!fams.length) return "";
    return `
      <section class="card">
        <h2 class="section-title">Nedavno otvorene obitelji</h2>
        <ul class="priest-recent-list">
          ${fams
            .map(
              (f) =>
                `<li><a href="${api.pageUrl("pages/obitelji.html")}?family=${encodeURIComponent(f.id)}"><strong>${esc(f.surname)}</strong><small>${esc(f.address || "")}</small></a></li>`
            )
            .join("")}
        </ul>
      </section>`;
  }

  function renderQuickActionsHtml() {
    return "";
  }

  function renderDashboardExtras(data, stats) {
    return (
      renderQuickActionsHtml(stats) +
      `<div class="dashboard-grid dashboard-grid--priest">` +
      renderTodayMassesHtml(data) +
      renderRecentFamiliesHtml(data) +
      `</div>`
    );
  }

  function bindKeyboardShortcuts() {
    if (document.body.dataset.priestKeys) return;
    document.body.dataset.priestKeys = "1";
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        openGlobalSearch();
      }
    });
  }

  function enhanceShell() {
    const stats = readOfficeStats() || getOfficeStats(api.getData());
    enhanceNavBadges(stats);
    global.PastoralTheme?.repositionInTopbar?.();
    bindKeyboardShortcuts();
    return stats;
  }

  global.PastoralPriestTools = {
    init(hooks) {
      api = hooks;
    },
    enhanceShell,
    getOfficeStats,
    trackRecentFamily,
    renderDashboardExtras,
    printTodaySheet: () => printTodaySheet(api.getData()),
    openGlobalSearch,
  };
})(typeof window !== "undefined" ? window : global);
