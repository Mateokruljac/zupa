/**
 * Administrativni paket župe — pravilnici, uredbe, obrasci, evidencije (HBK / župni ured)
 */
(function (global) {
  const STATUS_KEY = "pastoral_admin_doc_status";

  const SECTIONS = [
    { id: "pravilnici", label: "Pravilnici i uredbe", short: "1" },
    { id: "obrasci", label: "Službeni obrasci", short: "2" },
    { id: "evidencije", label: "Evidencije i knjige", short: "3" },
    { id: "financije", label: "Financijsko upravljanje", short: "4" },
    { id: "pastoral", label: "Pastoral i kateheza", short: "5" },
    { id: "pravno", label: "Pravni i državnopravni", short: "6" },
    { id: "dodatno", label: "Planovi i dodatno", short: "+" },
  ];

  /** @type {Array<object>} */
  const CATALOG = [
    /* 1 — Pravilnici i uredbe */
    {
      id: "pravilnik_zupni_ured",
      section: "pravilnici",
      title: "Pravilnik o radu župnog ureda i zaposlenika",
      ref: "HBK, str. 16",
      kind: "Pravilnik",
      desc: "Unutarnje procedure, odgovornosti župnika, vikara, upravitelja i kateheta.",
      link: "pages/poruke.html",
      templateId: null,
    },
    {
      id: "pravilnik_matica",
      section: "pravilnici",
      title: "Pravilnik o crkvenim maticama i drugim uredskim knjigama (2002.)",
      ref: "HBK, str. 8",
      kind: "Pravilnik",
      desc: "Vođenje knjiga krštenih, vjenčanih, umrlih, krizmanika; izvadci i arhiviranje.",
      link: "pages/maticne-knjige.html",
    },
    {
      id: "uredba_arhivi",
      section: "pravilnici",
      title: "Uredbe o crkvenim arhivima i muzejskim zbirkama (2002.)",
      ref: "HBK, str. 9",
      kind: "Uredba",
      desc: "Čuvanje, povrat knjiga u župu, pristup arhivskim jedinicama.",
      link: "pages/maticne-knjige.html",
    },
    {
      id: "uredba_admin_poslovi",
      section: "pravilnici",
      title: "Uredbe o administrativnim poslovima i vođenju župe",
      ref: "HBK",
      kind: "Uredba",
      desc: "Organizacija ureda, vijeća, izvještavanje biskupiji.",
      link: "pages/vijeca.html",
    },
    {
      id: "dekret_ustanovljenje",
      section: "pravilnici",
      title: "Dekret o ustanovljenju župe / pastoralnom području",
      ref: "Biskupija",
      kind: "Dekret",
      desc: "Teritorij, sjedište, prava i dužnosti župnika.",
      link: "pages/postavke.html",
    },

    /* 2 — Obrasci */
    {
      id: "izvjestaj_dekanska",
      section: "obrasci",
      title: "Izvješće o dekanskoj vizitaciji",
      ref: "HBK, str. 9 (2001.)",
      kind: "Izvještaj",
      desc: "Pregled stanja župe za dekana i biskupa.",
      templateId: "izvjestaj_dekanska_vizitacija",
    },
    {
      id: "zapisnik_kanonska",
      section: "obrasci",
      title: "Zapisnik kanonske vizitacije",
      ref: "HBK, str. 9 (2001.)",
      kind: "Zapisnik",
      desc: "Službeni zapisnik tijekom kanonske vizitacije župe.",
      templateId: "zapisnik_kanonska_vizitacija",
    },
    {
      id: "popis_imovine",
      section: "obrasci",
      title: "Župna imovina — evidencija i popis vlasništva",
      ref: "Župni ured",
      kind: "Popis",
      desc: "Crkve, stanovi, dvorane, zemljišta u vlasništvu župe.",
      anchor: "imovina",
    },
    {
      id: "ekonomski_izvjestaj",
      section: "obrasci",
      title: "Ekonomsko poslovanje — financijski izvještaji",
      ref: "HBK, str. 8–9 (2000.–2001.)",
      kind: "Izvještaj",
      desc: "Obračunski i godišnji financijski list, plavi/crveni dnevnik.",
      link: "pages/financijska-izvjestaja.html",
    },
    {
      id: "pregled_ureda",
      section: "obrasci",
      title: "Pregled župnog ureda — administrativne funkcije",
      ref: "Župni ured",
      kind: "Pregled",
      desc: "Checklist ureda, uloge, sigurnost podataka.",
      templateId: "pregled_zupnog_ureda",
      link: "pages/sigurnost.html",
    },
    {
      id: "obrasci_pastoral",
      section: "obrasci",
      title: "Obrasci za pastoralne i katehetske aktivnosti",
      ref: "HBK, str. 8",
      kind: "Obrazac",
      desc: "Pristupnice, programi skupina, zapisnici ŽPV.",
      link: "pages/formulari.html",
    },
    {
      id: "katalog_zupni_ured",
      section: "obrasci",
      title: "Katalog službenih formulara (krsni, vjenčani, smrtni list…)",
      ref: "župni-ured.com.hr",
      kind: "Katalog",
      desc: "18+ formulara za ispis s učitavanjem iz matice.",
      link: "pages/formulari.html",
    },

    /* 3 — Evidencije */
    {
      id: "ev_matica_krsenja",
      section: "evidencije",
      title: "Matična knjiga krštenih (rođenih)",
      ref: "Pravilnik HBK",
      kind: "Knjiga",
      desc: "Digitalna evidencija usklađena s knjigom; izvadci.",
      link: "pages/krsenja.html",
    },
    {
      id: "ev_matica_vjencanja",
      section: "evidencije",
      title: "Matična knjiga vjenčanih",
      ref: "Pravilnik HBK",
      kind: "Knjiga",
      link: "pages/vjencanja.html",
    },
    {
      id: "ev_matica_umrli",
      section: "evidencije",
      title: "Matična knjiga umrlih",
      ref: "Pravilnik HBK",
      kind: "Knjiga",
      link: "pages/pogrebi.html",
    },
    {
      id: "ev_matica_krizma",
      section: "evidencije",
      title: "Knjiga krizmanika / potvrđenih",
      ref: "Pravilnik HBK",
      kind: "Knjiga",
      link: "pages/krizma.html",
    },
    {
      id: "ev_pregled_knjiga",
      section: "evidencije",
      title: "Pregled svih matičnih knjiga u župi",
      ref: "Kan. 535",
      kind: "Pregled",
      link: "pages/maticne-knjige.html",
    },
    {
      id: "ev_obitelji",
      section: "evidencije",
      title: "Obiteljski listovi i župni karton",
      ref: "Župni ured",
      kind: "Evidencija",
      desc: "Tabovi: muž/žena, djeca, rođaci, lukno.",
      link: "pages/obitelji.html",
    },
    {
      id: "ev_imovina",
      section: "evidencije",
      title: "Evidencija župne imovine i infrastrukture",
      ref: "Župni ured",
      kind: "Evidencija",
      anchor: "imovina",
    },
    {
      id: "ev_financije",
      section: "evidencije",
      title: "Dokumentacija financijskog poslovanja",
      ref: "ŽEV / HBK",
      kind: "Evidencija",
      link: "pages/blagajna.html",
    },
    {
      id: "ev_racuni",
      section: "evidencije",
      title: "Računi i potvrde o uplatama",
      ref: "Župni ured",
      kind: "Evidencija",
      link: "pages/racuni.html",
    },

    /* 4 — Financije */
    {
      id: "fin_pravilnik_2000",
      section: "financije",
      title: "Pravilnici o financijskom sustavu župe (2000.)",
      ref: "HBK, str. 8",
      kind: "Pravilnik",
      link: "pages/financijska-izvjestaja.html",
    },
    {
      id: "fin_uputnice_2001",
      section: "financije",
      title: "Uputnice o financijskom poslovanju (2001.)",
      ref: "HBK, str. 9",
      kind: "Uputnica",
      link: "pages/financijska-izvjestaja.html",
    },
    {
      id: "fin_plavi_crveni",
      section: "financije",
      title: "Plavi i crveni blagajnički dnevnik",
      ref: "ŽEV",
      kind: "Dnevnik",
      link: "pages/blagajna.html",
    },
    {
      id: "fin_kvartalni",
      section: "financije",
      title: "Kvartalni obračunski list",
      ref: "Biskupija",
      kind: "Izvještaj",
      link: "pages/financijska-izvjestaja.html",
    },
    {
      id: "fin_godisnji",
      section: "financije",
      title: "Godišnji financijski list za ŽEV",
      ref: "Biskupija",
      kind: "Izvještaj",
      link: "pages/financijska-izvjestaja.html",
    },
    {
      id: "fin_dugovanja",
      section: "financije",
      title: "Pregled dugovanja (lukno, nakane, sakramenti)",
      ref: "Župni ured",
      kind: "Pregled",
      link: "pages/dugovanja.html",
    },
    {
      id: "fin_transparentnost",
      section: "financije",
      title: "Upravni i financijski dokumenti — transparentnost",
      ref: "HBK",
      kind: "Uprava",
      link: "pages/vijeca.html",
    },

    /* 5 — Pastoral */
    {
      id: "pas_program_kateheza",
      section: "pastoral",
      title: "Program župne kateheze i vjeronauka",
      ref: "HBK, str. 8",
      kind: "Program",
      desc: "Skupine po godinama, katehete, pripreme sakramenata.",
      link: "pages/krizma.html",
      templateId: "program_zupne_kateheze",
    },
    {
      id: "pas_krizma",
      section: "pastoral",
      title: "Priprema za krizmu — popisi i dokumenti",
      ref: "Sinoda",
      kind: "Evidencija",
      link: "pages/krizma.html",
    },
    {
      id: "pas_pricest",
      section: "pastoral",
      title: "Priprema za prvu sv. Pričest",
      ref: "Sinoda",
      kind: "Evidencija",
      link: "pages/prva-pricest.html",
    },
    {
      id: "pas_zpv",
      section: "pastoral",
      title: "Župno pastoralno vijeće — zapisnici i plan",
      ref: "Kan. 536",
      kind: "Vijeće",
      link: "pages/vijeca.html",
      templateId: "zapisnik_zpv",
    },
    {
      id: "pas_biskup",
      section: "pastoral",
      title: "Pisma biskupa i preporuke za župu",
      ref: "Biskupija",
      kind: "Pismo",
      link: "pages/komunikacija.html",
    },
    {
      id: "pas_posjete",
      section: "pastoral",
      title: "Pastoralne posjete i kućna pričest",
      ref: "Pastoral",
      kind: "Evidencija",
      link: "pages/posjete.html",
    },

    /* 6 — Pravno */
    {
      id: "prav_ugovor_dusobriz",
      section: "pravno",
      title: "Ugovor o dušobrižništvu (ustanova / bolnica)",
      ref: "HBK, str. 8–9",
      kind: "Ugovor",
      anchor: "ugovori",
    },
    {
      id: "prav_ugovor_gosp",
      section: "pravno",
      title: "Ugovor o gospodarskim pitanjima župe",
      ref: "HBK",
      kind: "Ugovor",
      anchor: "ugovori",
    },
    {
      id: "prav_imovina_uprav",
      section: "pravno",
      title: "Uredbe o upravljanju imovinom i arhivima",
      ref: "HBK, str. 9",
      kind: "Uredba",
      anchor: "imovina",
      link: "pages/maticne-knjige.html",
    },
    {
      id: "prav_norme_sastavnica",
      section: "pravno",
      title: "Pravne norme sastavnica župne administracije",
      ref: "CIC 515–552",
      kind: "Kanonsko pravo",
      link: "pages/sigurnost.html",
    },

    /* Dodatno */
    {
      id: "dod_pastoralni_plan",
      section: "dodatno",
      title: "Planovi i izvještaji pastoralnih aktivnosti",
      ref: "ŽPV",
      kind: "Plan",
      link: "pages/kalendar.html",
      templateId: "pastoralni_plan_godisnji",
    },
    {
      id: "dod_vjeronauk_skola",
      section: "dodatno",
      title: "Dokumentacija katoličkog vjeronauka u javnim ustanovama",
      ref: "HBK",
      kind: "Evidencija",
      templateId: "evidencija_vjeronauk_skola",
    },
    {
      id: "dod_zajednice",
      section: "dodatno",
      title: "Evidencija župnih zajednica i aktivnosti",
      ref: "Župni ured",
      kind: "Evidencija",
      link: "pages/ulice.html",
    },
    {
      id: "dod_dokumenti_excel",
      section: "dodatno",
      title: "Knjižna dokumentacija — Excel/CSV i serijski ispis",
      ref: "Župni ured",
      kind: "Alat",
      link: "pages/dokumenti.html",
    },
    {
      id: "dod_potvrde",
      section: "dodatno",
      title: "Izdavanje potvrda i isprava iz evidencije",
      ref: "Kan. 535",
      kind: "Isprava",
      link: "pages/potvrde.html",
    },
  ];

  function loadStatus() {
    try {
      return JSON.parse(localStorage.getItem(STATUS_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function saveStatus(map) {
    localStorage.setItem(STATUS_KEY, JSON.stringify(map));
  }

  function migrate(data) {
    if (!Array.isArray(data.parishProperty)) {
      data.parishProperty = [
        {
          id: "im1",
          type: "crkva",
          name: "Župna crkva Bl. Djevice Marije",
          ownership: "župa",
          location: "Trg kralja Tomislava, Slavonski Brod",
          year: 1902,
          valueNote: "Upis u zemljišne knjige",
          custodian: "vlč. Krunoslav Karas",
        },
        {
          id: "im2",
          type: "stan",
          name: "Župni stan",
          ownership: "župa",
          location: "Ulica župnika 4",
          year: 1978,
          valueNote: "Stambeno-poslovni",
          custodian: "župni ured",
        },
        {
          id: "im3",
          type: "prostor",
          name: "Katehetska dvorana",
          ownership: "župa",
          location: "Uz crkvu",
          year: 2005,
          valueNote: "Krizma, pričest, sastanci ŽPV",
          custodian: "kateheta",
        },
      ];
    }
    if (!Array.isArray(data.legalDocuments)) {
      data.legalDocuments = [
        {
          id: "lg1",
          title: "Ugovor o dušobrižništvu — Opća bolnica „Sveti Duh“",
          party: "Sveti Duh SB",
          signed: "2018-09-01",
          status: "važeći",
          storage: "Župni arhiv — mapa 3",
        },
        {
          id: "lg2",
          title: "Ugovor o gospodarskim pitanjima župe",
          party: "Đakovačko-osječka nadbiskupija",
          signed: "2015-06-12",
          status: "važeći",
          storage: "Župni arhiv — mapa 2",
        },
        {
          id: "lg3",
          title: "Sporazum o vjeronauku u OS „I. Filipović“",
          party: "Grad SB / škola",
          signed: "2022-08-20",
          status: "važeći",
          storage: "Ured katehete",
        },
      ];
    }
    if (!Array.isArray(data.pastoralPrograms)) {
      data.pastoralPrograms = [
        {
          id: "pp1",
          title: "Program župne kateheze 2025/26",
          type: "kateheza",
          period: "2025–2026",
          responsible: "Marija Kovač",
          status: "u tijeku",
        },
        {
          id: "pp2",
          title: "Pastoralni plan župe — godina 2025",
          type: "plan",
          period: "2025",
          responsible: "ŽPV",
          status: "odobren",
        },
      ];
    }
    return data;
  }

  function defaultPrintValues(settings) {
    return {
      zupa: settings.name || "",
      zupnik: settings.pastor || "",
      danas: new Date().toLocaleDateString("hr-HR"),
      datum: new Date().toLocaleDateString("hr-HR"),
      godina: String(new Date().getFullYear()),
      prisutni: "članovi ŽPV i župnik",
      dnevni_red: "1. Pastoralni plan\n2. Financije\n3. Sakramenti",
      zakljucci: "Usvojen plan za sljedeći kvartal.",
      stanje_zupe: "Pastoral i financije u redu; preporuka za katehezu.",
      preporuke: "Nastaviti rad s obiteljima i mladima.",
      program_sadrzaj: "Krizma, prva pričest, obiteljski susreti, Caritas.",
      skola: "OS I. Filipović",
      razred: "5.–8. razred",
      broj_ucenika: "—",
      kateheta: settings.kateheta || "Marija Kovač",
    };
  }

  function printTemplate(api, templateId) {
    const Doc = global.PastoralDocuments;
    const tpl = Doc?.getTemplate(templateId);
    if (!tpl) {
      api.showToast("Predložak nije učitan — osvježite stranicu");
      return;
    }
    const settings = api.getSettings?.() || {};
    const html = Doc.mergeTemplate(tpl.body, defaultPrintValues(settings));
    Doc.printHtml(html, tpl.name);
  }

  function renderImovinaPanel(data, api) {
    const esc = api.escapeHtml;
    const rows = (data.parishProperty || [])
      .map(
        (p) => `<tr>
          <td><span class="badge">${esc(p.type)}</span></td>
          <td><strong>${esc(p.name)}</strong></td>
          <td>${esc(p.location)}</td>
          <td>${esc(p.ownership)}</td>
          <td>${p.year || "—"}</td>
          <td>${esc(p.custodian || "")}</td>
        </tr>`
      )
      .join("");
    return `
      <section class="card wide admin-anchor-panel" id="admin-anchor-imovina">
        <h2 class="section-title">Župna imovina i infrastruktura</h2>
        <p class="card-sub">Evidencija prema uredbi o upravljanju imovinom — demo podaci; u produkciji povezati s knjigovodstvom i arhivom.</p>
        <div class="table-wrap"><table class="data-table">
          <thead><tr><th>Vrsta</th><th>Naziv</th><th>Lokacija</th><th>Vlasništvo</th><th>God.</th><th>Skrbnik</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="6" class="empty-state">Nema zapisa.</td></tr>'}</tbody>
        </table></div>
        <button type="button" class="btn btn-secondary btn-sm" id="admin-print-imovina">Ispis popisa imovine</button>
      </section>`;
  }

  function renderUgovoriPanel(data, api) {
    const esc = api.escapeHtml;
    const rows = (data.legalDocuments || [])
      .map(
        (u) => `<tr>
          <td><strong>${esc(u.title)}</strong></td>
          <td>${esc(u.party)}</td>
          <td>${u.signed ? api.fmtDate(u.signed) : "—"}</td>
          <td><span class="badge badge-done">${esc(u.status)}</span></td>
          <td>${esc(u.storage || "")}</td>
        </tr>`
      )
      .join("");
    return `
      <section class="card wide admin-anchor-panel" id="admin-anchor-ugovori">
        <h2 class="section-title">Ugovori i sporazumi</h2>
        <p class="card-sub">Državnopravni i crkveni ugovori župe — čuvanje u arhivu (HBK, str. 8–9).</p>
        <div class="table-wrap"><table class="data-table">
          <thead><tr><th>Dokument</th><th>Stranka</th><th>Potpis</th><th>Status</th><th>Lokacija</th></tr></thead>
          <tbody>${rows}</tbody>
        </table></div>
      </section>`;
  }

  function renderProgramsPanel(data, api) {
    const esc = api.escapeHtml;
    return `
      <section class="card admin-anchor-panel" id="admin-anchor-programi">
        <h2 class="section-title">Programi i planovi</h2>
        ${(data.pastoralPrograms || [])
          .map(
            (p) => `<div class="list-item">
              <div><strong>${esc(p.title)}</strong><br><small>${esc(p.type)} · ${esc(p.period)} · ${esc(p.responsible)}</small></div>
              <span class="badge badge-done">${esc(p.status)}</span>
            </div>`
          )
          .join("")}
      </section>`;
  }

  function mountAdminPaketPage(root, api) {
    migrate(api.getData());
    let section = "pravilnici";
    let query = "";

    function filteredItems() {
      const q = query.toLowerCase().trim();
      return CATALOG.filter((it) => {
        if (it.section !== section) return false;
        if (!q) return true;
        const blob = [it.title, it.ref, it.kind, it.desc].filter(Boolean).join(" ").toLowerCase();
        return blob.includes(q);
      });
    }

    function render() {
      const data = api.getData();
      const esc = api.escapeHtml;
      const status = loadStatus();
      const items = filteredItems();
      const inOffice = Object.values(status).filter((s) => s === "u_uredu").length;
      const total = CATALOG.length;

      const rows = items
        .map((it) => {
          const st = status[it.id] || "potrebno";
          const stLabel =
            st === "u_uredu" ? '<span class="badge badge-done">u uredu</span>' : st === "arhiva" ? '<span class="badge">arhiva</span>' : '<span class="badge badge-urgent">potrebno</span>';
          const actions = [];
          if (it.link) actions.push(`<a href="${api.pageUrl(it.link)}" class="btn btn-primary btn-sm">Otvori modul</a>`);
          if (it.templateId) actions.push(`<button type="button" class="btn btn-secondary btn-sm" data-print="${esc(it.templateId)}">Ispis</button>`);
          if (it.anchor) actions.push(`<a href="#admin-anchor-${it.anchor}" class="btn btn-ghost btn-sm">Evidencija</a>`);
          actions.push(
            `<select class="admin-doc-status-select" data-doc-id="${esc(it.id)}" title="Status u uredu">
              <option value="potrebno" ${st === "potrebno" ? "selected" : ""}>Potrebno</option>
              <option value="u_uredu" ${st === "u_uredu" ? "selected" : ""}>U uredu</option>
              <option value="arhiva" ${st === "arhiva" ? "selected" : ""}>Arhiva</option>
            </select>`
          );
          return `<tr>
            <td><strong>${esc(it.title)}</strong>${it.desc ? `<br><small class="card-sub">${esc(it.desc)}</small>` : ""}</td>
            <td>${esc(it.kind || "—")}</td>
            <td>${esc(it.ref || "—")}</td>
            <td>${stLabel}</td>
            <td class="crud-actions" style="flex-wrap:wrap;gap:6px">${actions.join("")}</td>
          </tr>`;
        })
        .join("");

      root.innerHTML = `
        <section class="card wide admin-paket-hero">
          <h2 class="section-title">Administrativni paket župe</h2>
          <p class="card-sub">Pravilnici HBK, službeni obrasci, evidencije, financije, pastoralni programi i pravni dokumenti — povezano s modulima Pastoral. Usklađeno s popisom župne administracije (uredbe str. 8–16, vizitacije 2001., financije 2000.–2001.).</p>
          <p class="admin-paket-progress"><strong>${inOffice}</strong> / ${total} označeno kao <em>u uredu</em></p>
          <div class="admin-paket-quicklinks">
            <a href="${api.pageUrl("pages/maticne-knjige.html")}" class="btn btn-ghost btn-sm">Matične knjige</a>
            <a href="${api.pageUrl("pages/formulari.html")}" class="btn btn-ghost btn-sm">Formulari</a>
            <a href="${api.pageUrl("pages/financijska-izvjestaja.html")}" class="btn btn-ghost btn-sm">Financije</a>
            <a href="${api.pageUrl("pages/vijeca.html")}" class="btn btn-ghost btn-sm">Vijeća</a>
            <a href="${api.pageUrl("pages/dokumenti.html")}" class="btn btn-ghost btn-sm">Excel / ispis</a>
          </div>
        </section>
        <section class="card wide">
          <div class="admin-paket-toolbar">
            <input type="search" id="admin-doc-search" class="admin-doc-search" placeholder="Pretraži dokumentaciju…" value="${esc(query)}">
          </div>
          <nav class="family-tab-nav admin-section-nav" role="tablist">
            ${SECTIONS.map(
              (s) =>
                `<button type="button" class="family-tab admin-section-tab ${s.id === section ? "is-on" : ""}" data-sec="${s.id}">${esc(s.short)}. ${esc(s.label)}</button>`
            ).join("")}
          </nav>
          <div class="table-wrap" style="margin-top:16px">
            <table class="data-table admin-catalog-table">
              <thead><tr><th>Dokument / uredba</th><th>Vrsta</th><th>Izvor</th><th>Status</th><th>Akcije</th></tr></thead>
              <tbody>${rows || '<tr><td colspan="5" class="empty-state">Nema stavki za ovaj filter.</td></tr>'}</tbody>
            </table>
          </div>
        </section>
        ${renderImovinaPanel(data, api)}
        ${renderUgovoriPanel(data, api)}
        ${renderProgramsPanel(data, api)}`;

      root.querySelector("#admin-doc-search")?.addEventListener("input", (e) => {
        query = e.target.value;
        render();
      });
      root.querySelectorAll(".admin-section-tab").forEach((btn) => {
        btn.addEventListener("click", () => {
          section = btn.dataset.sec;
          render();
        });
      });
      root.querySelectorAll("[data-print]").forEach((btn) => {
        btn.addEventListener("click", () => printTemplate(api, btn.dataset.print));
      });
      root.querySelectorAll(".admin-doc-status-select").forEach((sel) => {
        sel.addEventListener("change", () => {
          const map = loadStatus();
          map[sel.dataset.docId] = sel.value;
          saveStatus(map);
          api.showToast("Status spremljen");
          render();
        });
      });
      root.querySelector("#admin-print-imovina")?.addEventListener("click", () => {
        const settings = api.getSettings?.() || {};
        const lines = (data.parishProperty || [])
          .map((p) => `<tr><td>${esc(p.type)}</td><td>${esc(p.name)}</td><td>${esc(p.location)}</td><td>${esc(p.ownership)}</td></tr>`)
          .join("");
        const html = `<div class="print-doc"><h2 style="text-align:center">POPIS ŽUPNE IMOVINE</h2>
          <p>Župa: <strong>${esc(settings.name || "")}</strong> · ${esc(defaultPrintValues(settings).danas)}</p>
          <table border="1" cellpadding="6" style="width:100%;border-collapse:collapse"><thead><tr><th>Vrsta</th><th>Naziv</th><th>Lokacija</th><th>Vlasništvo</th></tr></thead><tbody>${lines}</tbody></table>
          <p style="margin-top:2em">Župnik: ${esc(settings.pastor || "")}</p></div>`;
        global.PastoralDocuments?.printHtml(html, "Popis imovine");
      });
    }

    render();
  }

  global.PastoralAdminDocs = {
    CATALOG,
    SECTIONS,
    migrate,
    mountAdminPaketPage,
    loadStatus,
  };
})(typeof window !== "undefined" ? window : global);
