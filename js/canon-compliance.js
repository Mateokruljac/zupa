/**
 * Kanonski okvir (CIC 515–552, sinoda Đakovo, Mićan) — zahtjevi po stranici
 */
(function (global) {
  const SOURCES =
    "CIC kann. 515–552 (GK Zagreb 1996.); J. Brkan, Župa u zakonodavstvu Katoličke Crkve, Split 2004.; II. sinoda đakovačko-srijemska (2008) br. 554, 587–595, 598–600, 619–640; M. Mićan, Povrat crkvenih matičnih knjiga, VĐSB 6/2006.";

  const SPECS = {
    dashboard: {
      title: "Župa kao stabilna zajednica",
      canons: "515–519, 528–531",
      synod: "554",
      intro: "Župnik vodi cjelokupnu dušobrižničku službu; nadzorna ploča služi pregledu obveza prema kanonu i sinodi.",
      required: [
        "Pregled pastoralnog i ekonomskog plana",
        "Podsjetnici na rokove (ŽPV, ŽEV, biskupija)",
        "Evidencija sakramenata i posjeta",
      ],
      app: ["KPI i podsjetnici", "Prezentacija za župu", "Brzi pristup nakana i dugovanjima"],
    },
    obitelji: {
      title: "Obitelj u župnoj zajednici",
      canons: "529–530, 222",
      synod: "619–625",
      intro: "Poznavanje obitelji omogućuje pravednu pastoralnu brigu i praćenje župnog lukna (dobrovoljni doprinos).",
      required: [
        "Popis obitelji na teritoriju župe",
        "Članovi, sakramenti, pastoralne bilješke",
        "Lukno i davanja po godinama",
        "Zadnji pastoralni posjet",
      ],
      app: ["CRUD obitelji i članova", "Lukno po godinama", "Ulice i adrese"],
    },
    ulice: {
      title: "Teritorij župe",
      canons: "518–519",
      synod: "587",
      intro: "Granice župe određuje biskup; ulica pomaže organizirati pastoral po kvartovima.",
      required: ["Evidencija ulica i zona", "Povezivanje obitelji s adresom"],
      app: ["Ulice i pregled po adresi"],
    },
    posjete: {
      title: "Pastoralna briga",
      canons: "531, 1004",
      synod: "598–600",
      intro: "Župnik i suradnici posjećuju bolesne, obitelji i izolirane vjernike.",
      required: ["Plan posjeta", "Zapis svrhe i izvještaja", "Kućna sv. Pričest / pomazanje"],
      app: ["Raspored posjeta", "Veza na obitelj"],
    },
    nakane: {
      title: "Misne nakane i stipendiji",
      canons: "948, 1308",
      synod: "590",
      intro: "Nakane se upisuju u propisane knjige; stipendij je dar za misu (ne „naknada“ u komercijalnom smislu).",
      required: [
        "Kalendar nakana po misama",
        "Evidencija plaćenih / neplaćenih",
        "Gregorijanske serije (30 misa)",
      ],
      app: ["Kalendar", "Plaćanje / platiti kasnije", "Župni list"],
    },
    "zupni-listic": {
      title: "Župni listić",
      canons: "393, 528",
      synod: "587, 590",
      intro: "Tjedni župni list objavljuje raspored misa, nakane, obavijesti i pastoralne vijesti za župljane.",
      required: ["Predložak listića", "Povijest izdanja", "Usklađenost s rasporedom misa i nakana"],
      app: ["Predložak HTML", "Automatsko popunjavanje", "Povijest listića"],
    },
    krsenja: {
      title: "Knjiga rođenih i krštenih",
      canons: "535, 877–878",
      synod: "619, 630",
      intro: "Krštenje se upisuje u matičnu knjigu; krsni list izdaje se iz knjige. Priprema roditelja i kumova obavezna je.",
      required: [
        "Redni broj upisa (matična knjiga)",
        "Podaci o djetetu, roditeljima, kumovima",
        "Datum krštenja i slavlja",
        "Priprema prije sakramenta",
      ],
      app: ["Evidencija + registryNo", "Priprema krštenja", "Stipendij / plaćanje"],
    },
    "prva-pricest": {
      title: "Prva sv. Pričest",
      canons: "913–914",
      synod: "621–622",
      intro: "Kateheza i popis prvopričesnika; župnik odobrava pristup Euharistiji.",
      required: ["Skupine po godini", "Kateheti", "Popis kandidata", "Datum svečanosti"],
      app: ["Skupine", "Import/export", "Dokumenti"],
    },
    krizma: {
      title: "Knjiga krizmanika",
      canons: "879, 885",
      synod: "621–623",
      intro: "Krizma se upisuje; pristupnica i popis krizmanika vode se za biskupiju i arhiv.",
      required: [
        "Godina i biskup / ordinarij",
        "Kateheta i krizmanici",
        "Status pripreme",
        "Upis nakon krizme",
      ],
      app: ["Grupe po godini", "Pristupnica", "Potvrde"],
    },
    vjencanja: {
      title: "Knjiga vjenčanih",
      canons: "1066–1071, 1123",
      synod: "624–628",
      intro: "Priprema braka (sastanci), dokumentacija slobode za vjenčanje, slavlje i upis u knjigu.",
      required: [
        "Priprema braka (broj sastanaka)",
        "Dokumenti u redu",
        "Svjedoci, ženik i nevjesta",
        "Upis u matičnu knjigu",
      ],
      app: ["Evidencija parova", "Priprema vjenčanja", "Checklista"],
    },
    pogrebi: {
      title: "Knjiga umrlih",
      canons: "535, 1176",
      synod: "629",
      intro: "Smrt i ukop bilježe se; misa opela i pastoral obitelji preminuloga.",
      required: ["Podaci o preminulom", "Datum pogreba / ukopa", "Kontakt obitelji", "Stipendij mise"],
      app: ["Evidencija pogreba", "Javna prijava ukopa"],
    },
    pomazanje: {
      title: "Pomazanje bolesnika",
      canons: "1004–1007",
      synod: "598",
      intro: "Pastoral bolesnih; zapis posjeta i slavlja sakramenta.",
      required: ["Plan posjeta", "Obavljeno / nadolazeće"],
      app: ["Tablica pomazanja"],
    },
    dugovanja: {
      title: "Doprinos župi",
      canons: "222, 531",
      synod: "590–595",
      intro: "Lukno i nakane nisu „dug“ u građanskopravnom smislu, ali se prate radi transparentnosti i podsjetnika.",
      required: ["Pregled po kategorijama i godinama", "Izdavanje računa / potvrde uplate"],
      app: ["Lukno, nakane, sakramenti", "Izdaj račun"],
    },
    racuni: {
      title: "Financijska transparentnost",
      canons: "537, 1287",
      synod: "587–595",
      intro: "Računi vjernicima uz darove; ŽEV savjetuje o većim rashodima.",
      required: ["Numeracija računa", "Status plaćanja", "Veza na izvor (nakana, lukno)"],
      app: ["Računi", "Potvrda uplate"],
    },
    blagajna: {
      title: "Župno ekonomsko vijeće",
      canons: "537, 1287",
      synod: "587–595",
      intro: "ŽEV pomaže u proračunu, pregledava blagajnu i daje mišljenje (savjetodavno, ne odlučujuće).",
      required: [
        "Dnevnik ulaza i izlaza",
        "Godišnji izvještaj za ŽEV",
        "Čuvanje isprava i dokaznica",
      ],
      app: ["Blagajna", "Izvještaj ŽEV", "Kategorije"],
    },
    potvrde: {
      title: "Izdavanje isprava",
      canons: "535, 895",
      synod: "630",
      intro: "Izvadci i potvrde temelje se na matičnim knjigama i evidenciji.",
      required: ["Samo iz službenih podataka", "Vrsta isprave (krštenje, krizma, lukno…)"],
      app: ["Predlošci potvrda", "Ispis"],
    },
    dokumenti: {
      title: "Dokumenti i serijski ispis",
      canons: "535",
      synod: "630",
      intro: "Pristupnice, liste za krizmu/pričest — usklađeno s knjigama.",
      required: ["Predlošci", "Excel/CSV za skupine"],
      app: ["Predlošci", "Mapiranje stupaca"],
    },
    kalendar: {
      title: "Pastoralni plan",
      canons: "536",
      synod: "554, 619",
      intro: "ŽPV sudjeluje u planiranju pastoralnog rada (naviještanje, bogoslužje, dobrotvornost).",
      required: ["Župni događaji", "Liturgijski dani"],
      app: ["Kalendar", "Liturgijski API"],
    },
    zadaci: {
      title: "Zadaci ureda i vijeća",
      canons: "536–537",
      synod: "554",
      intro: "Zadaci za župnika, ŽPV, ŽEV i biskupiju.",
      required: ["Rokovi i prioriteti", "Kategorije ŽPV / ŽEV / biskupija"],
      app: ["Zadaci", "Kategorije"],
    },
    "javne-prijave": {
      title: "Prijave vjernika",
      canons: "515, 213",
      synod: "640",
      intro: "Vjernik podnosi podatke; župni ured provjerava i unosi u evidenciju (ne automatski u knjigu).",
      required: ["Pregled prijava", "Odobrenje / odbijanje", "Unos u sakramentalnu evidenciju"],
      app: ["Inbox prijava", "Portal /public/"],
    },
    komunikacija: {
      title: "Obavještavanje župe",
      canons: "536, 212",
      synod: "554",
      intro: "Obavijesti i predlošci poruka za transparentnost pastoralnog rada.",
      required: ["Župni list / obavijesti", "Predlošci SMS/e-mail"],
      app: ["Obavijesti", "Predlošci poruka"],
    },
    podsjetnici: {
      title: "Organizacija obveza",
      canons: "531",
      synod: "—",
      intro: "Centralni inbox za lukno, nakane, posjete, prijave.",
      required: ["Praćenje rokova", "Označavanje riješenog"],
      app: ["Inbox", "Dashboard widget"],
    },
    korisnici: {
      title: "Korisnici i grupe pristupa",
      canons: "519, 529",
      synod: "—",
      intro: "Svećenici župe i ostali korisnici — tko smije vidjeti financije, matice i pastoralne module.",
      required: ["Evidencija svećenika", "Grupe s dozvolama", "Osobni račun za pristup"],
      app: ["Svećenici župe", "Grupe", "Korisnici aplikacije"],
    },
    postavke: {
      title: "Podaci župe",
      canons: "515–522",
      synod: "587",
      intro: "Identitet župe, kontakt župnika, branding — usklađenost s dekretom o ustanovljenju.",
      required: ["Naziv, župnik, kontakt", "Logo za portal", "Sigurnost podataka"],
      app: ["Postavke", "Korisnici i grupe", "Sigurnost", "Export podataka"],
    },
    sigurnost: {
      title: "Zaštita podataka vjernika",
      canons: "220, 535",
      synod: "—",
      intro: "Osobni podaci u službi Crkve; pristup po ulogama; produkcija na sigurnom serveru.",
      required: ["Uloge u uredu", "Odvojen javni portal", "GDPR u produkciji"],
      app: ["Demo sesija", "Usporedba demo/produkcija"],
    },
    "maticne-knjige": {
      title: "Crkvene matične knjige",
      canons: "535, 552",
      synod: "630, Mićan",
      intro:
        "Knjige rođenih/krštenih, vjenčanih, umrlih i krizmanika čuvaju se u župi (povrat knjiga prema biskupiji — arhiv).",
      required: [
        "Fizička lokacija i skrbnik",
        "Zadnji upis i redni broj",
        "Usklađenost s digitalnom evidencijom",
        "Izdavanje izvadaka samo iz knjige",
      ],
      app: ["Pregled knjiga", "Status sinkronizacije"],
    },
    vijeca: {
      title: "ŽPV i ŽEV",
      canons: "536–537",
      synod: "554, 587–595",
      intro:
        "Župno pastoralno vijeće planira i prati pastoral; župno ekonomsko vijeće savjetuje o financijama (mišljenje, ne zamjena župnika).",
      required: [
        "Članovi (potvrda biskupa za ŽPV)",
        "Zapisnici sastanaka",
        "Godišnji pregled blagajne (ŽEV)",
        "Sudjelovanje u pastoralnom planu",
      ],
      app: ["Popis članova", "Zadnji / sljedeći sastanak", "Link na blagajnu i zadatke"],
    },
    vjernici: {
      title: "Pojedinačni vjernici",
      canons: "529",
      synod: "619",
      intro: "Pregled pojedinačnih zapisa (nasljeđe); preporuka: obiteljski karton.",
      required: ["Veza na obitelj", "Kontakt i uloge"],
      app: ["Tablica vjernika", "Preusmjerenje na obitelji"],
    },
    "admin-paket": {
      title: "Administrativni paket i uredbe",
      canons: "515–522, 535, 536–537",
      synod: "587, 630, 554",
      intro:
        "Pravilnici HBK o maticama, arhivima, financijama i radu ureda; službeni obrasci vizitacija; evidencija imovine i ugovora.",
      required: [
        "Pravilnik o maticama i uredskim knjigama",
        "Financijski izvještaji za ŽEV",
        "Popis župne imovine",
        "Ugovori s ustanovama i državom",
        "Programi kateheze i pastoralni plan",
      ],
      app: [
        "Katalog uredbi (6 odjeljaka)",
        "Status u uredu / arhiva",
        "Poveznice na module",
        "Ispis vizitacija i planova",
      ],
    },
    formulari: {
      title: "Službeni formulari",
      canons: "535, 1066",
      synod: "630",
      intro: "Ispis krsnog lista, vjenčanih, smrtnog lista i sl. — podaci iz matice.",
      required: ["Pregled i ispis", "Spremanje nacrta", "Učitavanje iz matice"],
      app: ["Katalog župni-ured", "PDF / ispis", "Spremeni obrasci"],
    },
    poruke: {
      title: "Komunikacija ureda",
      canons: "—",
      synod: "—",
      intro: "Interna pošta između župnika, upravitelja i suradnika.",
      required: ["Nepročitane obavijesti", "Povijest dopisa"],
      app: ["Inbox poruka", "Nova poruka"],
    },
    "financijska-izvjestaja": {
      title: "Izvješća ŽEV",
      canons: "537",
      synod: "587–595",
      intro: "Kvartalni obračunski i godišnji financijski list.",
      required: ["Obračunski list (plavi)", "Financijski list (godina)"],
      app: ["Q izvješće", "Godišnje izvješće", "Ispis"],
    },
  };

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function statusFromData(pageId, data) {
    const checks = [];
    if (pageId === "krsenja") {
      const missing = (data.baptisms || []).filter((b) => !b.registryNo).length;
      checks.push({
        ok: missing === 0,
        text: missing ? `${missing} krštenja bez broja matične knjige` : "Svi upisi imaju registryNo",
      });
    }
    if (pageId === "blagajna") {
      checks.push({
        ok: (data.cashbook || []).length > 0,
        text: (data.cashbook || []).length ? "Blagajnički dnevnik vodi se" : "Dnevnik prazan",
      });
    }
    if (pageId === "maticne-knjige") {
      (data.registryBooks || []).forEach((b) => {
        checks.push({
          ok: b.status === "u župi",
          text: `${b.title}: ${b.status}`,
        });
      });
    }
    if (pageId === "vijeca") {
      const zpv = data.pastoralCouncil;
      checks.push({
        ok: (zpv?.members?.length || 0) >= 7,
        text: `ŽPV: ${zpv?.members?.length || 0} članova (preporuka 7–30)`,
      });
    }
    return checks;
  }

  function renderPanelHtml(spec, pageId, data) {
    const checks = statusFromData(pageId, data);
    const checksHtml = checks.length
      ? `<ul class="canon-checks">${checks
          .map((c) => `<li class="${c.ok ? "is-ok" : "is-warn"}">${esc(c.text)}</li>`)
          .join("")}</ul>`
      : "";

    return `
      <details class="card canon-panel" data-canon-panel>
        <summary class="canon-panel-summary">
          <span class="canon-panel-badge">Kanonski okvir</span>
          <strong>${esc(spec.title)}</strong>
          <span class="card-sub canon-panel-meta">CIC ${esc(spec.canons)}${spec.synod ? ` · Sinoda ${esc(spec.synod)}` : ""}</span>
        </summary>
        <div class="canon-panel-body">
          <p class="card-sub">${esc(spec.intro)}</p>
          <div class="canon-panel-cols">
            <div>
              <h4 class="canon-h4">Što zakon traži</h4>
              <ul>${spec.required.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
            </div>
            <div>
              <h4 class="canon-h4">U Pastoralu (demo)</h4>
              <ul>${spec.app.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
            </div>
          </div>
          ${checksHtml}
          <p class="canon-sources card-sub">${esc(SOURCES)}</p>
        </div>
      </details>`;
  }

  function mountIntoPage(pageId, api) {
    const spec = SPECS[pageId];
    if (!spec) return;
    const rootId = pageId === "dashboard" ? "dashboard-root" : "page-root";
    const root = document.getElementById(rootId);
    if (!root) return;
    if (root.querySelector("[data-canon-panel]")) return;

    const data = api.getData ? api.getData() : {};
    const wrap = document.createElement("div");
    wrap.innerHTML = renderPanelHtml(spec, pageId, data);
    root.insertBefore(wrap.firstElementChild, root.firstChild);
  }

  function mountMaticneKnjigePage(el, api) {
    const d = api.getData();
    const books = d.registryBooks || [];
    const baptCount = (d.baptisms || []).length;
    const wedCount = (d.weddings || []).length;
    const funCount = (d.funerals || []).length;
    el.innerHTML = `
      <section class="card wide">
        <h2 class="section-title">Crkvene matične knjige</h2>
        <p class="card-sub">Kan. 535 · povrat knjiga u župu (M. Mićan). Digitalna evidencija ne zamjenjuje fizičku knjigu. Učitavanje u formular — kao <a href="https://zupni-ured.com.hr/manual.pdf" target="_blank" rel="noopener">župni-ured</a>.</p>
        <div class="kpi-row" style="margin-top:12px">
          <article class="card kpi-card"><p class="card-label">Krštenja (digitalno)</p><p class="card-value">${baptCount}</p></article>
          <article class="card kpi-card"><p class="card-label">Vjenčanja</p><p class="card-value">${wedCount}</p></article>
          <article class="card kpi-card"><p class="card-label">Umrli</p><p class="card-value">${funCount}</p></article>
        </div>
        <a href="${api.pageUrl("pages/krsenja.html")}" class="btn btn-ghost btn-sm">Matica krštenih +</a>
        <a href="${api.pageUrl("pages/vjencanja.html")}" class="btn btn-ghost btn-sm">Matica vjenčanih</a>
        <a href="${api.pageUrl("pages/pogrebi.html")}" class="btn btn-ghost btn-sm">Matica umrlih</a>
        <a href="${api.pageUrl("pages/admin-paket.html")}" class="btn btn-primary btn-sm">Uredbe i dokumentacija</a>
        <a href="${api.pageUrl("pages/formulari.html")}" class="btn btn-ghost btn-sm">Formulari za ispis</a>
      </section>
      <div class="canon-books-grid">
        ${books
          .map(
            (b) => `
          <article class="card">
            <h3>${api.escapeHtml(b.title)}</h3>
            <p><span class="badge ${b.status === "u župi" ? "badge-done" : ""}">${api.escapeHtml(b.status)}</span></p>
            <dl class="canon-dl">
              <dt>Lokacija</dt><dd>${api.escapeHtml(b.location)}</dd>
              <dt>Skrbnik</dt><dd>${api.escapeHtml(b.custodian)}</dd>
              <dt>Zadnji upis</dt><dd>${api.fmtDate(b.lastEntry)} · br. ${api.escapeHtml(b.lastNo || "—")}</dd>
            </dl>
            <p class="card-sub">${api.escapeHtml(b.notes || "")}</p>
          </article>`
          )
          .join("")}
      </div>`;
    mountIntoPage("maticne-knjige", api);
  }

  function mountVijecaPage(el, api) {
    const d = api.getData();
    const zpv = d.pastoralCouncil || {};
    const zev = d.economicCouncil || {};
    const memberRow = (m) =>
      `<li><strong>${api.escapeHtml(m.name)}</strong> — ${api.escapeHtml(m.role)}${m.confirmed ? ' <span class="badge badge-done">potvrđen</span>' : ""}</li>`;

    el.innerHTML = `
      <section class="card">
        <h2 class="section-title">Župno pastoralno vijeće (ŽPV)</h2>
        <p class="card-sub">Kan. 536 · Sinoda 554 — savjetodavno i djelatno tijelo (7–30 članova, potvrda biskupa).</p>
        <p class="card-sub">Ustanovljeno: ${api.fmtDate(zpv.established)} · Zadnji sastanak: ${api.fmtDate(zpv.lastMeeting)} · Sljedeći: ${api.fmtDate(zpv.nextMeeting)}</p>
        <ul class="canon-member-list">${(zpv.members || []).map(memberRow).join("")}</ul>
        <a href="${api.pageUrl("pages/zadaci.html")}?cat=ŽPV" class="btn btn-ghost btn-sm">Zadaci ŽPV</a>
        <a href="${api.pageUrl("pages/kalendar.html")}" class="btn btn-ghost btn-sm">Kalendar</a>
      </section>
      <section class="card">
        <h2 class="section-title">Župno ekonomsko vijeće (ŽEV)</h2>
        <p class="card-sub">Kan. 537 · Sinoda 587–595 — proračun, pregled blagajne, mišljenje (ne odlučuje umjesto župnika).</p>
        <p class="card-sub">Zadnji pregled: ${api.fmtDate(zev.lastReview)} · Proračun ${zev.budgetYear || "—"}</p>
        <ul class="canon-member-list">${(zev.members || []).map(memberRow).join("")}</ul>
        <a href="${api.pageUrl("pages/blagajna.html")}" class="btn btn-primary btn-sm">Blagajna i izvještaj</a>
      </section>`;
    mountIntoPage("vijeca", api);
  }

  global.PastoralCanon = {
    SPECS,
    SOURCES,
    mountIntoPage,
    mountMaticneKnjigePage,
    mountVijecaPage,
  };
})(typeof window !== "undefined" ? window : global);
