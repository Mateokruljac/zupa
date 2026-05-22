/**
 * Predlošci dokumenata + povezivanje Excel/CSV + ispis
 */
(function (global) {
  const BINDINGS_KEY = "pastoral_doc_bindings";

  const TEMPLATES = [
    {
      id: "pristupnica_krizma",
      name: "Pristupnica za sv. Potvrdu",
      category: "krizma",
      fields: ["ime_prezime", "datum_rodjenja", "datum_krstenja", "kum", "datum_potvrde", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h1 style="text-align:center;font-family:Georgia,serif">PRISTUPNICA ZA SAKRAMENT SVETE POTVRDE</h1>
        <p style="margin-top:2em">Ja, don <strong>{{zupnik}}</strong>, župnik župe <strong>{{zupa}}</strong>, potvrđujem da je:</p>
        <p><strong>Ime i prezime:</strong> {{ime_prezime}}</p>
        <p><strong>Datum rođenja:</strong> {{datum_rodjenja}}</p>
        <p><strong>Datum krštenja:</strong> {{datum_krstenja}}</p>
        <p><strong>Kum/ka za potvrdu:</strong> {{kum}}</p>
        <p style="margin-top:2em">Datum potvrde: <strong>{{datum_potvrde}}</strong></p>
        <p style="margin-top:3em">Potpis župnika: _________________________</p>
        <p>Mjesto i datum: {{zupa}}, {{danas}}</p>
      </div>`,
    },
    {
      id: "potvrda_krsenja",
      name: "Potvrda o krštenju (izvadak)",
      category: "krsenje",
      fields: ["ime_djeteta", "datum_krstenja", "roditelji", "kumovi", "maticni_broj", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">IZVADAK IZ MATIČNE KNJIGE KRŠTENIH</h2>
        <p>Župa: <strong>{{zupa}}</strong></p>
        <p>Dijete: <strong>{{ime_djeteta}}</strong></p>
        <p>Kršteno: <strong>{{datum_krstenja}}</strong></p>
        <p>Roditelji: {{roditelji}}</p>
        <p>Kum(ovi): {{kumovi}}</p>
        <p>Matični broj: {{maticni_broj}}</p>
        <p style="margin-top:2em">Izdano u {{zupa}}, {{danas}}.</p>
        <p>Župnik: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "raspored_nakana",
      name: "Raspored misnih nakana (tjedan)",
      category: "nakane",
      fields: ["tjedan_od", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">RASPORED MOLITVENIH NAKANA</h2>
        <p>Župa {{zupa}} · tjedan od {{tjedan_od}}</p>
        <table border="1" cellpadding="8" style="width:100%;border-collapse:collapse;margin-top:1em">
          <thead><tr><th>Datum</th><th>Misa</th><th>Namjera</th><th>Naručitelj</th><th>Stipendij</th></tr></thead>
          <tbody>{{tablica_nakana}}</tbody>
        </table>
      </div>`,
    },
    {
      id: "zapisnik_zpv",
      name: "Zapisnik sastanka ŽPV",
      category: "ured",
      fields: ["datum_sastanka", "prisutni", "dnevni_red", "zakljucci", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2>ZAPISNIK ŽUPNOG PASTORALNOG VIJEĆA</h2>
        <p>Župa: {{zupa}} · Datum: {{datum_sastanka}}</p>
        <p><strong>Prisutni:</strong> {{prisutni}}</p>
        <p><strong>Dnevni red:</strong> {{dnevni_red}}</p>
        <p><strong>Zaključci:</strong> {{zakljucci}}</p>
        <p style="margin-top:2em">Potpis župnika: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "izvjestaj_dekanska_vizitacija",
      name: "Izvješće o dekanskoj vizitaciji",
      category: "ured",
      fields: ["godina", "stanje_zupe", "preporuke", "zupnik", "zupa", "danas"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">IZVJEŠĆE O DEKANSKOJ VIZITACIJI</h2>
        <p>Župa: <strong>{{zupa}}</strong> · Godina: {{godina}}</p>
        <p><strong>Stanje župe:</strong></p><p>{{stanje_zupe}}</p>
        <p><strong>Preporuke dekana:</strong></p><p>{{preporuke}}</p>
        <p style="margin-top:2em">{{zupa}}, {{danas}}</p>
        <p>Župnik: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "zapisnik_kanonska_vizitacija",
      name: "Zapisnik kanonske vizitacije",
      category: "ured",
      fields: ["datum", "prisutni", "dnevni_red", "zakljucci", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">ZAPISNIK KANONSKE VIZITACIJE</h2>
        <p>Župa: {{zupa}} · Datum: {{datum}}</p>
        <p><strong>Prisutni:</strong> {{prisutni}}</p>
        <p><strong>Tijek vizitacije:</strong></p><p>{{dnevni_red}}</p>
        <p><strong>Zaključci i nalozi:</strong></p><p>{{zakljucci}}</p>
        <p style="margin-top:2em">Potpis župnika: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "pregled_zupnog_ureda",
      name: "Pregled župnog ureda",
      category: "ured",
      fields: ["godina", "zupnik", "zupa", "danas"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">PREGLED ŽUPNOG UREDA</h2>
        <p>Župa: {{zupa}} · {{godina}}</p>
        <ul style="line-height:1.8">
          <li>Matične knjige — evidencija i arhiv</li>
          <li>Obiteljski kartoni i pastoralne bilješke</li>
          <li>Blagajna (plavi/crveni dnevnik) i ŽEV izvješća</li>
          <li>ŽPV / ŽEV — zapisnici i plan</li>
          <li>Javni portal i zaštita podataka (GDPR)</li>
        </ul>
        <p style="margin-top:2em">Potvrđuje: {{zupnik}}, {{danas}}</p>
      </div>`,
    },
    {
      id: "program_zupne_kateheze",
      name: "Program župne kateheze",
      category: "pastoral",
      fields: ["godina", "program_sadrzaj", "kateheta", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">PROGRAM ŽUPNE KATEHEZE</h2>
        <p>Župa: {{zupa}} · Školska godina / godina: {{godina}}</p>
        <p><strong>Kateheta:</strong> {{kateheta}}</p>
        <p><strong>Sadržaj:</strong></p><p>{{program_sadrzaj}}</p>
        <p style="margin-top:2em">Župnik: {{zupnik}} · {{danas}}</p>
      </div>`,
    },
    {
      id: "pastoralni_plan_godisnji",
      name: "Godišnji pastoralni plan",
      category: "pastoral",
      fields: ["godina", "program_sadrzaj", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">GODIŠNJI PASTORALNI PLAN ŽUPE</h2>
        <p>Župa: {{zupa}} · {{godina}}</p>
        <p>{{program_sadrzaj}}</p>
        <p style="margin-top:2em">Usvojio ŽPV · Potpis župnika: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "evidencija_vjeronauk_skola",
      name: "Evidencija vjeronauka u školi",
      category: "pastoral",
      fields: ["skola", "razred", "broj_ucenika", "kateheta", "godina", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">EVIDENCIJA KATOLIČKOG VJERONAUKA</h2>
        <p>Župa: {{zupa}} · Škola: {{skola}} · Razred: {{razred}}</p>
        <p>Broj polaznika: {{broj_ucenika}} · Kateheta: {{kateheta}} · Godina: {{godina}}</p>
        <p style="margin-top:2em">Napomena: sporazum s ustanovom čuva se u arhivu župe.</p>
      </div>`,
    },
    {
      id: "potvrda_vjencanja",
      name: "Potvrda o vjenčanju",
      category: "vjenčanje",
      fields: ["mladenci", "datum_vjencanja", "svjedoci", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">POTVRDA O VJENČANJU</h2>
        <p>U župi {{zupa}} vjenčani su: <strong>{{mladenci}}</strong></p>
        <p>Datum obreda: {{datum_vjencanja}}</p>
        <p>Svjedoci: {{svjedoci}}</p>
        <p>Obred služio: {{zupnik}}</p>
        <p>Izdano: {{danas}}</p>
      </div>`,
    },
    {
      id: "potvrda_pricest",
      name: "Potvrda o prvoj sv. Pričesti",
      category: "prva-pricest",
      fields: ["ime_prezime", "datum_pricesti", "skupina", "roditelji", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">POTVRDA O PRVOJ SVETOJ PRIČESTI</h2>
        <p>Župa: <strong>{{zupa}}</strong></p>
        <p>Prvopričesnik/ica: <strong>{{ime_prezime}}</strong></p>
        <p>Skupina / godina: {{skupina}}</p>
        <p>Roditelji: {{roditelji}}</p>
        <p>Datum prve pričesti: <strong>{{datum_pricesti}}</strong></p>
        <p style="margin-top:2em">Izdano u {{zupa}}, {{danas}}.</p>
        <p>Župnik: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "potvrda_pogreba",
      name: "Potvrda o pogrebu / ukopu",
      category: "pogreb",
      fields: ["pokojnik", "datum_smrti", "datum_pogreba", "groblje", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">POTVRDA O KRŠTENJU I POGREBU</h2>
        <p>Župa: <strong>{{zupa}}</strong></p>
        <p>Pokojnik/ica: <strong>{{pokojnik}}</strong></p>
        <p>Datum smrti: {{datum_smrti}}</p>
        <p>Datum pogreba: <strong>{{datum_pogreba}}</strong></p>
        <p>Groblje: {{groblje}}</p>
        <p style="margin-top:2em">Izdano u {{zupa}}, {{danas}}.</p>
        <p>Župnik: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "potvrda_lukno",
      name: "Potvrda o uplati župnog lukna",
      category: "lukno",
      fields: ["obitelj", "adresa", "godina", "iznos", "datum_uplate", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">POTVRDA O UPLATI ŽUPNOG LUKNA</h2>
        <p>Župa: <strong>{{zupa}}</strong></p>
        <p>Obitelj: <strong>{{obitelj}}</strong></p>
        <p>Adresa: {{adresa}}</p>
        <p>Godina: <strong>{{godina}}</strong></p>
        <p>Iznos: <strong>{{iznos}} €</strong></p>
        <p>Datum uplate: {{datum_uplate}}</p>
        <p style="margin-top:2em">Potvrđujemo primitak navedenog iznosa za župno lukno.</p>
        <p style="margin-top:2em">{{zupa}}, {{danas}}</p>
        <p>Župnik: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "potvrda_uplate",
      name: "Potvrda o primitku uplate (opća)",
      category: "financije",
      fields: ["platitelj", "svrha", "iznos", "datum_uplate", "broj_racuna", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">POTVRDA O PRIMITKU UPLATE</h2>
        <p>Župa: <strong>{{zupa}}</strong></p>
        <p>Primili smo od: <strong>{{platitelj}}</strong></p>
        <p>Svrha uplate: {{svrha}}</p>
        <p>Iznos: <strong>{{iznos}} €</strong></p>
        <p>Datum: {{datum_uplate}}</p>
        <p>Veza na račun: {{broj_racuna}}</p>
        <p style="margin-top:2em">{{zupa}}, {{danas}}</p>
        <p>Župnik / blagajnik: {{zupnik}}</p>
      </div>`,
    },
    {
      id: "potvrda_nakane",
      name: "Potvrda o misnoj nakani",
      category: "nakane",
      fields: ["namjera", "datum_mise", "vrijeme_mise", "narucitelj", "stipendij", "zupnik", "zupa"],
      body: `<div class="print-doc">
        <h2 style="text-align:center">POTVRDA O MOLITVENOM NAKANU</h2>
        <p>Župa: <strong>{{zupa}}</strong></p>
        <p>Namjera: <strong>{{namjera}}</strong></p>
        <p>Misa: {{datum_mise}} u {{vrijeme_mise}}</p>
        <p>Naručitelj: {{narucitelj}}</p>
        <p>Stipendij: {{stipendij}} €</p>
        <p style="margin-top:2em">Izdano: {{danas}}</p>
        <p>{{zupnik}}</p>
      </div>`,
    },
  ];

  function getCertificateTemplates() {
    return TEMPLATES.filter((t) => t.id.startsWith("potvrda_") || t.id === "pristupnica_krizma");
  }

  function loadBindings() {
    try {
      return JSON.parse(localStorage.getItem(BINDINGS_KEY) || "[]");
    } catch (_) {
      return [];
    }
  }

  function saveBindings(list) {
    localStorage.setItem(BINDINGS_KEY, JSON.stringify(list));
  }

  function getTemplate(id) {
    return TEMPLATES.find((t) => t.id === id);
  }

  function mergeTemplate(html, values) {
    let out = html;
    Object.entries(values).forEach(([k, v]) => {
      out = out.split(`{{${k}}}`).join(String(v ?? ""));
    });
    return out.replace(/\{\{[^}]+\}\}/g, "—");
  }

  function mapRowToFields(row, mapping, parishDefaults) {
    const values = { ...parishDefaults };
    Object.entries(mapping || {}).forEach(([placeholder, column]) => {
      if (column && row[column] !== undefined) values[placeholder] = row[column];
    });
    return values;
  }

  function printHtml(html, title) {
    const w = window.open("", "_blank");
    if (!w) {
      alert("Omogućite skočne prozore za ispis.");
      return;
    }
    w.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>${title || "Ispis"}</title>
      <style>body{font-family:Georgia,serif;padding:40px;max-width:800px;margin:0 auto} @media print{.no-print{display:none}}</style></head><body>${html}
      <p class="no-print" style="margin-top:2em"><button onclick="window.print()">Ispis</button></p></body></html>`);
    w.document.close();
  }

  function renderDocumentsPageHtml(parish) {
    const bindings = loadBindings();
    return `
      <div class="docs-layout">
        <section class="card">
          <h2 class="section-title">Predlošci dokumenata</h2>
          <p class="card-sub">Odaberite predložak, povežite Excel/CSV datoteku, mapirajte stupce i ispišite.</p>
          <div class="form-group">
            <label>Predložak</label>
            <select id="doc-template-select">${TEMPLATES.map((t) => `<option value="${t.id}">${t.name} (${t.category})</option>`).join("")}</select>
          </div>
          <div id="doc-template-fields" class="doc-fields-list"></div>
        </section>
        <section class="card">
          <h2 class="section-title">Excel / CSV datoteka</h2>
          <input type="file" id="doc-file-upload" accept=".csv,.xlsx,.xls" />
          <p class="card-sub" id="doc-file-status">Nema učitane datoteke za ovaj predložak.</p>
          <div id="doc-mapping-area"></div>
          <button type="button" class="btn btn-primary" id="doc-save-binding">Spremi povezivanje</button>
        </section>
        <section class="card">
          <h2 class="section-title">Pregled i ispis</h2>
          <label>Red za ispis (iz Excela)</label>
          <select id="doc-row-select"><option value="0">— učitaj datoteku —</option></select>
          <div class="quick-actions" style="margin:12px 0">
            <button type="button" class="btn btn-primary" id="doc-preview-btn">Pregled</button>
            <button type="button" class="btn btn-secondary" id="doc-print-btn">🖨 Ispis</button>
          </div>
          <div id="doc-preview-box" class="doc-preview-box"></div>
        </section>
      </div>
      <section class="card" style="margin-top:20px">
        <h2 class="section-title">Spremljena povezivanja</h2>
        ${bindings.length
          ? `<ul class="doc-bindings-list">${bindings
              .map(
                (b) => `<li><strong>${b.templateName}</strong> — ${b.fileName} (${b.rowCount} redova)
                <button type="button" class="btn btn-ghost btn-sm" data-del-binding="${b.id}">Ukloni</button></li>`
              )
              .join("")}</ul>`
          : '<p class="empty-state">Još nema spremljenih povezivanja.</p>'}
      </section>`;
  }

  global.PastoralDocuments = {
    TEMPLATES,
    BINDINGS_KEY,
    loadBindings,
    saveBindings,
    getTemplate,
    getCertificateTemplates,
    mergeTemplate,
    mapRowToFields,
    printHtml,
    renderDocumentsPageHtml,
  };
})(typeof window !== "undefined" ? window : global);
