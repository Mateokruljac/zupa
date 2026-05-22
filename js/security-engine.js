/**
 * Sigurnost i privatnost — prezentacija za župu (demo)
 */
(function (global) {
  const PILLARS = [
    {
      id: "access",
      icon: "🔐",
      title: "Pristup po ulogama",
      summary: "Grupe korisnika — posebno Svećenici župe — određuju koji modul je vidljiv.",
      detail:
        "Stranica Korisnici i grupe: svećenici, upravitelj, katehete, vijeća. Demo: e-mail iz popisa + uloga. Produkcija: lozinka, audit log po korisniku.",
      demo: true,
    },
    {
      id: "session",
      icon: "⏱",
      title: "Sesija i odjava",
      summary: "Automatska odjava nakon neaktivnosti; eksplicitna odjava u izborniku.",
      detail:
        "Demo sprema vrijeme prijave u pregledniku. Produkcija: kratko trajanje sesije, zaključavanje zaslona na zajedničkom računalu u uredu.",
      demo: true,
    },
    {
      id: "gdpr",
      icon: "📋",
      title: "GDPR i podaci vjernika",
      summary: "Podaci služe pastoralnoj službi; privole za kontakt i javne prijave.",
      detail:
        "Svi podaci o župljanima (ime, adresa, sakramenti, kontakt) obrađuju se radi pastoralne službe, ne za marketing. Privola na portalu; pravo na ispravak i brisanje u granicama kanonskog prava.",
      demo: true,
    },
    {
      id: "public",
      icon: "🌐",
      title: "Javni obrasci odvojeni",
      summary: "Portal vjernika nema pristup matičnim knjigama ni financijama.",
      detail:
        "Vjernik šalje samo obrazac (krizma, krštenje…). Podaci ulaze u red čekanja — župni ured odobrava unos u evidenciju.",
      demo: true,
    },
    {
      id: "transport",
      icon: "🔒",
      title: "Prijenos i pohrana",
      summary: "Produkcija: HTTPS, šifrirana baza, sigurnosne kopije.",
      detail:
        "Demo koristi localStorage u pregledniku (samo prezentacija). Na serveru: EU hosting, dnevni backup, odvojena produkcijska župa (jedan tenant = jedna župa).",
      demo: false,
    },
    {
      id: "audit",
      icon: "📜",
      title: "Dnevnik događaja",
      summary: "Tko je izdao račun, tko je označio plaćeno, tko je uredio obitelj.",
      detail: "U produkciji svaka osjetljiva radnja zapisuje se s datumom i korisnikom — za biskupiju i unutarnju kontrolu.",
      demo: false,
    },
  ];

  function getSessionInfo() {
    try {
      const raw = localStorage.getItem("pastoral_session");
      if (!raw) return null;
      const s = JSON.parse(raw);
      if (s.expiresAt && Date.now() > s.expiresAt) return { expired: true };
      return s;
    } catch {
      return { legacy: true };
    }
  }

  function renderTrustStrip() {
    return `
      <div class="security-trust-strip" role="list">
        ${PILLARS.filter((p) => p.demo)
          .map(
            (p) =>
              `<span class="security-trust-item" role="listitem" title="${p.title}"><span aria-hidden="true">${p.icon}</span> ${p.title}</span>`
          )
          .join("")}
        <a href="#" class="security-trust-more" data-security-open>Svi detalji →</a>
      </div>`;
  }

  function mountSecurityPage(root, api) {
    const esc = api.escapeHtml;
    const session = getSessionInfo();
    const sessionLine = session?.expired
      ? '<span class="badge badge-urgent">Sesija istekla — prijavite se ponovo</span>'
      : session?.loginAt
        ? `<span class="badge badge-done">Prijavljeni: ${esc(session.role || "—")} · ${new Date(session.loginAt).toLocaleString("hr-HR")}</span>`
        : '<span class="badge">Niste prijavljeni</span>';

    root.innerHTML = `
      <section class="card security-hero">
        <h2 class="section-title">Sigurnost i povjerenje</h2>
        <p class="card-sub">Za župu su osobni podaci vjernika i financije osjetljivi. Pastoral je građen da to bude jasno i jednostavno.</p>
        <p>${sessionLine}</p>
      </section>
      <div id="encryption-demo-mount"></div>
      <div class="security-grid">
        ${PILLARS.map(
          (p) => `
          <article class="card security-card">
            <span class="security-card-ico">${p.icon}</span>
            <h3>${esc(p.title)}</h3>
            <p><strong>${esc(p.summary)}</strong></p>
            <p class="card-sub">${esc(p.detail)}</p>
            ${p.demo ? '<span class="badge">U demo-u</span>' : '<span class="badge">Produkcija</span>'}
          </article>`
        ).join("")}
      </div>
      <section class="card wide">
        <h2 class="section-title">Demo vs produkcija</h2>
        <table class="data-table">
          <thead><tr><th></th><th>Demo (sada)</th><th>Produkcija</th></tr></thead>
          <tbody>
            <tr><td>Prijava</td><td>OTP kod na stranici (demo)</td><td>OTP e-mail + HTTPS</td></tr>
            <tr><td>Podaci</td><td>Preglednik (localStorage)</td><td>Server EU, backup</td></tr>
            <tr><td>Javni portal</td><td>Isti podaci u pregledniku</td><td>Odvojen URL, CAPTCHA, rate limit</td></tr>
            <tr><td>Financije</td><td>Simulacija plaćanja</td><td>Bez spremanja kartice; žiro/Blagajna</td></tr>
          </tbody>
        </table>
      </section>
      <section class="card">
        <h2 class="section-title">Prezentacija za župnika (2 min)</h2>
        <ol class="security-pitch">
          <li><strong>Vi kontrolirate tko vidi što</strong> — ured nije otvoren internet.</li>
          <li><strong>Vjernik ne ulazi u vašu evidenciju</strong> — samo šalje prijavu.</li>
          <li><strong>GDPR</strong> — podaci u svrhu službe, ne prodaje marketinga.</li>
          <li><strong>Na serveru</strong> — šifriranje, kopije, jedna župa = jedan zatvoreni prostor podataka.</li>
        </ol>
        <button type="button" class="btn btn-primary btn-sm" id="sec-copy-pitch">Kopiraj tekst za sastanak</button>
      </section>`;

    global.PastoralGdpr?.mountGdprOnSecurityPage(root, api);

    const encMount = root.querySelector("#encryption-demo-mount");
    if (encMount && global.PastoralEncryptionDemo) {
      global.PastoralEncryptionDemo.mountEncryptionDemo(encMount, api);
    }

    root.querySelector("#sec-copy-pitch")?.addEventListener("click", async () => {
      const text = root.querySelector(".security-pitch")?.innerText || "";
      try {
        await navigator.clipboard.writeText(text);
        api.showToast("Kopirano");
      } catch {
        api.showToast("Kopiraj ručno");
      }
    });
  }

  function openSecurityModal(api) {
    global.PastoralModal?.openDetail({
      title: "Sigurnost u kratkim crtama",
      size: "lg",
      body: `<div class="security-grid" style="grid-template-columns:1fr">${PILLARS.slice(0, 4)
        .map((p) => `<p><strong>${p.icon} ${p.title}</strong> — ${p.summary}</p>`)
        .join("")}</div><p class="card-sub">Puni pregled: stranica Sigurnost u izborniku.</p>`,
    });
  }

  function bindTrustStrip(container, api) {
    container?.querySelector("[data-security-open]")?.addEventListener("click", (e) => {
      e.preventDefault();
      if (api.pageUrl) location.href = api.pageUrl("pages/sigurnost.html");
      else openSecurityModal(api);
    });
  }

  function enhanceLoginHtml() {
    return `
      <p class="login-security-note card-sub">
        <strong>Demo prijava:</strong> OTP kod prikazuje se na stranici nakon klika.
        <strong>GDPR:</strong> podaci župljana povjerljivi.
        <a href="pages/sigurnost.html" id="login-security-link">Sigurnost i šifriranje baze</a> ·
        <button type="button" class="gdpr-inline-link" id="login-gdpr-privacy-btn">Privatnost</button>
      </p>`;
  }

  global.PastoralSecurity = {
    PILLARS,
    getSessionInfo,
    renderTrustStrip,
    mountSecurityPage,
    openSecurityModal,
    bindTrustStrip,
    enhanceLoginHtml,
  };
})(typeof window !== "undefined" ? window : global);
