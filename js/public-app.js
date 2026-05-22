/**
 * Javne stranice obrazaca (bez prijave)
 */
document.addEventListener("DOMContentLoaded", () => {
  const P = window.PastoralParish;
  const PF = window.PastoralPublicForms;
  const root = document.getElementById("public-root");
  if (!P || !PF) {
    if (root) {
      root.innerHTML = `
        <section class="card public-error-card" style="max-width:520px;margin:2rem auto">
          <h2>Skripte nisu učitane</h2>
          <p class="card-sub">Koristite mapu <strong>pastoral-zupa/public/</strong> (ne <code>pages/public</code>).</p>
          <pre style="background:var(--bg);padding:12px;border-radius:8px">cd pastoral-zupa\nnpx serve -l 3340</pre>
          <p><a href="http://localhost:3340/public/index.html">http://localhost:3340/public/index.html</a></p>
        </section>`;
    }
    return;
  }

  P.applyTheme();
  if (window.PastoralTheme) window.PastoralTheme.initThemePicker({ fixed: true });
  window.PastoralData?.ensureSeed();

  const formType = document.body.dataset.form;
  const settings = P.loadSettings();

  if (document.body.dataset.page === "public-index" && root) {
    root.innerHTML = `
      <header class="public-header">
        ${P.renderLogoHtml(true)}
        <h1>${PF.escapeHtml(settings.name)}</h1>
        <p>Online prijave za sakramente i pastoralne usluge</p>
      </header>
      ${window.PastoralGdpr ? window.PastoralGdpr.renderPublicPortalNotice() : ""}
      <div class="public-form-grid">
        <a class="card public-form-card fx-card-hover" href="prijava-krizma.html"><span class="public-form-ico">✠</span><h2>Krizma</h2><p>Prijava za svetu Potvrdu</p></a>
        <a class="card public-form-card fx-card-hover" href="prijava-krsenje.html"><span class="public-form-ico">💧</span><h2>Krštenje</h2><p>Prijava djeteta</p></a>
        <a class="card public-form-card fx-card-hover" href="prijava-pricest.html"><span class="public-form-ico">✞</span><h2>Prva pričest</h2><p>Prijava prvopričesnika</p></a>
        <a class="card public-form-card fx-card-hover" href="prijava-ukop.html"><span class="public-form-ico">✝</span><h2>Ukop</h2><p>Dogovor pogreba</p></a>
      </div>
      <p class="public-footer card-sub"><button type="button" class="gdpr-inline-link" id="gdpr-public-index-privacy">Obavijest o privatnosti</button> · <a href="../login.html">Prijava za župni ured</a></p>`;
    document.getElementById("gdpr-public-index-privacy")?.addEventListener("click", () => window.PastoralGdpr?.openPrivacyModal());
    return;
  }

  const def = PF.FORMS[formType];
  if (!def || !root) return;

  root.innerHTML = PF.renderFormHtml(def, settings);
  window.PastoralGdpr?.bindPrivacyTriggers(root);

  document.getElementById("public-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    if (window.PastoralGdpr && !window.PastoralGdpr.validatePublicConsent()) {
      alert("Molimo potvrdite suglasnost za obradu osobnih podataka (GDPR).");
      return;
    }
    const payload = {};
    def.fields.forEach((f) => {
      const el = document.getElementById(`f-${f.id}`);
      if (el) payload[f.id] = el.value.trim();
    });
    PF.addSubmission(formType, payload);
    root.innerHTML = `
      <section class="card public-success fx-glass">
        <p class="payment-success-icon">✓</p>
        <h2>Prijava zaprimljena</h2>
        <p>Hvala. Župni ured će pregledati podatke i kontaktirati vas.</p>
        <a href="index.html" class="btn btn-primary">Natrag na obrasce</a>
      </section>`;
  });
});
