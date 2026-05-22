/**
 * GDPR — zaštita osobnih podataka župljana (vjernika)
 */
(function (global) {
  const VERSION = "2025-1";
  const STAFF_KEY = "pastoral_gdpr_staff_v1";
  const BANNER_KEY = "pastoral_gdpr_banner_ok";

  const RIGHTS = [
    { id: "info", label: "Pravo na informiranost", text: "Vjernik zna tko obrađuje podatke, zašto i koliko dugo." },
    { id: "pristup", label: "Pristup i ispravak", text: "Zahtjev za uvid u karton ili ispravak netočnih podataka." },
    { id: "brisanje", label: "Brisanje / ograničenje", text: "U granicama kanonskog prava i pastoralne nužnosti." },
    { id: "prigovor", label: "Prigovor obradi", text: "Obrada samo u svrhu pastoralne službe, ne za marketing trećih strana." },
    { id: "prenos", label: "Prenosivost", text: "Izvadak u razumljivom formatu na zahtjev (produkcija)." },
  ];

  const PURPOSES = [
    "Vođenje matičnih knjiga i službenih evidencija župe",
    "Organizacija sakramenata (krštenje, pričest, krizma, vjenčanje, pogreb)",
    "Pastoralne posjete i komunikacija (uz privolu za kontakt)",
    "Financije župe (lukno, nakane) — bez dijeljenja s trećim stranama bez osnove",
    "Javne prijave s portala — pregled i odobrenje u uredu prije unosa u knjigu",
  ];

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function staffAccepted() {
    try {
      return localStorage.getItem(STAFF_KEY) === VERSION;
    } catch {
      return false;
    }
  }

  function setStaffAccepted() {
    localStorage.setItem(STAFF_KEY, VERSION);
  }

  function bannerDismissed() {
    try {
      return sessionStorage.getItem(BANNER_KEY) === "1";
    } catch {
      return false;
    }
  }

  function dismissBanner() {
    sessionStorage.setItem(BANNER_KEY, "1");
  }

  function renderStaffLoginBlock() {
    return `
      <div class="gdpr-login-block">
        <label class="gdpr-consent-label">
          <input type="checkbox" id="gdpr-staff-consent" required>
          <span>Potvrđujem da ću osobne podatke <strong>župljana</strong> koristiti isključivo u službi župe, čuvati povjerljivost i postupati prema <button type="button" class="gdpr-inline-link" id="gdpr-open-privacy">obavijesti o privatnosti</button>.</span>
        </label>
      </div>`;
  }

  function renderPublicConsentBlock(parishName) {
    const p = escapeHtml(parishName || "župa");
    return `
      <div class="gdpr-public-consent form-wide">
        <label class="gdpr-consent-label">
          <input type="checkbox" id="gdpr-public-consent" name="_gdpr_consent" required>
          <span>Suglasan/suglasna sam da župa <strong>${p}</strong> obrađuje moje osobne podatke iz ovog obrasca u svrhu pastoralne obrade prijave. Podaci se ne objavljuju javno. Više u <button type="button" class="gdpr-inline-link" id="gdpr-public-privacy">obavijesti za vjernike</button>.</span>
        </label>
        <p class="card-sub gdpr-mini-note">Obavezno polje (GDPR). Prijavu pregledava župni ured prije unosa u evidenciju.</p>
      </div>`;
  }

  function renderPublicPortalNotice() {
    return `
      <section class="card gdpr-public-banner fx-glass">
        <span class="gdpr-shield" aria-hidden="true">🛡</span>
        <div>
          <strong>Vaša privatnost</strong>
          <p class="card-sub" style="margin:4px 0 0">Obrasci služe samo pastoralnoj prijavi. Nemate pristup matičnim knjigama ni financijama župe.</p>
        </div>
      </section>`;
  }

  function privacyBodyHtml() {
    return `
      <div class="gdpr-privacy-doc">
        <p><strong>Voditelj obrade:</strong> župnik župe (crkvena pravna osoba u okviru Đakovačko-osječke nadbiskupije).</p>
        <p><strong>Pravna osnova:</strong> legitimni interes pastoralne službe (kanonsko pravo) i, gdje je potrebno, <em>privola</em> za kontakt (telefon, e-mail).</p>
        <h3>Svrhe obrade</h3>
        <ul>${PURPOSES.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>
        <h3>Prava župljana</h3>
        <ul>${RIGHTS.map((r) => `<li><strong>${escapeHtml(r.label)}</strong> — ${escapeHtml(r.text)}</li>`).join("")}</ul>
        <h3>Čuvanje</h3>
        <p>Matični i pastoralni podaci čuvaju se prema crkvenim propisima i razumnim rokovima; javne prijave koje nisu prihvaćene brišu se u produkciji nakon pregleda.</p>
        <h3>Demo aplikacija</h3>
        <p class="card-sub">Podaci u ovom pregledniku nisu zaštićeni kao na serveru. U produkciji: HTTPS, EU hosting, pristup po ulogama, audit log.</p>
        <p>Kontakt za pitanja privatnosti: župni ured (e-mail u postavkama župe).</p>
      </div>`;
  }

  function openPrivacyModal() {
    const body = privacyBodyHtml();
    if (global.PastoralModal?.openDetail) {
      global.PastoralModal.openDetail({
        title: "Obavijest o privatnosti — župljani",
        size: "lg",
        body,
      });
      return;
    }
    const w = window.open("", "_blank", "width=640,height=720");
    if (w) {
      w.document.write(`<!DOCTYPE html><html lang="hr"><head><meta charset="utf-8"><title>Privatnost</title></head><body style="font-family:Georgia,serif;padding:24px;max-width:560px">${body}</body></html>`);
      w.document.close();
    }
  }

  function bindPrivacyTriggers(root) {
    root?.querySelector("#gdpr-open-privacy")?.addEventListener("click", (e) => {
      e.preventDefault();
      openPrivacyModal();
    });
    root?.querySelector("#gdpr-public-privacy")?.addEventListener("click", (e) => {
      e.preventDefault();
      openPrivacyModal();
    });
  }

  function validatePublicConsent() {
    const el = document.getElementById("gdpr-public-consent");
    if (!el?.checked) {
      el?.focus();
      return false;
    }
    return true;
  }

  function validateStaffConsent() {
    const el = document.getElementById("gdpr-staff-consent");
    if (!el?.checked) {
      el?.focus();
      return false;
    }
    setStaffAccepted();
    return true;
  }

  function confirmBeforeExport(label, rowCount) {
    const n = rowCount ?? 0;
    const msg = `Izvoz „${label}” (${n} redaka) sadrži osobne podatke župljana.\n\nKoristite datoteku samo u župnom uredu. Ne šaljite nešifriranim kanalom. Nastaviti?`;
    if (global.PastoralCrudModals?.confirm) {
      return global.PastoralCrudModals.confirm(msg, { title: "GDPR — izvoz podataka" });
    }
    return Promise.resolve(confirm(msg));
  }

  function renderAdminBanner(api) {
    if (bannerDismissed()) return "";
    return `
      <div class="gdpr-admin-banner fx-glass" role="status" id="gdpr-admin-banner" data-no-stagger>
        <span class="gdpr-shield gdpr-shield--pulse" aria-hidden="true">🛡</span>
        <div class="gdpr-admin-banner-text">
          <strong>Osobni podaci župljana</strong> — povjerljivo. Izvoz i ispis samo za službenu svrhu.
          <a href="${api.pageUrl("pages/sigurnost.html")}#gdpr">Prava vjernika</a>
        </div>
        <button type="button" class="btn btn-ghost btn-sm" id="gdpr-banner-dismiss" aria-label="Zatvori">×</button>
      </div>`;
  }

  function mountAdminBanner(api) {
    const content = document.querySelector(".app-shell .main .content");
    if (!content || content.querySelector("#gdpr-admin-banner")) return;
    const wrap = document.createElement("div");
    wrap.innerHTML = renderAdminBanner(api);
    const banner = wrap.firstElementChild;
    if (!banner) return;
    content.insertBefore(banner, content.firstChild);
    banner.querySelector("#gdpr-banner-dismiss")?.addEventListener("click", () => {
      dismissBanner();
      banner.classList.add("gdpr-banner-out");
      setTimeout(() => banner.remove(), 280);
    });
  }

  function mountGdprOnSecurityPage(root, api) {
    const esc = api.escapeHtml;
    const block = document.createElement("section");
    block.className = "card wide";
    block.id = "gdpr";
    block.innerHTML = `
      <h2 class="section-title">GDPR — župljani (vjernici)</h2>
      <p class="card-sub">Osobni podaci u Pastoralu odnose se na župljane: obitelji, sakramenti, kontakti, prijave s portala. Obrada mora biti razmjerna, transparentna i zaštićena.</p>
      <div class="gdpr-rights-grid">
        ${RIGHTS.map(
          (r) => `<article class="gdpr-right-card fx-card-hover">
            <h3>${esc(r.label)}</h3>
            <p class="card-sub">${esc(r.text)}</p>
          </article>`
        ).join("")}
      </div>
      <h3 class="section-title" style="margin-top:20px">Obveze župnog ureda</h3>
      <ul class="gdpr-duty-list">
        <li>Pristup samo ovlaštenim osobama (uloga u sustavu)</li>
        <li>Javni portal odvojen — vjernik ne vidi tuđe kartone ni blagajnu</li>
        <li>Prije izvoza CSV/Excel — potvrda povjerljivosti</li>
        <li>Poruke vjernicima — bez automatskog slanja bez privole (predlošci za ručni odabir)</li>
        <li>Pravo na ispravak: uređivanje kartona obitelji / brisanje pogrešnih prijava</li>
      </ul>
      <button type="button" class="btn btn-primary btn-sm" id="gdpr-full-privacy-btn">Puna obavijest o privatnosti</button>
      <button type="button" class="btn btn-ghost btn-sm" id="gdpr-reset-staff">Poništi potvrdu na prijavi (demo)</button>`;
    root.appendChild(block);
    block.querySelector("#gdpr-full-privacy-btn")?.addEventListener("click", openPrivacyModal);
    block.querySelector("#gdpr-reset-staff")?.addEventListener("click", () => {
      localStorage.removeItem(STAFF_KEY);
      api.showToast("Pri sljedećoj prijavi tražit će se ponovna potvrda");
    });
  }

  function renderDashboardGdprCard(api) {
    return `
      <section class="card wide gdpr-dash-card fx-glass" data-no-stagger>
        <div class="gdpr-dash-inner">
          <span class="gdpr-shield gdpr-shield--pulse" aria-hidden="true">🛡</span>
          <div>
            <h2 class="section-title" style="margin:0">Privatnost župljana</h2>
            <p class="card-sub" style="margin:4px 0 0">Podaci vjernika su povjerljivi. Portal je odvojen; izvoz zahtijeva potvrdu.</p>
          </div>
          <a href="${api.pageUrl("pages/sigurnost.html")}#gdpr" class="btn btn-primary btn-sm">GDPR u uredu</a>
        </div>
      </section>`;
  }

  global.PastoralGdpr = {
    VERSION,
    RIGHTS,
    PURPOSES,
    staffAccepted,
    setStaffAccepted,
    renderStaffLoginBlock,
    renderPublicConsentBlock,
    renderPublicPortalNotice,
    privacyBodyHtml,
    openPrivacyModal,
    bindPrivacyTriggers,
    validatePublicConsent,
    validateStaffConsent,
    confirmBeforeExport,
    mountAdminBanner,
    mountGdprOnSecurityPage,
    renderDashboardGdprCard,
  };
})(typeof window !== "undefined" ? window : global);
