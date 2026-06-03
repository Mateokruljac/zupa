/**
 * Župni listić — sastavljanje blokova (rich text), povijest izdanja
 */
(function (global) {
  const BLOCK_TYPES = {
    header: { label: "Zaglavlje", desc: "Naziv župe, tjedan, župnik — automatski iz postavki", auto: true, fixed: true },
    mass_schedule: { label: "Raspored misa", desc: "Automatski iz modula Mise", auto: true },
    nakane: { label: "Molitvene nakane", desc: "Automatski iz kalendara nakana za tjedan", auto: true },
    announcements: { label: "Obavijesti župe", desc: "Automatski iz modula Obavijesti", auto: true },
    custom_text: { label: "Slobodni tekst", desc: "Naslov i oblikovani tekst", auto: false },
    sacraments: { label: "Sakramenti i događaji", desc: "Krštenja, vjenčanja, pogrebi, događaji", auto: true },
    contact: { label: "Kontakt ureda", desc: "Telefon, e-mail i adresa župe", auto: true },
    footer: { label: "Podnožje", desc: "Kratka oblikovana napomena na dnu listića", auto: false, fixed: true },
  };

  const DEFAULT_LAYOUT = {
    blocks: [
      { id: "blk_hdr", type: "header", enabled: true },
      { id: "blk_ms", type: "mass_schedule", enabled: true, title: "Raspored sv. misa" },
      { id: "blk_nk", type: "nakane", enabled: true, title: "Molitvene nakane" },
      { id: "blk_ob", type: "announcements", enabled: true, title: "Obavijesti župe" },
      {
        id: "blk_kt",
        type: "custom_text",
        enabled: true,
        title: "Kateheza i pobožnosti",
        body: "Kateheza: provjerite raspored skupina u modulu Krizma / Prva pričest.\n\nPobožnosti: korizmeni program prema župnom kalendaru.",
      },
      { id: "blk_sk", type: "sacraments", enabled: true, title: "Sakramenti i događaji" },
      { id: "blk_ku", type: "contact", enabled: true, title: "Župni ured" },
      {
        id: "blk_ft",
        type: "footer",
        enabled: true,
        title: "",
        body: "Župni listić — izdanje za župljane. Molimo za molitvenu naknadu za župu.",
      },
    ],
    updatedAt: null,
  };

  const DEFAULT_TEMPLATE = {
    fileName: "zupni-listic-zadani.html",
    updatedAt: null,
    html: "",
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

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function plainTextToHtml(text) {
    const t = String(text ?? "").trim();
    if (!t) return "<p>—</p>";
    return t
      .split(/\n\s*\n/)
      .map((p) => `<p>${escapeHtml(p.trim()).replace(/\n/g, "<br>")}</p>`)
      .join("");
  }

  function renderRichBody(htmlOrText) {
    const RTE = global.PastoralRichText;
    if (RTE?.renderBodyHtml) return RTE.renderBodyHtml(htmlOrText);
    return plainTextToHtml(htmlOrText);
  }

  function cloneLayout(layout) {
    return JSON.parse(JSON.stringify(layout || DEFAULT_LAYOUT));
  }

  function getLayout(data) {
    if (data.zupniListicLayout?.blocks?.length) return cloneLayout(data.zupniListicLayout);
    return cloneLayout(DEFAULT_LAYOUT);
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

  function formatMassSchedule(data) {
    if (global.PastoralMise?.formatMassScheduleHtml) {
      return global.PastoralMise.formatMassScheduleHtml(data);
    }
    const rows = data.massSchedule || [];
    if (!rows.length) return "<p>Raspored misa nije unesen.</p>";
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
    const items = (data.announcements || []).slice(0, 8);
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
    const L = global.PastoralLiturgical;
    if (L?.getSummarySync) {
      const sum = L.getSummarySync(iso);
      if (sum?.colorLabel) return sum.colorLabel;
      if (sum?.title) return sum.title;
    }
    const d = new Date(iso + "T12:00:00");
    const day = d.getDay();
    if (day === 0) return "Zelena (ili liturgija dana)";
    if (day === 5) return "Ljubičasta / crvena (petak)";
    return "Zelena (ferija)";
  }

  function renderHeaderBlock(settings, weekStart) {
    const end = weekEndFrom(weekStart);
    return `<header class="listic-print-header">
      <p class="listic-print-meta">${escapeHtml(settings.diocese || "")}</p>
      <h1>${escapeHtml(settings.name || "Župa")}</h1>
      <p class="listic-print-week">${escapeHtml(settings.city || "")} · tjedan ${fmtShort(weekStart)} – ${fmtShort(end)}</p>
      <p class="listic-print-pastor">Župnik: ${escapeHtml(settings.pastor || "")}</p>
      <p class="listic-print-liturgy"><em>Liturgijska boja:</em> ${escapeHtml(liturgicalColorHint(weekStart))}</p>
    </header>`;
  }

  function renderSection(title, bodyHtml) {
    if (!title) return `<div class="listic-print-body">${bodyHtml}</div>`;
    return `<section class="listic-print-block"><h2>${escapeHtml(title)}</h2><div class="listic-print-body">${bodyHtml}</div></section>`;
  }

  function renderBlockHtml(block, data, settings, weekStart) {
    const start = weekStartFrom(weekStart);
    const end = weekEndFrom(start);
    const meta = BLOCK_TYPES[block.type] || {};

    switch (block.type) {
      case "header":
        return renderHeaderBlock(settings, start);
      case "mass_schedule":
        return renderSection(block.title || "Raspored sv. misa", formatMassSchedule(data));
      case "nakane":
        return renderSection(block.title || "Molitvene nakane", formatNakaneHtml(data, start));
      case "announcements":
        return renderSection(block.title || "Obavijesti župe", formatAnnouncements(data));
      case "custom_text":
        return renderSection(block.title || "Obavijest", renderRichBody(block.body));
      case "sacraments":
        return renderSection(block.title || "Sakramenti i događaji", formatSacramentsAndEvents(data, start, end));
      case "contact":
        return renderSection(
          block.title || "Župni ured",
          `<p>Tel. ${escapeHtml(settings.phone || "—")}<br>E-mail: ${escapeHtml(settings.email || "—")}<br>${escapeHtml(settings.address || "")}</p>`
        );
      case "footer":
        return `<footer class="listic-print-footer">
          ${renderRichBody(block.body)}
          <p><small>Izdano: ${new Date().toLocaleDateString("hr-HR")}</small></p>
        </footer>`;
      default:
        return meta.auto ? "" : renderSection(block.title || "", renderRichBody(block.body));
    }
  }

  function renderLayoutToHtml(layout, data, settings, weekStart) {
    const blocks = (layout?.blocks || []).filter((b) => b.enabled !== false);
    const inner = blocks.map((b) => renderBlockHtml(b, data, settings, weekStart)).join("\n");
    return `<div class="listic-print-doc">${inner}</div>`;
  }

  function buildAutoValues(data, settings, weekStart) {
    const start = weekStartFrom(weekStart);
    const end = weekEndFrom(start);
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
      obavijesti_zupe: formatAnnouncements(data),
      kateheza_pobožnosti:
        "Kateheza: provjerite raspored skupina u modulu Krizma / Prva pričest.\n\nPobožnosti: korizmeni program prema župnom kalendaru.",
      sakramenti_dogadaji: formatSacramentsAndEvents(data, start, end),
      kontakt_ured: `Tel. ${settings.phone || "—"}\nE-mail: ${settings.email || "—"}\n${settings.address || ""}`,
      napomena_listica: "Župni listić — izdanje za župljane. Molimo za molitvenu naknadu za župu.",
      datum_izdavanja: new Date().toLocaleDateString("hr-HR"),
    };
  }

  function syncAutoBlocksFromData(layout, data, settings, weekStart) {
    const auto = buildAutoValues(data, settings, weekStart);
    layout.blocks.forEach((b) => {
      if (b.type === "custom_text" && b.id === "blk_kt" && !b.body) {
        b.body = auto.kateheza_pobožnosti;
      }
      if (b.type === "footer" && b.id === "blk_ft" && !b.body) {
        b.body = auto.napomena_listica;
      }
    });
    return layout;
  }

  function defaultData() {
    const start = weekStartFrom();
    const end = weekEndFrom(start);
    return {
      zupniListicLayout: cloneLayout(DEFAULT_LAYOUT),
      zupniListicTemplate: { ...DEFAULT_TEMPLATE },
      zupniListicIssues: [],
    };
  }

  function migrate(data, settings) {
    const def = defaultData();
    if (!data.zupniListicLayout?.blocks?.length) {
      data.zupniListicLayout = def.zupniListicLayout;
      data.zupniListicLayout.updatedAt = new Date().toISOString();
    }
    if (!Array.isArray(data.zupniListicIssues)) data.zupniListicIssues = [];
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

  function blockUid() {
    return `blk_${Date.now().toString(36).slice(-6)}`;
  }

  function renderBlockBuilder(blocks, { mode = "edit" } = {}) {
    const esc = escapeHtml;
    return `<div class="listic-blocks-builder" data-builder-mode="${mode}">
      ${blocks
        .map((block, index) => {
          const meta = BLOCK_TYPES[block.type] || { label: block.type, desc: "", auto: false };
          const canRemove = !meta.fixed && block.type === "custom_text";
          const showTitle = block.type !== "header" && block.type !== "footer";
          const titleField = showTitle
            ? `<input type="text" class="listic-block-title-input" data-block-title="${esc(block.id)}" value="${esc(block.title || meta.label)}" placeholder="Naslov sekcije" />`
            : `<span class="listic-block-fixed-title">${esc(meta.label)}</span>`;

          const bodyField =
            !meta.auto && block.type !== "header"
              ? `<div class="listic-rte-host" data-block-body="${esc(block.id)}"></div>`
              : `<p class="card-sub listic-block-auto-hint">${esc(meta.desc)}</p>`;

          return `<article class="listic-block-card${block.enabled === false ? " is-disabled" : ""}" data-block-id="${esc(block.id)}">
            <div class="listic-block-card-head">
              <label class="listic-block-enable">
                <input type="checkbox" data-block-enabled="${esc(block.id)}" ${block.enabled !== false ? "checked" : ""} />
                <strong>${esc(meta.label)}</strong>
              </label>
              <div class="listic-block-move">
                <button type="button" class="btn btn-ghost btn-sm" data-block-up="${esc(block.id)}" ${index === 0 ? "disabled" : ""} title="Gore">↑</button>
                <button type="button" class="btn btn-ghost btn-sm" data-block-down="${esc(block.id)}" ${index === blocks.length - 1 ? "disabled" : ""} title="Dolje">↓</button>
                ${canRemove ? `<button type="button" class="btn btn-ghost btn-sm" data-block-del="${esc(block.id)}" title="Ukloni">×</button>` : ""}
              </div>
            </div>
            ${titleField}
            ${bodyField}
          </article>`;
        })
        .join("")}
    </div>
    <button type="button" class="btn btn-secondary btn-sm listic-add-text-block" data-add-text-block="${mode}">+ Dodaj tekstualni blok</button>`;
  }

  function mountZupniListicPage(root, api) {
    if (!root) return;
    const esc = api.escapeHtml || escapeHtml;
    let activeTab = "edit";
    let editingIssueId = null;
    let weekStart = weekStartFrom();
    let editLayout = null;

    function getData() {
      return migrate(api.getData(), api.getSettings?.() || {});
    }

    function saveData(data) {
      api.saveData(data);
    }

    function freshEditLayout() {
      const data = getData();
      const settings = api.getSettings?.() || {};
      return syncAutoBlocksFromData(cloneLayout(getLayout(data)), data, settings, weekStart);
    }

    function getEditLayout() {
      if (!editLayout) editLayout = freshEditLayout();
      return editLayout;
    }

    function readBlockBodyFromDom(blockId, scope) {
      const wrap = (scope || root).querySelector(`[data-block-body="${blockId}"]`);
      if (!wrap) return null;
      if (global.PastoralRichText?.getHtml) return global.PastoralRichText.getHtml(wrap);
      return wrap.value ?? "";
    }

    function readBlocksFromDom() {
      const layout = getEditLayout();
      layout.blocks.forEach((block) => {
        const en = root.querySelector(`[data-block-enabled="${block.id}"]`);
        if (en) block.enabled = en.checked;
        const title = root.querySelector(`[data-block-title="${block.id}"]`);
        if (title) block.title = title.value;
        const body = readBlockBodyFromDom(block.id);
        if (body !== null) block.body = body;
      });
      return layout;
    }

    function updatePreview() {
      const box = root.querySelector("#listic-preview");
      if (!box) return;
      const layout = readBlocksFromDom();
      const html = renderLayoutToHtml(layout, getData(), api.getSettings?.() || {}, weekStart);
      box.innerHTML = html;
    }

    function moveBlock(id, dir) {
      const layout = readBlocksFromDom();
      const i = layout.blocks.findIndex((b) => b.id === id);
      const j = i + dir;
      if (i < 0 || j < 0 || j >= layout.blocks.length) return;
      const tmp = layout.blocks[i];
      layout.blocks[i] = layout.blocks[j];
      layout.blocks[j] = tmp;
      render();
      updatePreview();
    }

    function render() {
      if (root.querySelector('[data-builder-mode="edit"]') && editLayout) {
        readBlocksFromDom();
      }
      const data = getData();
      const settings = api.getSettings?.() || {};
      const layout = getEditLayout();
      const issues = [...(data.zupniListicIssues || [])].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
      const savedLayout = getLayout(data);

      root.innerHTML = `
        <div class="listic-tabs card" role="tablist">
          <button type="button" class="listic-tab ${activeTab === "edit" ? "is-active" : ""}" data-tab="edit">Sastavi listić</button>
          <button type="button" class="listic-tab ${activeTab === "layout" ? "is-active" : ""}" data-tab="layout">Raspored blokova</button>
          <button type="button" class="listic-tab ${activeTab === "history" ? "is-active" : ""}" data-tab="history">Povijest (${issues.length})</button>
        </div>

        <div class="listic-panel ${activeTab === "edit" ? "" : "hidden"}" data-panel="edit">
          <div class="listic-layout">
            <section class="card listic-form-card">
              <h2 class="section-title">Sastavi listić za tjedan</h2>
              <p class="card-sub">Uključite blokove, uredite tekst rich editorom i pregledajte listić — bez ručnog HTML-a.</p>
              <div class="listic-week-row">
                <div class="form-group">
                  <label>Tjedan (ponedjeljak)</label>
                  <input type="date" id="listic-week-start" value="${weekStart}" />
                </div>
                <button type="button" class="btn btn-secondary btn-sm" id="listic-autofill">Osvježi automatske blokove</button>
              </div>
              ${renderBlockBuilder(layout.blocks, { mode: "edit" })}
              <div class="listic-actions">
                <button type="button" class="btn btn-primary" id="listic-save-issue">Spremi u povijest</button>
                <button type="button" class="btn btn-secondary" id="listic-print-btn">Ispis / PDF</button>
                ${editingIssueId ? `<button type="button" class="btn btn-ghost" id="listic-cancel-edit">Novi listić</button>` : ""}
              </div>
            </section>
            <section class="card listic-preview-card">
              <h2 class="section-title">Pregled</h2>
              <div id="listic-preview" class="listic-preview"></div>
            </section>
          </div>
        </div>

        <div class="listic-panel ${activeTab === "layout" ? "" : "hidden"}" data-panel="layout">
          <section class="card">
            <h2 class="section-title">Zadani raspored blokova</h2>
            <p class="card-sub">Ovaj redoslijed i uključenost blokova koristi se pri svakom novom listiću. Tekstualne blokove možete dodavati i uklanjati.</p>
            ${renderBlockBuilder(savedLayout.blocks, { mode: "layout" })}
            <div class="listic-actions">
              <button type="button" class="btn btn-primary" id="listic-save-default-layout">Spremi zadani raspored</button>
              <button type="button" class="btn btn-ghost btn-sm" id="listic-reset-layout">Vrati početni raspored</button>
            </div>
          </section>
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
                : `<div class="empty-state ui-empty-fancy"><p>Još nema spremljenih listića. Sastavite prvi u kartici „Sastavi listić”.</p></div>`
            }
          </section>
        </div>`;

      bindEvents();
      mountRichEditors("edit");
      mountRichEditors("layout");
      if (activeTab === "edit") updatePreview();
    }

    function mountRichEditors(mode) {
      const RTE = global.PastoralRichText;
      if (!RTE) return;
      const builder = root.querySelector(`[data-builder-mode="${mode}"]`);
      if (!builder) return;
      const layout = mode === "layout" ? getLayout(getData()) : getEditLayout();
      builder.querySelectorAll("[data-block-body]").forEach((wrap) => {
        const block = layout.blocks.find((b) => b.id === wrap.dataset.blockBody);
        delete wrap.dataset.rteMounted;
        RTE.mount(wrap, {
          html: block?.body || "",
          placeholder: "Upišite i oblikujte tekst…",
          onChange: () => {
            if (mode === "edit") updatePreview();
          },
        });
      });
    }

    function readLayoutBlocksFromDom(mode) {
      const selector = `[data-builder-mode="${mode}"]`;
      const builder = root.querySelector(selector);
      if (!builder) return [];
      const source = mode === "layout" ? getLayout(getData()) : getEditLayout();
      const blocks = cloneLayout({ blocks: source.blocks }).blocks;
      blocks.forEach((block) => {
        const en = builder.querySelector(`[data-block-enabled="${block.id}"]`);
        if (en) block.enabled = en.checked;
        const title = builder.querySelector(`[data-block-title="${block.id}"]`);
        if (title) block.title = title.value;
        const body = readBlockBodyFromDom(block.id, builder);
        if (body !== null) block.body = body;
      });
      return blocks;
    }

    function bindBlockBuilderEvents(mode) {
      const builder = root.querySelector(`[data-builder-mode="${mode}"]`);
      if (!builder) return;

      builder.addEventListener("input", (e) => {
        if (e.target.matches("[data-block-title], [data-block-enabled]")) {
          if (mode === "edit") updatePreview();
        }
      });

      builder.querySelectorAll("[data-block-up]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const layout = mode === "layout" ? { blocks: readLayoutBlocksFromDom("layout") } : readBlocksFromDom();
          const i = layout.blocks.findIndex((b) => b.id === btn.dataset.blockUp);
          if (i <= 0) return;
          [layout.blocks[i - 1], layout.blocks[i]] = [layout.blocks[i], layout.blocks[i - 1]];
          if (mode === "layout") {
            const d = getData();
            d.zupniListicLayout.blocks = layout.blocks;
            saveData(d);
            render();
          } else {
            editLayout = layout;
            render();
            updatePreview();
          }
        });
      });

      builder.querySelectorAll("[data-block-down]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const layout = mode === "layout" ? { blocks: readLayoutBlocksFromDom("layout") } : readBlocksFromDom();
          const i = layout.blocks.findIndex((b) => b.id === btn.dataset.blockDown);
          if (i < 0 || i >= layout.blocks.length - 1) return;
          [layout.blocks[i + 1], layout.blocks[i]] = [layout.blocks[i], layout.blocks[i + 1]];
          if (mode === "layout") {
            const d = getData();
            d.zupniListicLayout.blocks = layout.blocks;
            saveData(d);
            render();
          } else {
            editLayout = layout;
            render();
            updatePreview();
          }
        });
      });

      builder.querySelectorAll("[data-block-del]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const layout = mode === "layout" ? { blocks: readLayoutBlocksFromDom("layout") } : readBlocksFromDom();
          layout.blocks = layout.blocks.filter((b) => b.id !== btn.dataset.blockDel);
          if (mode === "layout") {
            const d = getData();
            d.zupniListicLayout.blocks = layout.blocks;
            saveData(d);
            render();
          } else {
            editLayout = layout;
            render();
            updatePreview();
          }
        });
      });
    }

    function bindEvents() {
      root.querySelectorAll(".listic-tab").forEach((btn) => {
        btn.addEventListener("click", () => {
          activeTab = btn.dataset.tab;
          if (activeTab === "edit" && !editLayout) editLayout = freshEditLayout();
          render();
        });
      });

      root.querySelector("#listic-week-start")?.addEventListener("change", (e) => {
        weekStart = e.target.value || weekStartFrom();
        if (activeTab === "edit") {
          editLayout = freshEditLayout();
          render();
        }
      });

      bindBlockBuilderEvents("edit");
      bindBlockBuilderEvents("layout");

      root.querySelectorAll("[data-add-text-block]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const mode = btn.dataset.addTextBlock;
          const newBlock = {
            id: blockUid(),
            type: "custom_text",
            enabled: true,
            title: "Nova sekcija",
            body: "",
          };
          if (mode === "layout") {
            const d = getData();
            const blocks = readLayoutBlocksFromDom("layout");
            blocks.push(newBlock);
            d.zupniListicLayout.blocks = blocks;
            saveData(d);
            render();
          } else {
            const layout = readBlocksFromDom();
            layout.blocks.push(newBlock);
            editLayout = layout;
            render();
            updatePreview();
          }
        });
      });

      root.querySelector("#listic-autofill")?.addEventListener("click", () => {
        weekStart = root.querySelector("#listic-week-start")?.value || weekStartFrom();
        editLayout = freshEditLayout();
        render();
        api.showToast?.("Automatski blokovi osvježeni iz župe");
      });

      root.querySelector("#listic-print-btn")?.addEventListener("click", () => {
        const layout = readBlocksFromDom();
        const html = renderLayoutToHtml(layout, getData(), api.getSettings?.() || {}, weekStart);
        const start = weekStartFrom(weekStart);
        printHtml(html, `Župni listić ${fmtShort(start)}`);
      });

      root.querySelector("#listic-save-issue")?.addEventListener("click", () => {
        const d = getData();
        const layout = readBlocksFromDom();
        const ws = root.querySelector("#listic-week-start")?.value || weekStartFrom();
        const we = weekEndFrom(ws);
        const html = renderLayoutToHtml(layout, d, api.getSettings?.() || {}, ws);
        const title = `Listić ${fmtShort(ws)} – ${fmtShort(we)}`;
        const id = editingIssueId || api.uid?.("listic") || `listic_${Date.now()}`;
        const issue = {
          id,
          weekStart: ws,
          weekEnd: we,
          title,
          status: "izdan",
          layoutSnapshot: layout,
          renderedHtml: html,
          createdAt: editingIssueId
            ? d.zupniListicIssues.find((x) => x.id === editingIssueId)?.createdAt || new Date().toISOString()
            : new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        d.zupniListicIssues = d.zupniListicIssues.filter((x) => x.id !== id);
        d.zupniListicIssues.unshift(issue);
        saveData(d);
        editingIssueId = id;
        api.showToast?.("Listić spremljen u povijest");
        activeTab = "history";
        render();
      });

      root.querySelector("#listic-cancel-edit")?.addEventListener("click", () => {
        editingIssueId = null;
        editLayout = freshEditLayout();
        activeTab = "edit";
        render();
      });

      root.querySelector("#listic-save-default-layout")?.addEventListener("click", () => {
        const d = getData();
        d.zupniListicLayout = {
          blocks: readLayoutBlocksFromDom("layout"),
          updatedAt: new Date().toISOString(),
        };
        saveData(d);
        editLayout = null;
        api.showToast?.("Zadani raspored blokova spremljen");
      });

      root.querySelector("#listic-reset-layout")?.addEventListener("click", () => {
        if (!confirm("Vratiti početni raspored blokova?")) return;
        const d = getData();
        d.zupniListicLayout = cloneLayout(DEFAULT_LAYOUT);
        d.zupniListicLayout.updatedAt = new Date().toISOString();
        saveData(d);
        editLayout = null;
        api.showToast?.("Početni raspored vraćen");
        render();
      });

      root.querySelectorAll("[data-listic-view]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const issue = getData().zupniListicIssues.find((x) => x.id === btn.dataset.listicView);
          if (!issue) return;
          const html =
            issue.renderedHtml ||
            renderLayoutToHtml(
              issue.layoutSnapshot || getLayout(getData()),
              getData(),
              api.getSettings?.() || {},
              issue.weekStart
            );
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
          editLayout = cloneLayout(issue.layoutSnapshot || getLayout(getData()));
          activeTab = "edit";
          render();
          const ws = root.querySelector("#listic-week-start");
          if (ws) ws.value = weekStart;
          updatePreview();
        });
      });

      root.querySelectorAll("[data-listic-print-id]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const issue = getData().zupniListicIssues.find((x) => x.id === btn.dataset.listicPrintId);
          if (!issue) return;
          const html =
            issue.renderedHtml ||
            renderLayoutToHtml(
              issue.layoutSnapshot || getLayout(getData()),
              getData(),
              api.getSettings?.() || {},
              issue.weekStart
            );
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

    editLayout = freshEditLayout();
    render();
  }

  global.PastoralZupniListic = {
    DEFAULT_TEMPLATE,
    DEFAULT_LAYOUT,
    BLOCK_TYPES,
    FIELD_LABELS,
    migrate,
    getTemplate,
    getLayout,
    extractPlaceholders,
    mergeTemplate,
    buildAutoValues,
    renderLayoutToHtml,
    formatMassScheduleHtml: formatMassSchedule,
    mountZupniListicPage,
    printHtml,
    weekStartFrom,
  };
})(typeof window !== "undefined" ? window : global);
