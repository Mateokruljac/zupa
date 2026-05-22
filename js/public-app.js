/**
 * Javne stranice obrazaca (bez prijave)
 */
document.addEventListener("DOMContentLoaded", () => {
  const P = window.PastoralParish;
  const PF = window.PastoralPublicForms;
  if (!P || !PF) return;

  P.applyTheme();
  if (window.PastoralTheme) window.PastoralTheme.initThemePicker({ fixed: true });
  window.PastoralData?.ensureSeed();

  const formType = document.body.dataset.form;
  const root = document.getElementById("public-root");
  const settings = P.loadSettings();

  if (document.body.dataset.page === "public-index" && root) {
    root.innerHTML = `
      <header class="public-header">
        ${P.renderLogoHtml(true)}
        <h1>${PF.escapeHtml(settings.name)}</h1>
        <p>Online prijave za sakramente i pastoralne usluge</p>
      </header>
      <div class="public-form-grid">
        <a class="card public-form-card" href="prijava-krizma.html"><span class="public-form-ico">✠</span><h2>Krizma</h2><p>Prijava za svetu Potvrdu</p></a>
        <a class="card public-form-card" href="prijava-krsenje.html"><span class="public-form-ico">💧</span><h2>Krštenje</h2><p>Prijava djeteta</p></a>
        <a class="card public-form-card" href="prijava-pricest.html"><span class="public-form-ico">✞</span><h2>Prva pričest</h2><p>Prijava prvopričesnika</p></a>
        <a class="card public-form-card" href="prijava-ukop.html"><span class="public-form-ico">✝</span><h2>Ukop</h2><p>Dogovor pogreba</p></a>
      </div>
      <p class="public-footer card-sub"><a href="../login.html">Prijava za župni ured</a></p>`;
    return;
  }

  const def = PF.FORMS[formType];
  if (!def || !root) return;

  root.innerHTML = PF.renderFormHtml(def, settings);

  document.getElementById("public-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const payload = {};
    def.fields.forEach((f) => {
      const el = document.getElementById(`f-${f.id}`);
      if (el) payload[f.id] = el.value.trim();
    });
    PF.addSubmission(formType, payload);
    root.innerHTML = `
      <section class="card public-success">
        <p class="payment-success-icon">✓</p>
        <h2>Prijava zaprimljena</h2>
        <p>Hvala. Župni ured će pregledati podatke i kontaktirati vas.</p>
        <a href="index.html" class="btn btn-primary">Natrag na obrasce</a>
      </section>`;
  });
});
