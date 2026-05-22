/**
 * Formulari za ispis — usklađeno s korisničkim priručnikom župni-ured.com.hr
 */
(function (global) {
  const SAVED_KEY = "pastoral_saved_forms";

  const CATEGORIES = [
    { id: "krstenje", label: "Krštenje" },
    { id: "potvrda", label: "Potvrda (krizma)" },
    { id: "vjenčanje", label: "Vjenčanje" },
    { id: "sprovod", label: "Sprovod" },
    { id: "obracenje", label: "Obraćenje" },
    { id: "ostalo", label: "Ostalo" },
  ];

  const FORMS = [
    { id: "krsni_list", cat: "krstenje", name: "Krsni list", fields: ["dijete", "datum_krstenja", "roditelji", "kumovi", "mjesto", "zupnik", "zupa"] },
    { id: "pristupnica_krizma", cat: "potvrda", name: "Pristupnica za sv. Potvrdu i obavijest o upisu", fields: ["ime_prezime", "datum_rodjenja", "datum_krstenja", "kum", "zupnik", "zupa"] },
    { id: "vjencani_list", cat: "vjenčanje", name: "Vjenčani list", fields: ["mladozenja", "mlada", "datum", "svjedoci", "zupnik", "zupa"] },
    { id: "postupak_zenidba", cat: "vjenčanje", name: "Postupak za ženidbu", fields: ["mladozenja", "mlada", "adresa", "datum_vjencanja", "zupnik", "zupa"] },
    { id: "otpusnica_vjencanje", cat: "vjenčanje", name: "Otpusnica za vjenčanje", fields: ["osoba", "zupa_odlaska", "zupa_cilj", "zupnik", "zupa"] },
    { id: "dopustenje_van_zupe", cat: "vjenčanje", name: "Dopuštenje za ženidbu izvan vlastite župe", fields: ["mladenci", "zupa", "datum", "zupnik"] },
    { id: "izjava_mjesovita", cat: "vjenčanje", name: "Izjave i obećanja — mješovita ženidba", fields: ["mladozenja", "mlada", "vjera_zaručnika", "zupnik", "zupa"] },
    { id: "molba_mjesovita", cat: "vjenčanje", name: "Molba za dopuštenje mješovite ženidbe", fields: ["mladenci", "zupnik", "zupa", "danas"] },
    { id: "molba_razlicita_vjera", cat: "vjenčanje", name: "Molba za oprost od zapreke različitosti vjere", fields: ["mladenci", "zupnik", "zupa"] },
    { id: "zapisnik_prijasnja_veza", cat: "vjenčanje", name: "Zapisnik o prijašnjoj ženidbenoj vezi", fields: ["osoba", "opis", "zupnik", "zupa"] },
    { id: "izjava_roditelja_malo", cat: "vjenčanje", name: "Izjava roditelja uz ženidbu maloljetnika", fields: ["dijete", "roditelji", "adresa", "zupnik", "zupa"] },
    { id: "navjestaj", cat: "vjenčanje", name: "Ženidbeni navještaj u župi prebivališta", fields: ["mladenci", "datum_navjestaja", "zupa", "zupnik"] },
    { id: "obavijest_zenidba", cat: "vjenčanje", name: "Obavijest o sklopljenoj ženidbi", fields: ["mladenci", "datum", "crkva", "zupnik", "zupa"] },
    { id: "smrtni_list", cat: "sprovod", name: "Smrtni list", fields: ["pokojnik", "datum_smrti", "datum_pogreba", "prebivaliste", "zupnik", "zupa"] },
    { id: "smrtni_list_v2", cat: "sprovod", name: "Smrtni list (verzija 2)", fields: ["pokojnik", "datum_smrti", "datum_pogreba", "zupnik", "zupa"] },
    { id: "izvadak_obracenje", cat: "obracenje", name: "Izvadak iz Knjige primljenih u potpuno zajedništvo", fields: ["ime", "datum", "zupnik", "zupa"] },
    { id: "posvjedocenje", cat: "ostalo", name: "Posvjedočenje", fields: ["sadrzaj", "osoba", "zupnik", "zupa", "danas"] },
    { id: "potvrdnica", cat: "ostalo", name: "Potvrdnica", fields: ["sadrzaj", "osoba", "zupnik", "zupa", "danas"] },
  ];

  function bodyFor(form) {
    return `<div class="print-doc zupni-form-doc">
      <p class="card-sub" style="text-align:center">${form.name}</p>
      <h2 style="text-align:center;font-family:Georgia,serif">${form.name.toUpperCase()}</h2>
      <p>Župa: <strong>{{zupa}}</strong></p>
      ${form.fields.filter((f) => !["zupa", "zupnik", "danas"].includes(f)).map((f) => `<p><strong>${f.replace(/_/g, " ")}:</strong> {{${f}}}</p>`).join("")}
      <p style="margin-top:2em">Mjesto i datum: {{zupa}}, {{danas}}</p>
      <p>Župnik: {{zupnik}}</p>
    </div>`;
  }

  function loadSaved() {
    try {
      return JSON.parse(localStorage.getItem(SAVED_KEY) || "[]");
    } catch {
      return [];
    }
  }

  function saveSaved(list) {
    localStorage.setItem(SAVED_KEY, JSON.stringify(list));
  }

  function merge(html, values) {
    return html.replace(/\{\{(\w+)\}\}/g, (_, k) => values[k] ?? "—");
  }

  function mountFormulariPage(root, api) {
    const settings = api.getSettings();
    const saved = loadSaved();
    let cat = "krstenje";
    let formId = FORMS.find((f) => f.cat === cat)?.id || FORMS[0].id;

    function render() {
      const form = FORMS.find((f) => f.id === formId) || FORMS[0];
      const esc = api.escapeHtml;
      const vals = {};
      form.fields.forEach((f) => {
        vals[f] = settings[f] || "";
      });
      vals.zupa = settings.name || "";
      vals.zupnik = settings.pastor || "";
      vals.danas = new Date().toLocaleDateString("hr-HR");

      root.innerHTML = `
        <section class="card">
          <p class="card-sub">Katalog formulara prema <a href="https://zupni-ured.com.hr/manual.pdf" target="_blank" rel="noopener">župni-ured.com.hr</a> — ispis, pregled, PDF, spremanje za kasnije.</p>
          <div class="form-grid" style="margin-top:12px">
            <div class="form-group"><label>Kategorija</label>
              <select id="zf-cat">${CATEGORIES.map((c) => `<option value="${c.id}" ${c.id === cat ? "selected" : ""}>${esc(c.label)}</option>`).join("")}</select>
            </div>
            <div class="form-group form-wide"><label>Formular</label>
              <select id="zf-form">${FORMS.filter((f) => f.cat === cat).map((f) => `<option value="${f.id}" ${f.id === formId ? "selected" : ""}>${esc(f.name)}</option>`).join("")}</select>
            </div>
          </div>
          <label class="card-sub"><input type="checkbox" id="zf-other-parish"> Ispis u drugoj župi (prilagodba pisača)</label>
        </section>
        <section class="card">
          <h3 class="section-title">Podaci</h3>
          <div id="zf-fields" class="form-grid">${form.fields.map((f) => `<div class="form-group"><label>${esc(f)}</label><input type="text" data-zf-field="${f}" value="${esc(vals[f] || "")}"></div>`).join("")}</div>
          <div class="racuni-toolbar" style="margin-top:16px">
            <button type="button" class="btn btn-primary btn-sm" id="zf-matica">Učitaj iz matice</button>
            <button type="button" class="btn btn-primary btn-sm" id="zf-preview">Pregled</button>
            <button type="button" class="btn btn-secondary btn-sm" id="zf-print">Ispis</button>
            <button type="button" class="btn btn-ghost btn-sm" id="zf-save">Spremi obrazac</button>
            <select id="zf-saved-open"><option value="">Otvori spremljeni…</option>${saved.map((s) => `<option value="${esc(s.id)}">${esc(s.label)}</option>`).join("")}</select>
          </div>
        </section>
        <section class="card wide">
          <h3 class="section-title">Povezano s maticama</h3>
          <p class="card-sub">Pretraga iz knjiga krštenih, vjenčanih ili umrlih — popunjava polja formulara.</p>
          <a href="${api.pageUrl("pages/maticne-knjige.html")}" class="btn btn-ghost btn-sm">Matične knjige</a>
          <a href="${api.pageUrl("pages/krsenja.html")}" class="btn btn-ghost btn-sm">Krštenja</a>
          <a href="${api.pageUrl("pages/vjencanja.html")}" class="btn btn-ghost btn-sm">Vjenčanja</a>
        </section>`;

      root.querySelector("#zf-cat")?.addEventListener("change", (e) => {
        cat = e.target.value;
        formId = FORMS.find((f) => f.cat === cat)?.id;
        render();
      });
      root.querySelector("#zf-form")?.addEventListener("change", (e) => {
        formId = e.target.value;
        render();
      });

      const collect = () => {
        const v = { zupa: settings.name, zupnik: settings.pastor, danas: new Date().toLocaleDateString("hr-HR") };
        root.querySelectorAll("[data-zf-field]").forEach((inp) => {
          v[inp.dataset.zfField] = inp.value.trim();
        });
        return v;
      };

      const maticaTypes = () => {
        if (cat === "krstenje") return ["krštenja"];
        if (cat === "vjenčanje") return ["vjenčanja", "krštenja"];
        if (cat === "sprovod") return ["umrli"];
        return ["krštenja", "vjenčanja", "umrli"];
      };

      root.querySelector("#zf-matica")?.addEventListener("click", () => {
        if (!api.getData || !global.PastoralMaticaLookup) return api.showToast("Matica nije dostupna");
        global.PastoralMaticaLookup.openSearchModal(
          { getData: api.getData, escapeHtml: esc, showToast: api.showToast },
          {
            types: maticaTypes(),
            title: "Učitaj u formular",
            onPick: (hit) => {
              Object.entries(hit.payload || {}).forEach(([k, val]) => {
                const inp = root.querySelector(`[data-zf-field="${k}"]`);
                if (inp && val) inp.value = val;
              });
              api.showToast("Podaci učitani");
            },
          }
        );
      });

      root.querySelector("#zf-preview")?.addEventListener("click", () => {
        const html = merge(bodyFor(form), collect());
        global.PastoralModal?.openDetail({ title: form.name, size: "lg", body: html });
      });

      root.querySelector("#zf-print")?.addEventListener("click", () => {
        const w = window.open("", "_blank");
        if (!w) return api.showToast("Omogućite skočne prozore");
        w.document.write(`<html><head><title>${form.name}</title><link rel="stylesheet" href="../css/styles.css"></head><body>${merge(bodyFor(form), collect())}</body></html>`);
        w.document.close();
        w.focus();
        w.print();
      });

      root.querySelector("#zf-save")?.addEventListener("click", () => {
        const v = collect();
        const label = `${v.ime_prezime || v.dijete || v.mladenci || v.pokojnik || v.osoba || "Obrazac"} — ${form.name} — ${v.danas}`;
        const list = loadSaved();
        list.unshift({ id: `sf_${Date.now()}`, formId: form.id, label, values: v });
        saveSaved(list.slice(0, 50));
        api.showToast("Spremljeno");
        render();
      });

      root.querySelector("#zf-saved-open")?.addEventListener("change", (e) => {
        const id = e.target.value;
        if (!id) return;
        const item = loadSaved().find((s) => s.id === id);
        if (!item) return;
        formId = item.formId;
        cat = FORMS.find((f) => f.id === formId)?.cat || cat;
        render();
        setTimeout(() => {
          Object.entries(item.values || {}).forEach(([k, val]) => {
            const inp = root.querySelector(`[data-zf-field="${k}"]`);
            if (inp) inp.value = val;
          });
        }, 0);
      });
    }

    render();
  }

  global.PastoralZupniForms = { FORMS, CATEGORIES, mountFormulariPage, loadSaved };
})(typeof window !== "undefined" ? window : global);
