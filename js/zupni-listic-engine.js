/**
 * Župni listić — predložak (HTML), unos po poljima, povijest izdanja
 */
(function (global) {
  const DEFAULT_TEMPLATE = {
    fileName: "zupni-listic-zadani.html",
    updatedAt: null,
    html: `<div class="listic-print-doc">
  <header class="listic-print-header">
    <p class="listic-print-meta">{{biskupija}}</p>
    <h1>{{zupa}}</h1>
    <p class="listic-print-week">{{grad}} · tjedan {{tjedan_od}} – {{tjedan_do}}</p>
    <p class="listic-print-pastor">Župnik: {{zupnik}}</p>
    <p class="listic-print-liturgy"><em>Liturgijska boja:</em> {{liturgijska_boja}}</p>
  </header>

  <section class="listic-print-block">
    <h2>Raspored sv. misa</h2>
    <div class="listic-print-body">{{misni_raspored}}</div>
  </section>

  <section class="listic-print-block">
    <h2>Molitvene nakane</h2>
    <div class="listic-print-body">{{nakane_tjedan}}</div>
  </section>

  <section class="listic-print-block">
    <h2>Obavijesti župe</h2>
    <div class="listic-print-body">{{obavijesti_zupe}}</div>
  </section>

  <section class="listic-print-block">
    <h2>Kateheza i pobožnosti</h2>
    <div class="listic-print-body">{{kateheza_pobožnosti}}</div>
  </section>

  <section class="listic-print-block">
    <h2>Sakramenti i događaji</h2>
    <div class="listic-print-body">{{sakramenti_dogadaji}}</div>
  </section>

  <section class="listic-print-block">
    <h2>Župni ured</h2>
    <div class="listic-print-body">{{kontakt_ured}}</div>
  </section>

  <footer class="listic-print-footer">
    <p>{{napomena_listica}}</p>
    <p><small>Izdano: {{datum_izdavanja}}</small></p>
  </footer>
</div>`,
  };

  const FIELD_LABELS = {
    biskupija: "Biskupija / nadbiskupija",
    zupa: "Naziv župe",
    grad: "Mjesto",
    zupnik: "Župnik",
    tjedan_od: "Tjedan od",
    tjedan_do: "Tjedan do",
    liturgijska_boja: "Liturgijska boja",
    misni_raspored: "Raspored misa",
    nakane_tjedan: "Nakane (tjedan)",
    obavijesti_zupe: "Obavijesti župe",
    kateheza_pobožnosti: "Kateheza i pobožnosti",
    sakramenti_dogadaji: "Sakramenti i događaji",
    kontakt_ured: "Kontakt župnog ureda",
    napomena_listica: "Napomena na listiću",
    datum_izdavanja: "Datum izdavanja",
    tablica_nakana: "Tablica nakana (HTML)",
  };

  function weekStartFrom(iso) {
    if (global.PastoralBulletin?.weekStartFrom) return global.PastoralBulletin.weekStartFrom(iso);
    const d = new Date((iso || new Date().toISOString().slice(0, 10)) + "T12:00:00");
    const day = (d.getDay() + 6) % 7;
    d.setDate(d.getDate() - day);
    return d.toISOString().slice(0, 10);
  }

  function weekEndFrom(start) {
    const d = new Date(start + "T12:00:00");
    d.setDate(d.getDate() + 6);
    return d.toISOString().slice(0, 10);
  }

  function fmtShort(iso) {
    return new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
  }

  function extractPlaceholders(html) {
    const keys = new Set();
    const re = /\{\{(\w+)\}\}/g;
    let m;
    while ((m = re.exec(html || ""))) keys.add(m[1]);
    return [...keys];
  }

  function mergeTemplate(html, values) {
    if (global.PastoralDocuments?.mergeTemplate) {
      return global.PastoralDocuments.mergeTemplate(html, values);
    }
    let out = html || "";
    Object.entries(values || {}).forEach(([k, v]) => {
      out = out.split(`{{${k}}}`).join(String(v ?? ""));
    });
    return out.replace(/\{\{[^}]+\}\}/g, "—");
  }

  function getTemplate(data) {
    const t = data.zupniListicTemplate;
    if (t?.html) return { ...DEFAULT_TEMPLATE, ...t };
    return { ...DEFAULT_TEMPLATE };
  }

  function labelForField(key) {
    return FIELD_LABELS[key] || key.replace(/_/g, " ");
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatMassSchedule(data) {
    const rows = data.massSchedule || [];
    if (!rows.length) return "<p>Raspored misa nije unesen u postavkama.</p>";
    return `<ul class="listic-ul">${rows
      .map((m) => `<li><strong>${escapeHtml(m.day)}</strong> — ${escapeHtml(m.time)}</li>`)
      .join("")}</ul>`;
  }

  function formatNakaneHtml(data, weekStart) {
    const start = weekStartFrom(weekStart);
    const end = weekEndFrom(start);
    const rows = (data.intentions || [])
      .filter((n) => n.date >= start && n.date <= end)
      .sort((a, b) => (a.date + a.massTime).localeCompare(b.date + b.massTime));
    if (!rows.length) return "<p>U tom tjednu nema upisanih nakana.</p>";
    const body = rows
      .map(
        (n) =>
          `<tr><td>${fmtShort(n.date)}</td><td>${escapeHtml(n.massTime)}</td><td>${escapeHtml(n.intentionFor)}</td><td>${escapeHtml(n.requestedBy || "—")}</td></tr>`
      )
      .join("");
    return `<table class="listic-table" border="1" cellpadding="6" style="width:100%;border-collapse:collapse">
      <thead><tr><th>Dan</th><th>Misa</th><th>Namjera</th><th>Naručitelj</th></tr></thead>
      <tbody>${body}</tbody></table>`;
  }

  function formatAnnouncements(data) {
    const items = (data.announcements || []).slice(0, 6);
    if (!items.length) return "<p>Nema aktivnih obavijesti — unesite u modulu Obavijesti.</p>";
    return `<ul class="listic-ul">${items
      .map((a) => `<li><strong>${escapeHtml(a.title)}</strong><br>${escapeHtml(a.body)}</li>`)
      .join("")}</ul>`;
  }

  function formatSacramentsAndEvents(data, weekStart, weekEnd) {
    const lines = [];
    (data.baptisms || [])
      .filter((b) => b.baptismDate && b.baptismDate >= weekStart && b.baptismDate <= weekEnd)
      .forEach((b) => lines.push(`Krštenje: ${b.childName} — ${fmtShort(b.baptismDate)}`));
    (data.weddings || [])
      .filter((w) => w.weddingDate && w.weddingDate >= weekStart && w.weddingDate <= weekEnd)
      .forEach((w) => lines.push(`Vjenčanje: ${w.couple} — ${fmtShort(w.weddingDate)}`));
    (data.funerals || [])
      .filter((f) => f.funeralDate && f.funeralDate >= weekStart && f.funeralDate <= weekEnd)
      .forEach((f) => lines.push(`Pogreb: ${f.deceased} — ${fmtShort(f.funeralDate)}`));
    (data.events || [])
      .filter((e) => e.date && e.date >= weekStart && e.date <= weekEnd)
      .forEach((e) => lines.push(`${e.title} — ${fmtShort(e.date)} (${escapeHtml(e.place || "")})`));
    if (!lines.length) return "<p>Nema sakramenata ni događaja u ovom tjednu.</p>";
    return `<ul class="listic-ul">${lines.map((l) => `<li>${escapeHtml(l)}</li>`).join("")}</ul>`;
  }

  function liturgicalColorHint(iso) {
    const d = new Date(iso + "T12:00:00");
    const day = d.getDay();
    if (day === 0) return "Zelena (ili liturgija dana)";
    if (day === 5) return "Ljubičasta / crvena (petak)";
    return "Zelena (ferija)";
  }

  function buildAutoValues(data, settings, weekStart) {
    const start = weekStartFrom(weekStart);
    const end = weekEndFrom(start);
    const today = new Date().toISOString().slice(0, 10);
    return {
      biskupija: settings.diocese || "",
      zupa: settings.name || "",
      grad: settings.city || "",
      zupnik: settings.pastor || "",
      tjedan_od: fmtShort(start),
      tjedan_do: fmtShort(end),
      liturgijska_boja: liturgicalColorHint(start),
      misni_raspored: formatMassSchedule(data),
      nakane_tjedan: formatNakaneHtml(data, start),
      tablica_nakana: formatNakaneHtml(data, start),
      obavijesti_zupe: formatAnnouncements(data),
      kateheza_pobožnosti:
        "<p>Kateheza: provjerite raspored skupina u modulu Krizma / Prva pričest.</p><p>Pobožnosti: korizmeni program prema župnom kalendaru.</p>",
      sakramenti_dogadaji: formatSacramentsAndEvents(data, start, end),
      kontakt_ured: `<p>Tel. ${escapeHtml(settings.phone || "—")}<br>E-mail: ${escapeHtml(settings.email || "—")}<br>${escapeHtml(settings.address || "")}</p>`,
      napomena_listica: "Župni listić — izdanje za župljane. Molimo za molitvenu naknadu za župu.",
      datum_izdavanja: new Date().toLocaleDateString("hr-HR"),
    };
  }

  function defaultData() {
    const start = weekStartFrom();
    const end = weekEndFrom(start);
    return {
      zupniListicTemplate: { ...DEFAULT_TEMPLATE, updatedAt: new Date().toISOString() },
      zupniListicIssues: [
        {
          id: "listic_demo_1",
          weekStart: start,
          weekEnd: end,
          title: `Listić ${fmtShort(start)} – ${fmtShort(end)}`,
          status: "izdan",
          values: {},
          createdAt: new Date(Date.now() - 86400000 * 7).toISOString(),
          createdBy: "demo",
        },
      ],
    };
  }

  function migrate(data, settings) {
    const def = defaultData();
    if (!data.zupniListicTemplate?.html) {
      data.zupniListicTemplate = def.zupniListicTemplate;
    }
    if (!Array.isArray(data.zupniListicIssues)) data.zupniListicIssues = [];
    if (!data.zupniListicIssues.length && settings) {
      const vals = buildAutoValues(data, settings, weekStartFrom());
      const tpl = getTemplate(data);
      data.zupniListicIssues = [
        {
          id: "listic_demo_1",
          weekStart: weekStartFrom(),
          weekEnd: weekEndFrom(weekStartFrom()),
          title: `Listić ${vals.tjedan_od} – ${vals.tjedan_do}`,
          status: "izdan",
          values: vals,
          renderedHtml: mergeTemplate(tpl.html, vals),
          createdAt: new Date(Date.now() - 86400000 * 7).toISOString(),
          createdBy: "demo",
        },
      ];
    }
    return data;
  }

  function printHtml(html, title) {
    if (global.PastoralDocuments?.printHtml) {
      global.PastoralDocuments.printHtml(html, title);
      return;
    }
    const w = window.open("", "_blank");
    if (!w) {
      alert("Omogućite skočne prozore za ispis.");
      return;
    }
    w.document.write(
      `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${escapeHtml(title || "Župni listić")}</title>
      <link rel="stylesheet" href="${location.pathname.includes("/pages/") ? "../" : ""}css/styles.css">
      <style>body{padding:24px;max-width:720px;margin:0 auto} @media print{.no-print{display:none}}</style></head><body>${html}
      <p class="no-print" style="margin-top:2em"><button onclick="window.print()">Ispis</button></p></body></html>`
    );
    w.document.close();
  }

  function mountZupniListicPage(root, api) {
    if (!root) return;
    const esc = api.escapeHtml;
    let activeTab = "edit";
    let editValues = {};
    let editingIssueId = null;
    let weekStart = weekStartFrom();

    function getData() {
      return migrate(api.getData(), api.getSettings?.() || {});
    }

    function saveData(data) {
      api.saveData(data);
    }

    function readFormValues() {
      const tpl = getTemplate(getData());
      const keys = extractPlaceholders(tpl.html);
      const values = {};
      keys.forEach((k) => {
        const el = root.querySelector(`[data-listic-field="${k}"]`);
        values[k] = el ? el.value : editValues[k] || "";
      });
      return values;
    }

    function fillForm(values) {
      const tpl = getTemplate(getData());
      extractPlaceholders(tpl.html).forEach((k) => {
        const el = root.querySelector(`[data-listic-field="${k}"]`);
        if (el) el.value = values[k] ?? "";
      });
      editValues = { ...values };
      updatePreview();
    }

    function updatePreview() {
      const box = root.querySelector("#listic-preview");
      if (!box) return;
      const tpl = getTemplate(getData());
      const values = readFormValues();
      box.innerHTML = mergeTemplate(tpl.html, values);
    }

    function renderFieldsForm() {
      const tpl = getTemplate(getData());
      const keys = extractPlaceholders(tpl.html);
      return keys
        .map((k) => {
          const isLong = /raspored|nakane|obavijest|kateheza|sakrament|kontakt|napomena|tablica/i.test(k);
          const val = editValues[k] ?? "";
          if (isLong) {
            return `<div class="form-group"><label>${esc(labelForField(k))} <code>{{${k}}}</code></label>
              <textarea rows="4" data-listic-field="${k}">${esc(val)}</textarea></div>`;
          }
          return `<div class="form-group"><label>${esc(labelForField(k))} <code>{{${k}}}</code></label>
            <input type="text" data-listic-field="${k}" value="${esc(val)}" /></div>`;
        })
        .join("");
    }

    function render() {
      const data = getData();
      const settings = api.getSettings?.() || {};
      const tpl = getTemplate(data);
      const placeholders = extractPlaceholders(tpl.html);
      const issues = [...(data.zupniListicIssues || [])].sort(
        (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
      );

      root.innerHTML = `
        <div class="listic-tabs card" role="tablist">
          <button type="button" class="listic-tab ${activeTab === "edit" ? "is-active" : ""}" data-tab="edit">Novi listić</button>
          <button type="button" class="listic-tab ${activeTab === "template" ? "is-active" : ""}" data-tab="template">Predložak</button>
          <button type="button" class="listic-tab ${activeTab === "history" ? "is-active" : ""}" data-tab="history">Povijest (${issues.length})</button>
        </div>

        <div class="listic-panel ${activeTab === "edit" ? "" : "hidden"}" data-panel="edit">
          <div class="listic-layout">
            <section class="card listic-form-card">
              <h2 class="section-title">Podaci za listić</h2>
              <p class="card-sub">Polja odgovaraju oznakama <code>{{naziv}}</code> u predlošku. Automatski popuni iz župnih podataka.</p>
              <div class="listic-week-row">
                <div class="form-group">
                  <label>Tjedan (ponedjeljak)</label>
                  <input type="date" id="listic-week-start" value="${weekStart}" />
                </div>
                <button type="button" class="btn btn-secondary btn-sm" id="listic-autofill">Popuni iz podataka</button>
              </div>
              <div id="listic-fields" class="listic-fields-grid">${renderFieldsForm()}</div>
              <div class="listic-actions">
                <button type="button" class="btn btn-primary" id="listic-save-issue">Spremi u povijest</button>
                <button type="button" class="btn btn-secondary" id="listic-print-btn">Ispis / PDF</button>
                ${editingIssueId ? `<button type="button" class="btn btn-ghost" id="listic-cancel-edit">Novi (prazno)</button>` : ""}
              </div>
            </section>
            <section class="card listic-preview-card">
              <h2 class="section-title">Pregled</h2>
              <div id="listic-preview" class="listic-preview"></div>
            </section>
          </div>
        </div>

        <div class="listic-panel ${activeTab === "template" ? "" : "hidden"}" data-panel="template">
          <div class="listic-layout listic-layout--template">
            <section class="card">
              <h2 class="section-title">Predložak župnog listića</h2>
              <p class="card-sub">Učitajte vlastiti HTML (.html) s oznakama <code>{{polje}}</code> ili uredite zadani predložak.</p>
              <p class="card-sub"><strong>Trenutno:</strong> ${esc(tpl.fileName || "zadani")} · ${placeholders.length} polja · ažurirano: ${tpl.updatedAt ? new Date(tpl.updatedAt).toLocaleString("hr-HR") : "—"}</p>
              <div class="listic-template-actions">
                <label class="btn btn-secondary btn-sm" style="cursor:pointer">
                  Učitaj predložak
                  <input type="file" id="listic-upload" accept=".html,.htm,text/html" hidden />
                </label>
                <button type="button" class="btn btn-ghost btn-sm" id="listic-reset-template">Vrati zadani</button>
                <button type="button" class="btn btn-ghost btn-sm" id="listic-detect-fields">Osvježi polja u obrascu</button>
              </div>
              <details class="listic-placeholders-hint">
                <summary>Polja u predlošku (${placeholders.length})</summary>
                <p class="card-sub">${placeholders.map((p) => `<code>{{${p}}}</code>`).join(" · ") || "—"}</p>
              </details>
              <div class="form-group" style="margin-top:16px">
                <label>HTML predloška</label>
                <textarea id="listic-template-html" rows="14" class="listic-template-editor">${esc(tpl.html)}</textarea>
              </div>
              <button type="button" class="btn btn-primary" id="listic-save-template">Spremi predložak</button>
            </section>
            <section class="card">
              <h2 class="section-title">Pregled predloška</h2>
              <div id="listic-template-preview" class="listic-preview listic-preview--muted"></div>
            </section>
          </div>
        </div>

        <div class="listic-panel ${activeTab === "history" ? "" : "hidden"}" data-panel="history">
          <section class="card">
            <h2 class="section-title">Povijest izdanih listića</h2>
            ${
              issues.length
                ? `<div class="table-wrap"><table class="data-table listic-history-table">
              <thead><tr><th>Tjedan</th><th>Naslov</th><th>Status</th><th>Datum</th><th></th></tr></thead>
              <tbody>
                ${issues
                  .map((issue) => {
                    const wk = `${fmtShort(issue.weekStart)} – ${fmtShort(issue.weekEnd)}`;
                    const dt = issue.createdAt
                      ? new Date(issue.createdAt).toLocaleString("hr-HR", { dateStyle: "short", timeStyle: "short" })
                      : "—";
                    return `<tr>
                      <td>${esc(wk)}</td>
                      <td><strong>${esc(issue.title || wk)}</strong></td>
                      <td><span class="badge ${issue.status === "nacrt" ? "badge-pending" : "badge-done"}">${issue.status === "nacrt" ? "nacrt" : "izdan"}</span></td>
                      <td>${esc(dt)}</td>
                      <td class="listic-history-actions">
                        <button type="button" class="btn btn-ghost btn-sm" data-listic-view="${esc(issue.id)}">Pregled</button>
                        <button type="button" class="btn btn-ghost btn-sm" data-listic-edit="${esc(issue.id)}">Uredi</button>
                        <button type="button" class="btn btn-ghost btn-sm" data-listic-print-id="${esc(issue.id)}">Ispis</button>
                        <button type="button" class="btn btn-ghost btn-sm" data-listic-del="${esc(issue.id)}">Obriši</button>
                      </td>
                    </tr>`;
                  })
                  .join("")}
              </tbody>
            </table></div>`
                : `<div class="empty-state ui-empty-fancy"><p>Još nema spremljenih listića. Kreirajte prvi u kartici „Novi listić”.</p></div>`
            }
          </section>
        </div>`;

      bindEvents(data, settings, tpl);
      if (activeTab === "edit") {
        if (!Object.keys(editValues).length) {
          editValues = buildAutoValues(data, settings, weekStart);
          fillForm(editValues);
        } else updatePreview();
      }
      if (activeTab === "template") refreshTemplatePreview();
    }

    function refreshTemplatePreview() {
      const box = root.querySelector("#listic-template-preview");
      const html = root.querySelector("#listic-template-html")?.value || getTemplate(getData()).html;
      if (!box) return;
      const sample = buildAutoValues(getData(), api.getSettings?.() || {}, weekStart);
      box.innerHTML = mergeTemplate(html, sample);
    }

    function bindEvents(data, settings, tpl) {
      root.querySelectorAll(".listic-tab").forEach((btn) => {
        btn.addEventListener("click", () => {
          activeTab = btn.dataset.tab;
          render();
        });
      });

      root.querySelector("#listic-week-start")?.addEventListener("change", (e) => {
        weekStart = e.target.value || weekStartFrom();
        const end = weekEndFrom(weekStart);
        if (editValues.tjedan_od !== undefined) {
          editValues.tjedan_od = fmtShort(weekStart);
          editValues.tjedan_do = fmtShort(end);
          fillForm(editValues);
        }
      });

      root.querySelector("#listic-fields")?.addEventListener("input", (e) => {
        if (e.target.matches("[data-listic-field]")) {
          editValues[e.target.dataset.listicField] = e.target.value;
          updatePreview();
        }
      });

      root.querySelector("#listic-autofill")?.addEventListener("click", () => {
        weekStart = root.querySelector("#listic-week-start")?.value || weekStartFrom();
        editValues = buildAutoValues(getData(), settings, weekStart);
        fillForm(editValues);
        api.showToast?.("Podaci učitani iz župe");
      });

      root.querySelector("#listic-print-btn")?.addEventListener("click", () => {
        const values = readFormValues();
        const html = mergeTemplate(getTemplate(getData()).html, values);
        printHtml(html, `Župni listić ${values.tjedan_od || ""}`);
      });

      root.querySelector("#listic-save-issue")?.addEventListener("click", () => {
        const d = getData();
        const values = readFormValues();
        const ws = root.querySelector("#listic-week-start")?.value || weekStartFrom();
        const we = weekEndFrom(ws);
        const html = mergeTemplate(getTemplate(d).html, values);
        const title = `Listić ${fmtShort(ws)} – ${fmtShort(we)}`;
        const id = editingIssueId || api.uid?.("listic") || `listic_${Date.now()}`;
        const issue = {
          id,
          weekStart: ws,
          weekEnd: we,
          title,
          status: "izdan",
          values,
          renderedHtml: html,
          createdAt: editingIssueId
            ? d.zupniListicIssues.find((x) => x.id === editingIssueId)?.createdAt || new Date().toISOString()
            : new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        const list = d.zupniListicIssues.filter((x) => x.id !== id);
        list.unshift(issue);
        d.zupniListicIssues = list;
        saveData(d);
        editingIssueId = id;
        api.showToast?.("Listić spremljen u povijest");
        activeTab = "history";
        render();
      });

      root.querySelector("#listic-cancel-edit")?.addEventListener("click", () => {
        editingIssueId = null;
        editValues = buildAutoValues(getData(), settings, weekStart);
        fillForm(editValues);
        render();
      });

      root.querySelector("#listic-save-template")?.addEventListener("click", () => {
        const html = root.querySelector("#listic-template-html")?.value || "";
        if (!extractPlaceholders(html).length) {
          api.showToast?.("Predložak mora imati barem jednu oznaku {{polje}}");
          return;
        }
        const d = getData();
        d.zupniListicTemplate = {
          html,
          fileName: d.zupniListicTemplate?.fileName || "uredeno.html",
          updatedAt: new Date().toISOString(),
        };
        saveData(d);
        editValues = {};
        api.showToast?.("Predložak spremljen");
        render();
      });

      root.querySelector("#listic-reset-template")?.addEventListener("click", () => {
        if (!confirm("Vratiti zadani predložak župnog listića?")) return;
        const d = getData();
        d.zupniListicTemplate = { ...DEFAULT_TEMPLATE, updatedAt: new Date().toISOString() };
        saveData(d);
        editValues = {};
        api.showToast?.("Zadani predložak učitan");
        render();
      });

      root.querySelector("#listic-detect-fields")?.addEventListener("click", () => {
        activeTab = "edit";
        editValues = readFormValues();
        render();
        api.showToast?.("Polja osvježena prema predlošku");
      });

      root.querySelector("#listic-upload")?.addEventListener("change", (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          const html = String(reader.result || "");
          if (!extractPlaceholders(html).length) {
            api.showToast?.("Datoteka mora sadržavati {{polja}}");
            return;
          }
          const d = getData();
          d.zupniListicTemplate = { html, fileName: file.name, updatedAt: new Date().toISOString() };
          saveData(d);
          editValues = {};
          api.showToast?.(`Učitano: ${file.name}`);
          render();
        };
        reader.readAsText(file, "UTF-8");
        e.target.value = "";
      });

      root.querySelector("#listic-template-html")?.addEventListener("input", refreshTemplatePreview);

      root.querySelectorAll("[data-listic-view]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const issue = getData().zupniListicIssues.find((x) => x.id === btn.dataset.listicView);
          if (!issue) return;
          const html = issue.renderedHtml || mergeTemplate(getTemplate(getData()).html, issue.values || {});
          global.PastoralModal?.openDetail?.({
            title: issue.title || "Župni listić",
            body: `<div class="listic-preview listic-preview--modal">${html}</div>`,
            size: "xl",
          });
        });
      });

      root.querySelectorAll("[data-listic-edit]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const issue = getData().zupniListicIssues.find((x) => x.id === btn.dataset.listicEdit);
          if (!issue) return;
          editingIssueId = issue.id;
          weekStart = issue.weekStart || weekStartFrom();
          editValues = { ...(issue.values || {}) };
          activeTab = "edit";
          render();
          fillForm(editValues);
          const ws = root.querySelector("#listic-week-start");
          if (ws) ws.value = weekStart;
        });
      });

      root.querySelectorAll("[data-listic-print-id]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const issue = getData().zupniListicIssues.find((x) => x.id === btn.dataset.listicPrintId);
          if (!issue) return;
          const html = issue.renderedHtml || mergeTemplate(getTemplate(getData()).html, issue.values || {});
          printHtml(html, issue.title || "Župni listić");
        });
      });

      root.querySelectorAll("[data-listic-del]").forEach((btn) => {
        btn.addEventListener("click", () => {
          if (!confirm("Obrisati ovaj listić iz povijesti?")) return;
          const d = getData();
          d.zupniListicIssues = d.zupniListicIssues.filter((x) => x.id !== btn.dataset.listicDel);
          saveData(d);
          if (editingIssueId === btn.dataset.listicDel) editingIssueId = null;
          api.showToast?.("Obrisano");
          render();
        });
      });
    }

    editValues = buildAutoValues(getData(), api.getSettings?.() || {}, weekStart);
    render();
  }

  global.PastoralZupniListic = {
    DEFAULT_TEMPLATE,
    FIELD_LABELS,
    migrate,
    getTemplate,
    extractPlaceholders,
    mergeTemplate,
    buildAutoValues,
    mountZupniListicPage,
    printHtml,
    weekStartFrom,
  };
})(typeof window !== "undefined" ? window : global);
