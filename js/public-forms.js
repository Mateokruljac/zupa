/**
 * Javni obrasci — prijave vjernika (localStorage)
 */
(function (global) {
  const FORMS = {
    krizma: {
      id: "krizma",
      title: "Prijava za svetu Potvrdu (krizmu)",
      intro: "Ispunite obrazac za upis krizmanika. Župni ured će vas kontaktirati.",
      fields: [
        { id: "ime", label: "Ime", type: "text", required: true },
        { id: "prezime", label: "Prezime", type: "text", required: true },
        { id: "datum_rodjenja", label: "Datum rođenja", type: "date", required: true },
        { id: "skola", label: "Škola", type: "text", required: true },
        { id: "razred", label: "Razred", type: "text", required: true },
        { id: "roditelji", label: "Roditelji / skrbnici", type: "text", required: true },
        { id: "datum_krstenja", label: "Datum krštenja", type: "date" },
        { id: "kum", label: "Kum/ka za potvrdu", type: "text" },
        { id: "telefon", label: "Telefon", type: "tel", required: true },
        { id: "email", label: "E-mail", type: "email" },
        { id: "napomena", label: "Napomena", type: "textarea" },
      ],
    },
    krstenje: {
      id: "krstenje",
      title: "Prijava za krštenje",
      intro: "Prijava djeteta za sakrament krštenja. Molimo popunite što je moguće točnije.",
      fields: [
        { id: "ime_djeteta", label: "Ime i prezime djeteta", type: "text", required: true },
        { id: "datum_rodjenja", label: "Datum rođenja djeteta", type: "date", required: true },
        { id: "mjesto_rodjenja", label: "Mjesto rođenja", type: "text" },
        { id: "roditelji", label: "Roditelji", type: "text", required: true },
        { id: "kumovi", label: "Kum(ovi) — ime i prezime", type: "text" },
        { id: "adresa", label: "Adresa obitelji", type: "text" },
        { id: "telefon", label: "Telefon", type: "tel", required: true },
        { id: "email", label: "E-mail", type: "email" },
        { id: "zeljeni_termin", label: "Željeni termin (ako znate)", type: "date" },
        { id: "napomena", label: "Napomena", type: "textarea" },
      ],
    },
    pricest: {
      id: "pricest",
      title: "Prijava za prvu svetu Pričest",
      intro: "Prijava prvopričesnika. Katehetski program dogovara se s župnim uredom.",
      fields: [
        { id: "ime_djeteta", label: "Ime i prezime djeteta", type: "text", required: true },
        { id: "datum_rodjenja", label: "Datum rođenja", type: "date", required: true },
        { id: "skola", label: "Škola", type: "text", required: true },
        { id: "razred", label: "Razred", type: "text", required: true },
        { id: "roditelji", label: "Roditelji", type: "text", required: true },
        { id: "datum_krstenja", label: "Datum krštenja", type: "date" },
        { id: "telefon", label: "Telefon", type: "tel", required: true },
        { id: "email", label: "E-mail", type: "email" },
        { id: "napomena", label: "Napomena", type: "textarea" },
      ],
    },
    ukop: {
      id: "ukop",
      title: "Prijava za ukop (pogreb)",
      intro: "Obrazac za dogovor pogreba i ukopa. U hitnim slučajevima nazovite župni ured.",
      fields: [
        { id: "pokojnik", label: "Ime i prezime pokojnika", type: "text", required: true },
        { id: "datum_smrti", label: "Datum smrti", type: "date", required: true },
        { id: "kontakt", label: "Kontakt osoba (ime)", type: "text", required: true },
        { id: "telefon", label: "Telefon", type: "tel", required: true },
        { id: "email", label: "E-mail", type: "email" },
        { id: "groblje", label: "Groblje / mjesto ukopa", type: "text" },
        { id: "zeljeni_datum", label: "Željeni datum pogreba", type: "date" },
        { id: "napomena", label: "Napomena (liturgija, posebne želje)", type: "textarea" },
      ],
    },
  };

  const TYPE_LABELS = {
    krizma: "Krizma",
    krstenje: "Krštenje",
    pricest: "Prva pričest",
    ukop: "Ukop / pogreb",
  };

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function ensurePublicSubmissions(data) {
    if (!Array.isArray(data.publicSubmissions)) data.publicSubmissions = [];
    return data;
  }

  function addSubmission(type, payload) {
    const data = global.PastoralData.load();
    ensurePublicSubmissions(data);
    const row = {
      id: `pub_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      type,
      status: "nova",
      submittedAt: new Date().toISOString(),
      data: payload,
    };
    data.publicSubmissions.unshift(row);
    global.PastoralData.save(data);
    return row;
  }

  function renderFormHtml(formDef, parish) {
    const logo =
      global.PastoralParish && typeof global.PastoralParish.renderLogoHtml === "function"
        ? global.PastoralParish.renderLogoHtml(true)
        : "";
    const fields = formDef.fields
      .map((f) => {
        const req = f.required ? " required" : "";
        if (f.type === "textarea") {
          return `<div class="form-group form-wide"><label for="f-${f.id}">${escapeHtml(f.label)}</label><textarea id="f-${f.id}" name="${f.id}" rows="3"${req}></textarea></div>`;
        }
        return `<div class="form-group${f.type === "textarea" ? " form-wide" : ""}"><label for="f-${f.id}">${escapeHtml(f.label)}</label><input type="${f.type || "text"}" id="f-${f.id}" name="${f.id}"${req} /></div>`;
      })
      .join("");
    return `
      <header class="public-header">
        <a href="index.html" class="public-back">← Svi obrasci</a>
        <div class="public-logo">${logo}</div>
        <h1>${escapeHtml(formDef.title)}</h1>
        <p>${escapeHtml(formDef.intro)}</p>
        <p class="card-sub">${escapeHtml(parish.name || "")} · ${escapeHtml(parish.city || "")}</p>
      </header>
      <form id="public-form" class="public-form card">
        ${fields}
        ${global.PastoralGdpr ? global.PastoralGdpr.renderPublicConsentBlock(parish.name) : ""}
        <button type="submit" class="btn btn-primary fx-btn-shine">Pošalji prijavu</button>
      </form>
      <p class="public-footer card-sub">Hitno? <a href="tel:${escapeHtml((parish.phone || "").replace(/\s/g, ""))}">${escapeHtml(parish.phone || "župni ured")}</a></p>`;
  }

  global.PastoralPublicForms = {
    FORMS,
    TYPE_LABELS,
    addSubmission,
    ensurePublicSubmissions,
    renderFormHtml,
    escapeHtml,
  };
})(typeof window !== "undefined" ? window : global);
