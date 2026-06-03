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
    if (global.PastoralMise?.getMassesForDate && dataOrSchedule?.intentions !== undefined) {
      return global.PastoralMise.getMassesForDate(dataOrSchedule, todayIso());
    }
    const schedule = Array.isArray(dataOrSchedule) ? dataOrSchedule : dataOrSchedule?.massSchedule || [];
    const dow = new Date().getDay();
    const label = dow === 0 ? "Nedjelja" : dow === 6 ? "Subota" : "Pon–Pet";
    return schedule.filter((m) => m.day === label).map((m) => ({ time: m.time, celebrant: m.celebrant || "" }));
  }

  function getOfficeStats(data) {
    const today = todayIso();
    const FC = global.PastoralFamilyCrud;
    const y = new Date().getFullYear();
    const novaPrijave = (data.publicSubmissions || []).filter((s) => s.status === "nova").length;
    const unpaidNakane = (data.intentions || []).filter((n) => !n.paid).length;
    const todayNakane = (data.intentions || []).filter((n) => n.date === today).length;
    const overdueTasks = (data.tasks || []).filter((t) => !t.done && t.due && t.due < today).length;
    const dueTodayTasks = (data.tasks || []).filter((t) => !t.done && t.due === today).length;
    const luknoUnpaid = (data.families || []).filter((f) => FC && !FC.currentYearStatus(f, y).paid).length;
    const upcomingBaptisms = (data.baptisms || []).filter((b) => b.baptismDate && b.baptismDate >= today).length;
    const debtsUnpaid = global.PastoralDebts ? global.PastoralDebts.getUnpaidCount(data) : unpaidNakane + luknoUnpaid;
    const remindersCount = global.PastoralReminders ? global.PastoralReminders.getCount(data) : 0;
    const visitsDue = (data.visits || []).filter((v) => !v.done && v.scheduled && v.scheduled <= today).length;
    const me = global.PastoralStaffMessages?.staffUserFromSession?.() || "";
    const unreadMessages = global.PastoralStaffMessages ? global.PastoralStaffMessages.unreadCount(data, me) : 0;
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
      unreadMessages,
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
    const map = {
      "javne-prijave.html": stats.novaPrijave,
      "nakane.html": stats.unpaidNakane,
      "dugovanja.html": stats.debtsUnpaid,
      "podsjetnici.html": stats.remindersCount,
      "posjete.html": stats.visitsDue,
      "zadaci.html": stats.overdueTasks + stats.dueTodayTasks,
      "obitelji.html": stats.luknoUnpaid > 0 ? stats.luknoUnpaid : 0,
    "poruke.html": stats.unreadMessages > 0 ? stats.unreadMessages : 0,
    };
    document.querySelectorAll(".sidebar .nav a").forEach((a) => {
      const href = a.getAttribute("href") || "";
      const file = href.split("/").pop();
      const n = map[file];
      a.querySelector(".nav-badge")?.remove();
      if (n > 0) {
        const b = document.createElement("span");
        b.className = "nav-badge";
        b.textContent = n > 99 ? "99+" : String(n);
        b.title = `${n} stavki za pregled`;
        a.appendChild(b);
      }
    });
  }

  function ensurePrezentacijaInTopbar() {
    const actions = document.querySelector(".app-shell .topbar .topbar-actions");
    if (!actions || document.getElementById("btn-demo-present")) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-secondary btn-sm";
    btn.id = "btn-demo-present";
    btn.textContent = "Prezentacija";
    btn.addEventListener("click", () => {
      global.PastoralDemo?.openSalesStory?.({ showToast: api.showToast, pageUrl: api.pageUrl });
    });
    actions.insertBefore(btn, actions.firstChild);
    global.PastoralTheme?.repositionInTopbar?.();
  }

  function injectGlobalQuickBar() {
    const topbar = document.querySelector(".app-shell .main .topbar");
    if (!topbar || topbar.querySelector(".priest-global-search")) return;
    const actions = topbar.querySelector(".topbar-actions") || topbar;
    const wrap = document.createElement("div");
    wrap.className = "priest-global-search";
    wrap.innerHTML = `
      <button type="button" class="priest-search-trigger" id="priest-search-open" title="Pretraga (Ctrl+K)">
        <span class="priest-search-ico">⌕</span>
        <span class="priest-search-ph">Pretraži župu…</span>
        <kbd class="priest-kbd">Ctrl+K</kbd>
      </button>
      <button type="button" class="btn btn-ghost btn-sm" id="priest-help-btn" title="Pomoć (?)" aria-label="Pomoć">?</button>
      <button type="button" class="btn btn-ghost btn-sm" id="priest-print-today" title="Ispis lista za danas">🖨 Danas</button>`;
    if (topbar.querySelector(".topbar-actions")) {
      topbar.insertBefore(wrap, topbar.querySelector(".topbar-actions"));
    } else {
      topbar.appendChild(wrap);
    }
    document.getElementById("priest-search-open")?.addEventListener("click", openGlobalSearch);
    document.getElementById("priest-help-btn")?.addEventListener("click", openHelpModal);
    document.getElementById("priest-print-today")?.addEventListener("click", () => printTodaySheet(api.getData()));
  }

  function buildSearchIndex(data) {
    const items = [];
    (data.families || []).forEach((f) => {
      const members = (f.members || []).map((m) => m.name).join(" ");
      items.push({
        type: "Obitelj",
        label: f.surname,
        sub: `${f.address || ""} · ${members}`.trim(),
        href: api.pageUrl("pages/obitelji.html") + `?family=${encodeURIComponent(f.id)}`,
        q: `${f.surname} ${f.address} ${f.phone} ${members}`.toLowerCase(),
      });
    });
    (data.intentions || []).forEach((n) => {
      items.push({
        type: "Nakana",
        label: n.intentionFor,
        sub: `${n.date} ${n.massTime} · ${n.requestedBy || ""}`,
        href: api.pageUrl("pages/nakane.html") + `?date=${n.date}`,
        q: `${n.intentionFor} ${n.requestedBy} ${n.date}`.toLowerCase(),
      });
    });
    (data.tasks || []).forEach((t) => {
      items.push({
        type: "Zadatak",
        label: t.title,
        sub: `${t.due || "bez roka"} · ${t.category}`,
        href: api.pageUrl("pages/zadaci.html"),
        q: `${t.title} ${t.category}`.toLowerCase(),
      });
    });
    (data.baptisms || []).forEach((b) => {
      items.push({
        type: "Krštenje",
        label: b.childName,
        sub: b.baptismDate || "",
        href: api.pageUrl("pages/krsenja.html"),
        q: `${b.childName} ${b.parents}`.toLowerCase(),
      });
    });
    (data.publicSubmissions || []).forEach((s) => {
      if (s.status !== "nova") return;
      const PF = global.PastoralPublicForms;
      const label =
        s.type === "krizma"
          ? `${s.data?.ime || ""} ${s.data?.prezime || ""}`.trim()
          : s.data?.ime_djeteta || s.data?.pokojnik || "Prijava";
      items.push({
        type: PF?.TYPE_LABELS?.[s.type] || "Prijava",
        label,
        sub: new Date(s.submittedAt).toLocaleString("hr-HR"),
        href: api.pageUrl("pages/javne-prijave.html"),
        q: label.toLowerCase(),
      });
    });
    return items;
  }

  function openGlobalSearch() {
    const data = api.getData();
    const index = buildSearchIndex(data);
    const M = global.PastoralModal;
    if (!M) return;

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
        const render = () => {
          const q = input?.value.trim().toLowerCase() || "";
          if (q.length < 2) {
            list.innerHTML = `<li class="priest-search-hint">Npr. „Horvat”, „pokoj”, „krizma”, „ŽPV”…</li>`;
            return;
          }
          const hits = index.filter((it) => it.q.includes(q)).slice(0, 20);
          list.innerHTML = hits.length
            ? hits
                .map(
                  (it) =>
                    `<li><a href="${esc(it.href)}" class="priest-search-hit"><span class="badge">${esc(it.type)}</span><strong>${esc(it.label)}</strong><small>${esc(it.sub)}</small></a></li>`
                )
                .join("")
            : `<li class="priest-search-hint">Nema rezultata za „${esc(q)}”.</li>`;
        };
        input?.addEventListener("input", render);
        render();
        setTimeout(() => input?.focus(), 80);
      },
    });
  }

  function openHelpModal() {
    const M = global.PastoralModal;
    if (!M) return;
    M.openDetail({
      title: "Pomoć — župni ured",
      size: "md",
      body: `
        <div class="priest-help">
          <h3>Prezentacija (prodaja / demo)</h3>
          <p>Gumb <strong>Prezentacija</strong> na ploči — kratka priča za župnika (5 min). Otvorite i <strong>Portal vjernika</strong> u novom prozoru. URL: <code>app.html?prezentacija=1</code> automatski pokreće priču.</p>
          <h3>Uvod u aplikaciju</h3>
          <p>Prvi put nakon prijave kreće obilazak <strong>ekran po ekran</strong> kroz aplikaciju. Ponovno: <strong>Postavke → Ponovi uvod u aplikaciju</strong>.</p>
          <h3>Brzi pristup</h3>
          <ul>
            <li><kbd>Ctrl</kbd>+<kbd>K</kbd> — pretraga cijele župe (obitelji, nakane, zadaci…)</li>
            <li><kbd>?</kbd> — ovaj prozor pomoći</li>
            <li>Gumb <strong>Danas</strong> u traci — ispis nakana i misa za današnji dan</li>
          </ul>
          <h3>Nadzorna ploča</h3>
          <p>Kartice s brojevima vode na odgovarajuće stranice. Crvene značke u izborniku upozoravaju na neplaćene nakane, nove prijave s weba i zakašnjele zadatke.</p>
          <h3>Obitelji</h3>
          <p>Klik na red u tablici otvara karton obitelji. Zatvaranje kartona — samo gumb ×. Nedavno otvorene obitelji nalaze se na ploči.</p>
          <h3>Nakane</h3>
          <p>Tri prikaza: <strong>Danas</strong> (jutarnji ritual), <strong>Kalendar</strong> (planiranje po danima), <strong>Evidencija</strong> (tablica i statistika). Akcije su u traci na vrhu.</p>
          <h3>Raspored misa</h3>
          <p><strong>Danas</strong> — mise s nakana po terminu; <strong>Tjedni raspored</strong> — mreža; <strong>Upravljanje</strong> — termini, blagdanske iznimke, kopiranje za listić.</p>
          <h3>Javni obrasci</h3>
          <p>Prijave s web stranice župe pregledajte pod Javne prijave → Preuzmi u evidenciju.</p>
        </div>`,
    });
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

  function renderQuickActionsHtml(stats) {
    return `
      <section class="card priest-quick-actions">
        <h2 class="section-title">Brzi pristup — župni ured</h2>
        <div class="priest-action-grid">
          <a href="${api.pageUrl("pages/nakane.html")}?date=today" class="priest-action-tile">
            <span class="priest-action-ico">☩</span>
            <strong>Nakane danas</strong>
            <small>${stats.todayNakane} za misu</small>
          </a>
          <a href="${api.pageUrl("pages/obitelji.html")}?action=new-family" class="priest-action-tile">
            <span class="priest-action-ico">👨‍👩‍👧</span>
            <strong>Nova obitelj</strong>
            <small>upis domaćinstva</small>
          </a>
          <a href="${api.pageUrl("pages/javne-prijave.html")}" class="priest-action-tile ${stats.novaPrijave ? "priest-action-tile--alert" : ""}">
            <span class="priest-action-ico">📝</span>
            <strong>Javne prijave</strong>
            <small>${stats.novaPrijave ? stats.novaPrijave + " novih" : "sve pregledano"}</small>
          </a>
          <a href="${api.pageUrl("pages/zadaci.html")}" class="priest-action-tile ${stats.overdueTasks ? "priest-action-tile--alert" : ""}">
            <span class="priest-action-ico">📋</span>
            <strong>Zadaci</strong>
            <small>${stats.openTasks} otvorenih</small>
          </a>
          <a href="${api.pageUrl("pages/mise.html")}?mode=today" class="priest-action-tile">
            <span class="priest-action-ico">◉</span>
            <strong>Raspored misa</strong>
            <small>tjedni plan</small>
          </a>
          <a href="${api.pageUrl("pages/podsjetnici.html")}" class="priest-action-tile ${stats.remindersCount ? "priest-action-tile--alert" : ""}">
            <span class="priest-action-ico">🔔</span>
            <strong>Podsjetnici</strong>
            <small>${stats.remindersCount || 0} stavki</small>
          </a>
          <a href="${api.pageUrl("pages/potvrde.html")}" class="priest-action-tile">
            <span class="priest-action-ico">📜</span>
            <strong>Potvrde</strong>
            <small>ispis iz evidencije</small>
          </a>
          <a href="${api.pageUrl("pages/dugovanja.html")}" class="priest-action-tile">
            <span class="priest-action-ico">€</span>
            <strong>Dugovanja</strong>
            <small>lukno, nakane…</small>
          </a>
          <button type="button" class="priest-action-tile priest-action-tile--demo" id="priest-demo-story">
            <span class="priest-action-ico">✦</span>
            <strong>Prezentacija</strong>
            <small>priča za župu (5 min)</small>
          </button>
        </div>
      </section>`;
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
        return;
      }
      if (
        e.key === "?" &&
        !e.ctrlKey &&
        !e.metaKey &&
        !document.body.classList.contains("onboarding-active") &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        e.preventDefault();
        openHelpModal();
      }
    });
  }

  function enhanceShell() {
    const data = api.getData();
    const stats = getOfficeStats(data);
    enhanceNavBadges(stats);
    ensurePrezentacijaInTopbar();
    injectGlobalQuickBar();
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
    openHelpModal,
  };
})(typeof window !== "undefined" ? window : global);
