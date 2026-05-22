/**
 * Potvrde i isprave — iz evidencije župe (bez Excela)
 */
(function (global) {
  function fmtHr(iso) {
    if (!iso) return "—";
    return new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  const SOURCES = [
    {
      id: "krizma",
      label: "Sv. Potvrda (krizmanik)",
      templateId: "pristupnica_krizma",
      list(data) {
        const out = [];
        (data.confirmations || []).forEach((g) => {
          (g.candidates || []).forEach((c) => {
            out.push({
              key: `${g.year}:${c.id}`,
              label: `${c.name} (${g.year})`,
              group: g,
              record: c,
            });
          });
        });
        return out;
      },
      values(item, parish) {
        const g = item.group;
        const c = item.record;
        return {
          ime_prezime: c.name,
          datum_rodjenja: fmtHr(c.birthDate),
          datum_krstenja: fmtHr(c.baptized),
          kum: c.sponsor || "—",
          datum_potvrde: fmtHr(g.ceremonyDate),
          zupnik: parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
    {
      id: "krsenje",
      label: "Krštenje",
      templateId: "potvrda_krsenja",
      list(data) {
        return (data.baptisms || []).map((b) => ({
          key: b.id,
          label: `${b.childName} — ${fmtHr(b.baptismDate)}`,
          record: b,
        }));
      },
      values(item, parish) {
        const b = item.record;
        return {
          ime_djeteta: b.childName,
          datum_krstenja: fmtHr(b.baptismDate),
          roditelji: b.parents || "—",
          kumovi: b.godparents || "—",
          maticni_broj: b.registryNo || "—",
          zupnik: b.celebrant || parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
    {
      id: "prva-pricest",
      label: "Prva sv. Pričest",
      templateId: "potvrda_pricest",
      list(data) {
        const out = [];
        (data.firstCommunion || []).forEach((g) => {
          (g.candidates || []).forEach((c) => {
            out.push({
              key: `${g.id}:${c.id}`,
              label: `${c.name} — ${g.groupName || g.year}`,
              group: g,
              record: c,
            });
          });
        });
        return out;
      },
      values(item, parish) {
        const g = item.group;
        const c = item.record;
        return {
          ime_prezime: c.name,
          datum_pricesti: fmtHr(g.ceremonyDate),
          skupina: `${g.groupName || ""} (${g.year})`.trim(),
          roditelji: c.parents || "—",
          zupnik: g.celebrant || parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
    {
      id: "vjencanje",
      label: "Vjenčanje",
      templateId: "potvrda_vjencanja",
      list(data) {
        return (data.weddings || []).map((w) => ({
          key: w.id,
          label: `${w.couple} — ${fmtHr(w.weddingDate)}`,
          record: w,
        }));
      },
      values(item, parish) {
        const w = item.record;
        return {
          mladenci: w.couple,
          datum_vjencanja: fmtHr(w.weddingDate),
          svjedoci: w.witnesses || "—",
          zupnik: w.celebrant || parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
    {
      id: "pogreb",
      label: "Pogreb",
      templateId: "potvrda_pogreba",
      list(data) {
        return (data.funerals || []).map((f) => ({
          key: f.id,
          label: `${f.deceased} — ${fmtHr(f.funeralDate)}`,
          record: f,
        }));
      },
      values(item, parish) {
        const f = item.record;
        return {
          pokojnik: f.deceased,
          datum_smrti: fmtHr(f.deathDate),
          datum_pogreba: fmtHr(f.funeralDate),
          groblje: f.cemetery || "—",
          zupnik: f.celebrant || parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
    {
      id: "lukno",
      label: "Župno lukno (obitelj)",
      templateId: "potvrda_lukno",
      list(data) {
        const out = [];
        (data.families || []).forEach((fam) => {
          (fam.contributions || []).forEach((c) => {
            if (!c.luknoPaid) return;
            out.push({
              key: `${fam.id}:${c.year}`,
              label: `${fam.surname} — lukno ${c.year}`,
              family: fam,
              contribution: c,
            });
          });
        });
        return out;
      },
      values(item, parish) {
        const fam = item.family;
        const c = item.contribution;
        return {
          obitelj: `Obitelj ${fam.surname}`,
          adresa: fam.address || "—",
          godina: String(c.year),
          iznos: String(c.luknoAmount ?? 150),
          datum_uplate: fmtHr(c.luknoPaidAt),
          zupnik: parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
    {
      id: "nakane",
      label: "Misna nakana",
      templateId: "potvrda_nakane",
      list(data) {
        return (data.intentions || []).map((n) => ({
          key: n.id,
          label: `${n.intentionFor} — ${fmtHr(n.date)} ${n.massTime || ""}`,
          record: n,
        }));
      },
      values(item, parish) {
        const n = item.record;
        return {
          namjera: n.intentionFor,
          datum_mise: fmtHr(n.date),
          vrijeme_mise: n.massTime || "—",
          narucitelj: n.requestedBy || "—",
          stipendij: String(n.stipend ?? 0),
          zupnik: parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
    {
      id: "uplata",
      label: "Opća potvrda uplate",
      templateId: "potvrda_uplate",
      list(data) {
        return (data.invoices || [])
          .filter((inv) => inv.status === "placen" || inv.paidAmount > 0)
          .map((inv) => ({
            key: inv.id,
            label: `${inv.number} — ${inv.payerName}`,
            record: inv,
          }));
      },
      values(item, parish) {
        const inv = item.record;
        return {
          platitelj: inv.payerName,
          svrha: inv.description,
          iznos: String(inv.total ?? inv.amount),
          datum_uplate: fmtHr(inv.paidAt || inv.issueDate),
          broj_racuna: inv.number,
          zupnik: parish.pastor,
          zupa: parish.name,
          danas: new Date().toLocaleDateString("hr-HR"),
        };
      },
    },
  ];

  function getSource(id) {
    return SOURCES.find((s) => s.id === id);
  }

  function mountPotvrdePage(root, api) {
    if (!root) return;
    const Doc = global.PastoralDocuments;
    const esc = api.escapeHtml;
    let sourceId = new URLSearchParams(location.search).get("vrsta") || "krizma";
    let recordKey = "";

    function render() {
      const data = api.getData();
      const parish = api.getSettings();
      const src = getSource(sourceId) || SOURCES[0];
      const items = src.list(data);
      if (!recordKey && items[0]) recordKey = items[0].key;

      root.innerHTML = `
        <div class="potvrde-layout">
          <section class="card potvrde-sidebar">
            <h2 class="section-title">Vrsta potvrde</h2>
            <div class="potvrde-type-list">
              ${SOURCES.map(
                (s) =>
                  `<button type="button" class="potvrde-type-btn ${s.id === sourceId ? "is-active" : ""}" data-src="${s.id}">${esc(s.label)}</button>`
              ).join("")}
            </div>
            <p class="card-sub" style="margin-top:16px">Za serijski ispis iz Excela koristite <a href="${api.pageUrl("pages/dokumenti.html")}">Dokumente</a>.</p>
          </section>
          <section class="card potvrde-main">
            <h2 class="section-title">${esc(src.label)}</h2>
            <div class="form-group form-wide">
              <label>Zapis iz evidencije</label>
              <select id="potvrda-record-select">
                ${items.length
                  ? items
                      .map((it) => `<option value="${esc(it.key)}" ${it.key === recordKey ? "selected" : ""}>${esc(it.label)}</option>`)
                      .join("")
                  : '<option value="">— nema zapisa —</option>'}
              </select>
            </div>
            <div class="quick-actions">
              <button type="button" class="btn btn-primary" id="potvrda-preview-btn">Osvježi pregled</button>
              <button type="button" class="btn btn-secondary" id="potvrda-print-btn">🖨 Ispis / PDF</button>
            </div>
            <div id="potvrda-preview-box" class="doc-preview-box potvrda-preview"></div>
          </section>
        </div>
        <section class="card" style="margin-top:16px">
          <h2 class="section-title">Svi predlošci potvrda</h2>
          <ul class="doc-bindings-list">
            ${(Doc?.getCertificateTemplates?.() || [])
              .map((t) => `<li><strong>${esc(t.name)}</strong> <span class="badge">${esc(t.category)}</span></li>`)
              .join("")}
          </ul>
        </section>`;

      function updatePreview() {
        const box = root.querySelector("#potvrda-preview-box");
        const tpl = Doc?.getTemplate(src.templateId);
        const item = items.find((it) => it.key === recordKey);
        if (!box || !tpl || !item) {
          if (box) box.innerHTML = '<p class="empty-state">Odaberite zapis ili dodajte evidenciju.</p>';
          return;
        }
        const values = src.values(item, parish);
        box.innerHTML = Doc.mergeTemplate(tpl.body, values);
      }

      root.querySelectorAll(".potvrde-type-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          sourceId = btn.dataset.src;
          recordKey = "";
          render();
        });
      });
      root.querySelector("#potvrda-record-select")?.addEventListener("change", (e) => {
        recordKey = e.target.value;
        updatePreview();
      });
      root.querySelector("#potvrda-preview-btn")?.addEventListener("click", updatePreview);
      root.querySelector("#potvrda-print-btn")?.addEventListener("click", () => {
        updatePreview();
        const tpl = Doc.getTemplate(src.templateId);
        const html = root.querySelector("#potvrda-preview-box")?.innerHTML;
        if (tpl && html) Doc.printHtml(html, tpl.name);
      });

      updatePreview();
    }

    render();
  }

  global.PastoralPotvrde = { SOURCES, getSource, mountPotvrdePage };
})(typeof window !== "undefined" ? window : global);
