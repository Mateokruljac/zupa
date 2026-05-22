/**
 * Demo / prodajni „wow” — hero, priča, portal vjernika
 */
(function (global) {
  const STORY_KEY = "pastoral_story_seen";

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function greeting() {
    const h = new Date().getHours();
    if (h < 11) return "Dobro jutro";
    if (h < 18) return "Dobar dan";
    return "Dobra večer";
  }

  function computeWowStats(data) {
    const families = (data.families || []).length;
    const members = (data.families || []).reduce((s, f) => s + (f.members?.length || 0), 0);
    const intentions = (data.intentions || []).length;
    const paid = (data.intentions || []).filter((n) => n.paid).length;
    const debts = global.PastoralDebts ? global.PastoralDebts.getUnpaidCount(data) : 0;
    const reminders = global.PastoralReminders ? global.PastoralReminders.getCount(data) : 0;
    const sacraments =
      (data.baptisms?.length || 0) +
      (data.weddings?.length || 0) +
      (data.confirmations?.reduce((s, g) => s + (g.candidates?.length || 0), 0) || 0);
    return { families, members, intentions, paid, debts, reminders, sacraments };
  }

  function renderHeroHtml(data, settings, api) {
    const s = computeWowStats(data);
    const today = new Date().toLocaleDateString("hr-HR", { weekday: "long", day: "numeric", month: "long" });
    const publicUrl = api.pageUrl("public/index.html");
    const trust = global.PastoralSecurity?.renderTrustStrip() || "";

    return `
      <section class="demo-hero card wide" id="demo-hero">
        <div class="demo-hero-bg" aria-hidden="true"></div>
        <div class="demo-hero-inner">
          <div class="demo-hero-text">
            <p class="demo-hero-kicker">${esc(greeting())}, ${esc(settings.pastor || "župniče")}</p>
            <h2 class="demo-hero-title">${esc(settings.shortName || settings.name)}</h2>
            <p class="demo-hero-sub">${esc(today)} · jedan uvid u cijelu župu — bez papira i Excel tablica</p>
            <div class="demo-hero-actions">
              <button type="button" class="btn btn-primary" id="demo-story-btn">Pokreni prezentaciju (5 min)</button>
              <button type="button" class="btn btn-secondary btn-sm" id="demo-print-today">Ispis za danas</button>
              <a href="${publicUrl}" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Portal vjernika ↗</a>
              <a href="${api.pageUrl("pages/sigurnost.html")}" class="btn btn-ghost btn-sm">Sigurnost</a>
            </div>
            ${trust}
          </div>
          <div class="demo-hero-stats">
            <div class="demo-stat" data-count="${s.families}"><span class="demo-stat-val">0</span><span class="demo-stat-label">obitelji</span></div>
            <div class="demo-stat" data-count="${s.members}"><span class="demo-stat-val">0</span><span class="demo-stat-label">vjernika</span></div>
            <div class="demo-stat" data-count="${s.intentions}"><span class="demo-stat-val">0</span><span class="demo-stat-label">nakana</span></div>
            <div class="demo-stat demo-stat--accent" data-count="${s.reminders}"><span class="demo-stat-val">0</span><span class="demo-stat-label">za danas</span></div>
          </div>
        </div>
      </section>
      <section class="card demo-portal-preview">
        <div class="demo-portal-copy">
          <h2 class="section-title">Kako vas vjernici vide</h2>
          <p class="card-sub">Javni portal župe — obrasci bez prijave u ured, vaš branding i boje.</p>
          <a href="${publicUrl}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Otvori demo portal</a>
        </div>
        <div class="demo-portal-mock" aria-hidden="true">
          <div class="demo-portal-screen">
            <p class="demo-portal-bar">${esc(settings.shortName || "Župa")}</p>
            <ul>
              <li>Prijava za krizmu</li>
              <li>Prijava za krštenje</li>
              <li>Prva sv. Pričest</li>
              <li>Prijava za ukop</li>
            </ul>
          </div>
        </div>
      </section>`;
  }

  function animateStats() {
    document.querySelectorAll(".demo-stat[data-count]").forEach((el) => {
      const target = Number(el.dataset.count) || 0;
      const valEl = el.querySelector(".demo-stat-val");
      if (!valEl) return;
      const duration = 900;
      const start = performance.now();
      function tick(now) {
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - (1 - t) ** 3;
        valEl.textContent = String(Math.round(target * eased));
        if (t < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  const STORY_SLIDES = [
    {
      title: "Problem: župni ured na papiru",
      body: "Nakane u bilježnici, lukno u Excelu, priprema braka u mapi, javne prijave na e-mailu… Svećenik gubi vrijeme tražeći podatke umjesto da bude s ljudima.",
    },
    {
      title: "Pastoral: sve na jednom mjestu",
      body: "Nadzorna ploča pokazuje što je danas važno. Podsjetnici skupljaju lukno, nakane, posjete, prijave i zadatke — jedan inbox.",
    },
    {
      title: "Obitelj = karton domaćinstva",
      body: "Članovi, sakramenti, lukno po godinama, pastoralne bilješke. Klik na obitelj — cijela slika za posjet ili telefonski razgovor.",
    },
    {
      title: "Liturgija i novac — pod kontrolom",
      body: "Kalendar nakana, Gregorijanska serija (30 misa), župni list za tisak, dugovanja, računi i blagajna za ŽEV.",
    },
    {
      title: "Potvrde i dokumenti u minuti",
      body: "Pristupnica, izvadak krštenja, potvrda uplate — ispis iz evidencije. Serijski ispis iz Excela za cijelu skupinu krizmanika.",
    },
    {
      title: "Vjernici dolaze k vama online",
      body: "Javni portal: prijave za sakramente stižu u ured. Manje telefona u župnikovu stanu — više vremena za služenje.",
    },
    {
      title: "Sigurnost i povjerenje",
      body: "Pristup po ulogama (župnik, upravitelj, kateheta). Javni portal odvojen od financija i matice. GDPR, sesija, audit u produkciji — HTTPS i backup na serveru.",
    },
    {
      title: "Spremno za vašu župu",
      body: "Demo podaci za prezentaciju. Produkcija: vaša župa, matične knjige, uloge ureda i blagajne, sigurna pohrana u oblaku. Stranica Sigurnost — za razgovor s župom.",
    },
  ];

  function openSalesStory(api) {
    const M = global.PastoralModal;
    if (!M) return;
    let idx = 0;

    function renderSlide() {
      const s = STORY_SLIDES[idx];
      const foot = document.getElementById("story-foot");
      if (foot) {
        foot.innerHTML = `
          <span class="card-sub">${idx + 1} / ${STORY_SLIDES.length}</span>
          <div>
            ${idx > 0 ? '<button type="button" class="btn btn-ghost" data-story-prev>Nazad</button>' : ""}
            ${idx < STORY_SLIDES.length - 1 ? '<button type="button" class="btn btn-primary" data-story-next>Sljedeće</button>' : '<button type="button" class="btn btn-primary" data-story-done>Završi — istraži aplikaciju</button>'}
          </div>`;
      }
      const title = document.getElementById("story-title");
      const body = document.getElementById("story-body");
      if (title) title.textContent = s.title;
      if (body) body.textContent = s.body;
    }

    M.openDetail({
      title: "Prezentacija za župu",
      size: "lg",
      body: `
        <div class="demo-story">
          <h3 id="story-title" class="demo-story-title"></h3>
          <p id="story-body" class="demo-story-body"></p>
          <div class="demo-story-dots">${STORY_SLIDES.map((_, i) => `<span class="demo-story-dot ${i === 0 ? "is-on" : ""}" data-dot="${i}"></span>`).join("")}</div>
          <div id="story-foot" class="demo-story-foot"></div>
        </div>`,
      onOpen: (overlay) => {
        renderSlide();
        overlay.addEventListener("click", (e) => {
          if (e.target.closest("[data-story-next]")) {
            idx = Math.min(STORY_SLIDES.length - 1, idx + 1);
            overlay.querySelectorAll(".demo-story-dot").forEach((d, i) => d.classList.toggle("is-on", i === idx));
            renderSlide();
          }
          if (e.target.closest("[data-story-prev]")) {
            idx = Math.max(0, idx - 1);
            overlay.querySelectorAll(".demo-story-dot").forEach((d, i) => d.classList.toggle("is-on", i === idx));
            renderSlide();
          }
          if (e.target.closest("[data-story-done]")) {
            M.close();
            saveStateSeen();
            api.showToast?.("Istražite Podsjetnike, Nakane i Obitelji");
            setTimeout(() => {
              location.href = api.pageUrl("pages/podsjetnici.html");
            }, 400);
          }
          const dot = e.target.closest("[data-dot]");
          if (dot) {
            idx = Number(dot.dataset.dot);
            overlay.querySelectorAll(".demo-story-dot").forEach((d, i) => d.classList.toggle("is-on", i === idx));
            renderSlide();
          }
        });
      },
    });
  }

  function saveStateSeen() {
    localStorage.setItem(STORY_KEY, "1");
  }

  function bindHero(api) {
    document.getElementById("demo-story-btn")?.addEventListener("click", () => openSalesStory(api));
    document.getElementById("demo-print-today")?.addEventListener("click", () => {
      global.PastoralPriestTools?.printTodaySheet();
    });
    global.PastoralSecurity?.bindTrustStrip(document.getElementById("demo-hero"), api);
    requestAnimationFrame(animateStats);
    if (!localStorage.getItem(STORY_KEY) && location.search.includes("prezentacija=1")) {
      setTimeout(() => openSalesStory(api), 600);
    }
  }

  function mountDashboardWow(api) {
    const data = api.getData();
    const settings = api.getSettings();
    const html = renderHeroHtml(data, settings, api);
    return { html, bind: () => bindHero(api) };
  }

  global.PastoralDemo = {
    mountDashboardWow,
    openSalesStory,
    computeWowStats,
  };
})(typeof window !== "undefined" ? window : global);
