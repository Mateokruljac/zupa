/**
 * Obiteljski list — tabovi kao župni-ured (osnovno, muž/žena, djeca, rođaci, bilješke, lukno)
 */
(function (global) {
  const SPOUSE_KEYS = ["husband", "wife"];

  function emptySpouse() {
    return {
      name: "",
      birthYear: "",
      birthPlace: "",
      baptismDate: "",
      baptismPlace: "",
      communionDate: "",
      confirmationDate: "",
      deathDate: "",
      weddingChurch: "",
      weddingCivil: "",
      notes: "",
    };
  }

  function syncSpousesFromMembers(fam) {
    const members = fam.members || [];
    const pick = (re) => members.find((m) => re.test(m.relation || ""));
    if (!fam.husband?.name) {
      const m = pick(/muž|otac|domaćin/i);
      if (m) fam.husband = { ...emptySpouse(), name: m.name, birthYear: m.birthYear || "", notes: m.notes || "" };
    }
    if (!fam.wife?.name) {
      const w = pick(/žena|majka/i);
      if (w) fam.wife = { ...emptySpouse(), name: w.name, birthYear: w.birthYear || "", notes: w.notes || "" };
    }
  }

  function migrateFamily(fam) {
    if (!fam.originPlace) fam.originPlace = "";
    if (!Array.isArray(fam.relatives)) fam.relatives = [];
    if (!fam.husband) fam.husband = null;
    if (!fam.wife) fam.wife = null;
    syncSpousesFromMembers(fam);
    (fam.members || []).forEach((m) => {
      if (!m.id) m.id = `m_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`;
    });
    (fam.relatives || []).forEach((r) => {
      if (!r.id) r.id = `rel_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`;
    });
    return fam;
  }

  function childMembers(fam) {
    return (fam.members || []).filter((m) => /dijete|kć|sin|unuk/i.test(m.relation || ""));
  }

  function renderSpouseBlock(label, key, person, famId, esc) {
    const p = person || emptySpouse();
    return `
      <div class="family-spouse-block">
        <div class="family-spouse-head">
          <h4>${esc(label)}</h4>
          <div class="family-spouse-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-action="edit-spouse" data-fam="${famId}" data-spouse="${key}">Uredi</button>
            <button type="button" class="btn btn-ghost btn-sm" data-action="load-matica-spouse" data-fam="${famId}" data-spouse="${key}">Iz matice</button>
          </div>
        </div>
        <dl class="canon-dl">
          <dt>Ime</dt><dd><strong>${esc(p.name || "—")}</strong></dd>
          <dt>Rođen</dt><dd>${esc(p.birthYear || "—")} ${p.birthPlace ? `· ${esc(p.birthPlace)}` : ""}</dd>
          <dt>Krštenje</dt><dd>${esc(p.baptismDate || "—")} ${p.baptismPlace ? `· ${esc(p.baptismPlace)}` : ""}</dd>
          <dt>Pričest / krizma</dt><dd>${esc(p.communionDate || "—")} / ${esc(p.confirmationDate || "—")}</dd>
          <dt>Vjenčanje</dt><dd>Crkveno: ${esc(p.weddingChurch || "—")} · Civilno: ${esc(p.weddingCivil || "—")}</dd>
        </dl>
      </div>`;
  }

  function renderDetailHtml(fam, data, api) {
    migrateFamily(fam);
    global.PastoralFamilyCrud?.migrateFamily(fam);
    const esc = api.escapeHtml;
    const fmt = api.fmtDate;
    const street = api.getStreetName(data, fam.streetId);
    const y = new Date().getFullYear();
    const FC = global.PastoralFamilyCrud;
    const cur = FC ? FC.currentYearStatus(fam, y) : {};

    const children = childMembers(fam);
    const otherMembers = (fam.members || []).filter((m) => !children.includes(m));

    const childrenRows = children
      .map(
        (m) => `<tr>
          <td><strong>${esc(m.name)}</strong></td>
          <td>${esc(m.relation || "—")}</td>
          <td>${m.birthYear || "—"}</td>
          <td>${(m.sacraments || []).map((s) => `<span class="badge badge-sacrament">${esc(s)}</span>`).join(" ") || "—"}</td>
          <td class="crud-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-action="edit-member" data-fam="${fam.id}" data-member="${m.id}">Uredi</button>
            <button type="button" class="btn btn-ghost btn-sm" data-action="delete-member" data-fam="${fam.id}" data-member="${m.id}">×</button>
          </td>
        </tr>`
      )
      .join("");

    const relativeRows = (fam.relatives || [])
      .map(
        (r) => `<tr>
          <td><strong>${esc(r.name)}</strong></td>
          <td>${esc(r.relation || "rođak")}</td>
          <td>${r.birthYear || "—"}</td>
          <td>${esc(r.notes || "")}</td>
          <td class="crud-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-action="edit-relative" data-fam="${fam.id}" data-relative="${r.id}">Uredi</button>
            <button type="button" class="btn btn-ghost btn-sm" data-action="delete-relative" data-fam="${fam.id}" data-relative="${r.id}">×</button>
          </td>
        </tr>`
      )
      .join("");

    const contribHtml = typeof api.renderContributions === "function" ? api.renderContributions(fam, data) : "";

    return `
      <div class="family-detail-inner family-tabs-root" data-family-detail="${fam.id}">
        <div class="family-karton-head">
          <div class="family-karton-summary">
            <p class="family-karton-addr">${esc(fam.address || street)}</p>
            <p class="family-karton-meta-line">
              <span class="badge">${esc(street)}</span>
              ${fam.phone ? `<span>${esc(fam.phone)}</span>` : ""}
              Lukno ${y}: ${cur.paid ? '<span class="badge badge-done">plaćeno</span>' : '<span class="badge badge-urgent">neplaćeno</span>'}
            </p>
          </div>
          <div class="family-karton-actions crud-actions">
            <button type="button" class="btn btn-secondary btn-sm" data-action="edit-family" data-fam="${fam.id}">Uredi obitelj</button>
            <button type="button" class="btn btn-ghost btn-sm" data-action="delete-family" data-fam="${fam.id}">Obriši</button>
          </div>
        </div>
        <nav class="family-tab-nav family-tab-nav--scroll" role="tablist">
          <button type="button" class="family-tab is-on" data-tab="osnovno">Osnovno</button>
          <button type="button" class="family-tab" data-tab="muz-zena">Muž i žena</button>
          <button type="button" class="family-tab" data-tab="djeca">Djeca</button>
          <button type="button" class="family-tab" data-tab="rodaci">Rođaci i ukućani</button>
          <button type="button" class="family-tab" data-tab="biljeske">Bilješke</button>
          <button type="button" class="family-tab" data-tab="lukno">Lukno i darovi</button>
        </nav>
        <div class="family-tab-panel is-on" data-panel="osnovno">
          <dl class="canon-dl">
            <dt>Prezime</dt><dd><strong>${esc(fam.surname)}</strong></dd>
            <dt>Adresa</dt><dd>${esc(fam.address || "—")}</dd>
            <dt>Ulica</dt><dd>${esc(street)}</dd>
            <dt>Telefon</dt><dd>${esc(fam.phone || "—")}</dd>
            <dt>E-mail</dt><dd>${esc(fam.email || "—")}</dd>
            <dt>Podrijetlo</dt><dd>${esc(fam.originPlace || "—")}</dd>
            <dt>Status</dt><dd><span class="badge">${esc(fam.status || "—")}</span></dd>
          </dl>
        </div>
        <div class="family-tab-panel" data-panel="muz-zena">
          <div class="family-spouse-grid">
            ${renderSpouseBlock("Muž", "husband", fam.husband, fam.id, esc)}
            ${renderSpouseBlock("Žena", "wife", fam.wife, fam.id, esc)}
          </div>
          ${otherMembers.length ? `<p class="card-sub family-other-members">Ostali u popisu: ${otherMembers.map((m) => esc(m.name)).join(", ")}</p>` : ""}
        </div>
        <div class="family-tab-panel" data-panel="djeca">
          <div class="family-panel-toolbar">
            <button type="button" class="btn btn-primary btn-sm" data-action="add-member" data-fam="${fam.id}">+ Dijete / član</button>
            <button type="button" class="btn btn-ghost btn-sm" data-action="load-matica-child" data-fam="${fam.id}">Iz matice krštenih</button>
          </div>
          <div class="table-wrap family-panel-table"><table class="data-table">
            <thead><tr><th>Ime</th><th>Srodstvo</th><th>Rođ.</th><th>Sakramenti</th><th></th></tr></thead>
            <tbody>${childrenRows || '<tr><td colspan="5" class="empty-state">Nema djece u popisu.</td></tr>'}</tbody>
          </table></div>
        </div>
        <div class="family-tab-panel" data-panel="rodaci">
          <div class="family-panel-toolbar">
            <button type="button" class="btn btn-primary btn-sm" data-action="add-relative" data-fam="${fam.id}">+ Rođak / ukućan</button>
          </div>
          <div class="table-wrap family-panel-table"><table class="data-table">
            <thead><tr><th>Ime</th><th>Uloga</th><th>Rođ.</th><th>Napomena</th><th></th></tr></thead>
            <tbody>${relativeRows || '<tr><td colspan="5" class="empty-state">Nema upisanih rođaka.</td></tr>'}</tbody>
          </table></div>
        </div>
        <div class="family-tab-panel" data-panel="biljeske">
          <p class="family-notes" style="white-space:pre-wrap">${esc(fam.pastoralNotes || "—")}</p>
          <button type="button" class="btn btn-ghost btn-sm" data-action="edit-notes" data-fam="${fam.id}">Uredi bilješke</button>
          ${(fam.tags || []).length ? `<p style="margin-top:12px">${fam.tags.map((t) => `<span class="badge badge-done">${esc(t)}</span>`).join(" ")}</p>` : ""}
        </div>
        <div class="family-tab-panel" data-panel="lukno">${contribHtml}</div>
      </div>`;
  }

  function bindTabs(overlay) {
    overlay.querySelectorAll(".family-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        const id = tab.dataset.tab;
        overlay.querySelectorAll(".family-tab").forEach((t) => t.classList.toggle("is-on", t.dataset.tab === id));
        overlay.querySelectorAll(".family-tab-panel").forEach((p) => p.classList.toggle("is-on", p.dataset.panel === id));
      });
    });
  }

  function openSpouseEditor(fam, key, api, onSaved) {
    const p = fam[key] || emptySpouse();
    global.PastoralModal?.openForm({
      title: key === "husband" ? "Muž" : "Žena",
      body: `
        <div class="form-grid">
          <div class="form-group"><label>Ime i prezime</label><input name="name" value="${api.escapeHtml(p.name)}" required></div>
          <div class="form-group"><label>Godina rođenja</label><input name="birthYear" value="${api.escapeHtml(p.birthYear)}"></div>
          <div class="form-group"><label>Mjesto rođenja</label><input name="birthPlace" value="${api.escapeHtml(p.birthPlace)}"></div>
          <div class="form-group"><label>Datum krštenja</label><input name="baptismDate" value="${api.escapeHtml(p.baptismDate)}"></div>
          <div class="form-group"><label>Mjesto krštenja</label><input name="baptismPlace" value="${api.escapeHtml(p.baptismPlace)}"></div>
          <div class="form-group"><label>Vjenčanje (crkva)</label><input name="weddingChurch" value="${api.escapeHtml(p.weddingChurch)}"></div>
          <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${api.escapeHtml(p.notes)}"></div>
        </div>`,
      onSubmit: (form) => {
        const fd = new FormData(form);
        fam[key] = {};
        ["name", "birthYear", "birthPlace", "baptismDate", "baptismPlace", "weddingChurch", "notes"].forEach((k) => {
          fam[key][k] = String(fd.get(k) || "").trim();
        });
        onSaved();
      },
    });
  }

  function bindDetail(overlay, root, api) {
    bindTabs(overlay);
    overlay.addEventListener("click", (e) => {
      const tabBtn = e.target.closest(".family-tab");
      if (tabBtn && overlay.contains(tabBtn)) return;

      const btn = e.target.closest("[data-action]");
      if (!btn || !overlay.contains(btn)) return;
      const action = btn.dataset.action;
      const famId = btn.dataset.fam;
      const data = api.getData();
      const fam = data.families?.find((f) => f.id === famId);
      if (!fam) return;

      if (action === "edit-spouse") {
        e.stopPropagation();
        openSpouseEditor(fam, btn.dataset.spouse, api, () => {
          api.saveData(data);
          api.refreshDetail(root);
          api.showToast("Spremljeno");
        });
        return;
      }
      if (action === "load-matica-spouse" || action === "load-matica-child") {
        e.stopPropagation();
        global.PastoralMaticaLookup?.openSearchModal(api, {
          types: action === "load-matica-child" ? ["krštenja"] : ["krštenja", "vjenčanja"],
          onPick: (hit) => {
            if (action === "load-matica-child") {
              fam.members = fam.members || [];
              fam.members.push({
                id: `m_${Date.now()}`,
                name: hit.payload.dijete || hit.payload.ime_prezime,
                relation: "dijete",
                birthYear: (hit.payload.birthDate || "").slice(0, 4),
                sacraments: ["krštenje"],
                roles: [],
                notes: `Učitano iz matice ${hit.payload.maticni_broj || ""}`,
              });
            } else {
              const key = btn.dataset.spouse;
              fam[key] = fam[key] || emptySpouse();
              fam[key].name = hit.payload.dijete || hit.payload.mladzenja || hit.payload.mlada || hit.payload.ime_prezime || "";
              fam[key].baptismDate = hit.payload.datum_krstenja || "";
            }
            api.saveData(data);
            api.refreshDetail(root);
            api.showToast("Učitano iz matice");
          },
        });
        return;
      }
      if (action === "add-relative") {
        e.stopPropagation();
        global.PastoralModal?.openForm({
          title: "Novi rođak / ukućan",
          body: `<div class="form-grid">
            <div class="form-group"><label>Ime</label><input name="name" required></div>
            <div class="form-group"><label>Uloga</label><input name="relation" value="rođak"></div>
            <div class="form-group"><label>Godina rođenja</label><input name="birthYear"></div>
            <div class="form-group form-wide"><label>Napomena</label><input name="notes"></div>
          </div>`,
          onSubmit: (form) => {
            const fd = new FormData(form);
            fam.relatives = fam.relatives || [];
            fam.relatives.push({
              id: `rel_${Date.now()}`,
              name: fd.get("name"),
              relation: fd.get("relation"),
              birthYear: fd.get("birthYear"),
              notes: fd.get("notes"),
            });
            api.saveData(data);
            api.refreshDetail(root);
            api.showToast("Dodano");
          },
        });
        return;
      }
      if (action === "edit-relative") {
        e.stopPropagation();
        const rel = fam.relatives?.find((r) => r.id === btn.dataset.relative);
        if (!rel) return;
        global.PastoralModal?.openForm({
          title: "Uredi rođaka",
          body: `<div class="form-grid">
            <div class="form-group"><label>Ime</label><input name="name" value="${api.escapeHtml(rel.name)}" required></div>
            <div class="form-group"><label>Uloga</label><input name="relation" value="${api.escapeHtml(rel.relation)}"></div>
            <div class="form-group"><label>Godina</label><input name="birthYear" value="${api.escapeHtml(rel.birthYear)}"></div>
            <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${api.escapeHtml(rel.notes)}"></div>
          </div>`,
          onSubmit: (form) => {
            const fd = new FormData(form);
            rel.name = fd.get("name");
            rel.relation = fd.get("relation");
            rel.birthYear = fd.get("birthYear");
            rel.notes = fd.get("notes");
            api.saveData(data);
            api.refreshDetail(root);
          },
        });
        return;
      }
      if (action === "delete-relative") {
        e.stopPropagation();
        api.confirm("Ukloniti rođaka?", { danger: true }).then((ok) => {
          if (!ok) return;
          fam.relatives = (fam.relatives || []).filter((r) => r.id !== btn.dataset.relative);
          api.saveData(data);
          api.refreshDetail(root);
        });
        return;
      }
      if (action === "edit-notes") {
        e.stopPropagation();
        global.PastoralModal?.openForm({
          title: "Pastoralne bilješke",
          body: `<div class="form-group form-wide"><textarea name="notes" rows="8">${api.escapeHtml(fam.pastoralNotes || "")}</textarea></div>`,
          onSubmit: (form) => {
            fam.pastoralNotes = new FormData(form).get("notes")?.trim() || "";
            api.saveData(data);
            api.refreshDetail(root);
          },
        });
        return;
      }
    });
  }

  global.PastoralFamilyList = {
    migrateFamily,
    renderDetailHtml,
    bindDetail,
    emptySpouse,
  };
})(typeof window !== "undefined" ? window : global);
