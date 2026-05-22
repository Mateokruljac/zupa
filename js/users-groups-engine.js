/**
 * Upravljanje grupama, korisnicima aplikacije i svećenicima župe
 */
(function (global) {
  const P = global.PastoralPermissions;
  const MODULES = P?.MODULES || {};

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function kindLabel(kind) {
    return P?.GROUP_KIND_LABELS?.[kind] || kind || "—";
  }

  function permCheckboxes(selected, disabled) {
    return Object.entries(MODULES)
      .map(([key, cfg]) => {
        const on = (selected || []).includes(key);
        return `<label class="perm-check"><input type="checkbox" name="perm" value="${esc(key)}" ${on ? "checked" : ""} ${disabled ? "disabled" : ""}> ${esc(cfg.label)}</label>`;
      })
      .join("");
  }

  function saveData(api, data) {
    P.migrate(data);
    api.saveData(data);
  }

  function mountKorisniciPage(root, api) {
    if (!root) return;
    P.migrate(api.getData());
    let tab = root.dataset.tab || "grupe";

    function render() {
      const data = api.getData();
      P.migrate(data);
      const groups = data.appGroups || [];
      const users = data.appUsers || [];
      const priests = data.parishPriests || [];
      const priestUsers = users.filter((u) => u.priestId || (u.groupIds || []).includes("grp-svecenici"));

      root.innerHTML = `
        <section class="card perm-intro-card">
          <h2 class="section-title">Korisnici, grupe i svećenici</h2>
          <p class="card-sub">Svaki korisnik pripada jednoj ili više <strong>grupa</strong>. Grupa <strong>Svećenici župe</strong> je posebna kategorija za kontrolu pristupa modulima (kao u drugim sustavima). Demo prijava: e-mail iz popisa + uloga ako korisnik nije pronađen.</p>
        </section>
        <nav class="plan-tabs perm-tabs">
          <button type="button" class="plan-tab ${tab === "grupe" ? "active" : ""}" data-perm-tab="grupe">Grupe (${groups.length})</button>
          <button type="button" class="plan-tab ${tab === "korisnici" ? "active" : ""}" data-perm-tab="korisnici">Korisnici (${users.length})</button>
          <button type="button" class="plan-tab ${tab === "svecenici" ? "active" : ""}" data-perm-tab="svecenici">Svećenici župe (${priests.length})</button>
        </nav>
        <div id="perm-tab-panel"></div>`;

      const panel = root.querySelector("#perm-tab-panel");

      if (tab === "grupe") {
        panel.innerHTML = `
          <section class="card">
            <div class="perm-panel-head">
              <h3 class="section-title" style="margin:0">Grupe pristupa</h3>
              <button type="button" class="btn btn-primary btn-sm" data-add-group>+ Nova grupa</button>
            </div>
            <div class="perm-grid">
              ${groups
                .map(
                  (g) => `
                <article class="card perm-group-card perm-group-card--${esc(g.kind)}">
                  <div class="perm-group-head">
                    <h4>${esc(g.name)}</h4>
                    <span class="badge">${esc(kindLabel(g.kind))}</span>
                    ${g.isSystem ? '<span class="badge badge-done">sustav</span>' : ""}
                  </div>
                  <p class="card-sub">${esc(g.description || "")}</p>
                  <p class="perm-module-tags">${(g.permissions || [])
                    .map((k) => `<span class="badge badge-sacrament">${esc(MODULES[k]?.label || k)}</span>`)
                    .join(" ")}</p>
                  <p class="card-sub">${users.filter((u) => (u.groupIds || []).includes(g.id)).length} korisnika</p>
                  <button type="button" class="btn btn-ghost btn-sm" data-edit-group="${esc(g.id)}">Uredi dozvole</button>
                </article>`
                )
                .join("")}
            </div>
          </section>`;
      } else if (tab === "korisnici") {
        panel.innerHTML = `
          <section class="card">
            <div class="perm-panel-head">
              <h3 class="section-title" style="margin:0">Korisnici aplikacije</h3>
              <button type="button" class="btn btn-primary btn-sm" data-add-user>+ Novi korisnik</button>
            </div>
            <div class="table-wrap"><table class="data-table">
              <thead><tr><th>Ime</th><th>E-mail</th><th>Grupe</th><th>Svećenik</th><th>Status</th><th></th></tr></thead>
              <tbody>
                ${users
                  .map((u) => {
                    const gnames = (u.groupIds || [])
                      .map((id) => groups.find((g) => g.id === id)?.name)
                      .filter(Boolean)
                      .join(", ");
                    const pr = priests.find((p) => p.id === u.priestId);
                    return `<tr>
                      <td><strong>${esc(u.name)}</strong></td>
                      <td>${esc(u.email)}</td>
                      <td>${esc(gnames || "—")}</td>
                      <td>${pr ? esc(pr.name) : "—"}</td>
                      <td>${u.active === false ? '<span class="badge badge-urgent">neaktivan</span>' : '<span class="badge badge-done">aktivan</span>'}</td>
                      <td><button type="button" class="btn btn-ghost btn-sm" data-edit-user="${esc(u.id)}">Uredi</button></td>
                    </tr>`;
                  })
                  .join("")}
              </tbody>
            </table></div>
          </section>`;
      } else {
        panel.innerHTML = `
          <section class="card perm-priest-hero card-section--liturgy">
            <h3 class="section-title">Svećenici župe</h3>
            <p class="card-sub">Evidencija svećenika odvojena je od ostalih korisnika. Za pristup aplikaciji svećenik je u grupi <strong>Svećenici župe</strong> i ima povezan korisnički račun (e-mail za prijavu).</p>
          </section>
          <section class="card">
            <div class="perm-panel-head">
              <h3 class="section-title" style="margin:0">Popis svećenika</h3>
              <button type="button" class="btn btn-primary btn-sm" data-add-priest>+ Svećenik</button>
            </div>
            <div class="table-wrap"><table class="data-table">
              <thead><tr><th>Ime</th><th>Uloga</th><th>E-mail</th><th>Telefon</th><th>Korisnik app</th><th></th></tr></thead>
              <tbody>
                ${priests
                  .map((pr) => {
                    const u = users.find((x) => x.id === pr.userId || x.priestId === pr.id);
                    return `<tr>
                      <td><strong>${esc(pr.name)}</strong></td>
                      <td><span class="badge">${esc(pr.title || "—")}</span></td>
                      <td>${esc(pr.email || "—")}</td>
                      <td>${esc(pr.phone || "—")}</td>
                      <td>${u ? esc(u.email) : '<span class="badge badge-urgent">nema računa</span>'}</td>
                      <td>
                        <button type="button" class="btn btn-ghost btn-sm" data-edit-priest="${esc(pr.id)}">Uredi</button>
                        ${!u ? `<button type="button" class="btn btn-primary btn-sm" data-link-user-priest="${esc(pr.id)}">+ Račun</button>` : ""}
                      </td>
                    </tr>`;
                  })
                  .join("")}
              </tbody>
            </table></div>
          </section>`;
      }

      bindPanel(root, api, render);
    }

    render();
  }

  function bindPanel(root, api, rerender) {
    root.querySelectorAll("[data-perm-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        root.dataset.tab = btn.dataset.permTab;
        rerender();
      });
    });

    root.querySelector("[data-add-group]")?.addEventListener("click", () => openGroupForm(api, null, rerender));
    root.querySelectorAll("[data-edit-group]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const g = api.getData().appGroups.find((x) => x.id === btn.dataset.editGroup);
        openGroupForm(api, g, rerender);
      });
    });

    root.querySelector("[data-add-user]")?.addEventListener("click", () => openUserForm(api, null, rerender));
    root.querySelectorAll("[data-edit-user]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const u = api.getData().appUsers.find((x) => x.id === btn.dataset.editUser);
        openUserForm(api, u, rerender);
      });
    });

    root.querySelector("[data-add-priest]")?.addEventListener("click", () => openPriestForm(api, null, rerender));
    root.querySelectorAll("[data-edit-priest]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const pr = api.getData().parishPriests.find((x) => x.id === btn.dataset.editPriest);
        openPriestForm(api, pr, rerender);
      });
    });
    root.querySelectorAll("[data-link-user-priest]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const pr = api.getData().parishPriests.find((x) => x.id === btn.dataset.linkUserPriest);
        openUserForm(api, null, rerender, { priest: pr, defaultGroupIds: ["grp-svecenici"] });
      });
    });
  }

  function openGroupForm(api, group, rerender) {
    const data = api.getData();
    const g = group || { id: `grp_${Date.now()}`, slug: "", name: "", kind: "custom", description: "", permissions: ["pregled"], isSystem: false };
    const isPriest = g.kind === "priest" || g.id === "grp-svecenici";

    global.PastoralModal?.openForm({
      title: group ? `Grupa: ${g.name}` : "Nova grupa",
      size: "lg",
      body: `
        <div class="form-grid">
          <div class="form-group"><label>Naziv</label><input name="name" value="${esc(g.name)}" required ${g.isSystem ? "readonly" : ""}></div>
          <div class="form-group"><label>Vrsta</label>
            <select name="kind" ${g.isSystem ? "disabled" : ""}>
              ${Object.entries(P.GROUP_KIND_LABELS)
                .map(([k, lbl]) => `<option value="${k}" ${g.kind === k ? "selected" : ""}>${esc(lbl)}</option>`)
                .join("")}
            </select>
          </div>
          <div class="form-group form-wide"><label>Opis</label><input name="description" value="${esc(g.description)}"></div>
        </div>
        <p class="card-label" style="margin-top:16px">Dozvole modula</p>
        <div class="perm-check-grid">${permCheckboxes(g.permissions, isPriest && g.isSystem)}</div>
        ${isPriest ? '<p class="card-sub">Grupa Svećenici župe u demo-u ima sve module; u produkciji prilagodite po župi.</p>' : ""}`,
      onSubmit: (form) => {
        const fd = new FormData(form);
        const perms = [...form.querySelectorAll('input[name="perm"]:checked')].map((i) => i.value);
        if (!perms.length) {
          api.showToast("Odaberite barem jedan modul");
          return;
        }
        const row = {
          ...g,
          name: fd.get("name")?.trim() || g.name,
          kind: g.isSystem ? g.kind : fd.get("kind") || "custom",
          description: fd.get("description")?.trim() || "",
          permissions: perms,
          slug: g.slug || (fd.get("name") || "").toLowerCase().replace(/\s+/g, "-").slice(0, 24),
        };
        const idx = data.appGroups.findIndex((x) => x.id === g.id);
        if (idx >= 0) data.appGroups[idx] = row;
        else data.appGroups.push(row);
        saveData(api, data);
        api.showToast("Grupa spremljena");
        rerender();
      },
    });
  }

  function openUserForm(api, user, rerender, opts = {}) {
    const data = api.getData();
    const groups = data.appGroups || [];
    const priests = data.parishPriests || [];
    const u =
      user ||
      {
        id: `usr_${Date.now()}`,
        name: opts.priest?.name || "",
        email: opts.priest?.email || "",
        groupIds: opts.defaultGroupIds || ["grp-kateheta"],
        active: true,
        priestId: opts.priest?.id || null,
        legacyRole: "kateheta",
      };

    const groupChecks = groups
      .map(
        (g) =>
          `<label class="perm-check"><input type="checkbox" name="groupId" value="${esc(g.id)}" ${
            (u.groupIds || []).includes(g.id) ? "checked" : ""
          }> ${esc(g.name)} <span class="card-sub">(${esc(kindLabel(g.kind))})</span></label>`
      )
      .join("");

    global.PastoralModal?.openForm({
      title: user ? `Korisnik: ${u.name}` : "Novi korisnik",
      size: "lg",
      body: `
        <div class="form-grid">
          <div class="form-group"><label>Ime i prezime</label><input name="name" value="${esc(u.name)}" required></div>
          <div class="form-group"><label>E-mail (prijava)</label><input name="email" type="email" value="${esc(u.email)}" required></div>
          <div class="form-group"><label>Povezani svećenik</label>
            <select name="priestId">
              <option value="">— nije svećenik —</option>
              ${priests.map((p) => `<option value="${esc(p.id)}" ${u.priestId === p.id ? "selected" : ""}>${esc(p.name)}</option>`).join("")}
            </select>
          </div>
          <div class="form-group"><label>Demo uloga (padajući izbornik)</label>
            <select name="legacyRole">
              ${["zupnik", "vikar", "upravitelj", "kateheta"]
                .map((r) => `<option value="${r}" ${u.legacyRole === r ? "selected" : ""}>${esc(P.LEGACY_ROLE_LABELS[r])}</option>`)
                .join("")}
            </select>
          </div>
          <div class="form-group"><label><input type="checkbox" name="active" ${u.active !== false ? "checked" : ""}> Aktivan</label></div>
        </div>
        <p class="card-label" style="margin-top:12px">Grupe</p>
        <div class="perm-check-grid">${groupChecks}</div>`,
      onSubmit: (form) => {
        const fd = new FormData(form);
        const groupIds = [...form.querySelectorAll('input[name="groupId"]:checked')].map((i) => i.value);
        if (!groupIds.length) {
          api.showToast("Odaberite barem jednu grupu");
          return;
        }
        const priestId = fd.get("priestId") || null;
        if (priestId && !groupIds.includes("grp-svecenici")) {
          groupIds.push("grp-svecenici");
        }
        const row = {
          ...u,
          name: fd.get("name")?.trim(),
          email: fd.get("email")?.trim(),
          groupIds,
          priestId: priestId || null,
          legacyRole: fd.get("legacyRole") || "kateheta",
          active: !!fd.get("active"),
        };
        const idx = data.appUsers.findIndex((x) => x.id === u.id);
        if (idx >= 0) data.appUsers[idx] = row;
        else data.appUsers.push(row);
        if (priestId) {
          const pr = data.parishPriests.find((p) => p.id === priestId);
          if (pr) {
            pr.userId = row.id;
            pr.email = row.email;
            pr.name = row.name;
          }
        }
        saveData(api, data);
        api.showToast("Korisnik spremljen");
        rerender();
      },
    });
  }

  function openPriestForm(api, priest, rerender) {
    const data = api.getData();
    const pr =
      priest ||
      {
        id: `pr_${Date.now()}`,
        name: "",
        title: "vikar",
        email: "",
        phone: "",
        active: true,
        userId: null,
        notes: "",
      };

    global.PastoralModal?.openForm({
      title: priest ? pr.name : "Novi svećenik",
      body: `
        <div class="form-grid">
          <div class="form-group"><label>Ime (s titulom)</label><input name="name" value="${esc(pr.name)}" required placeholder="npr. don Ivo Horvat"></div>
          <div class="form-group"><label>Uloga</label>
            <select name="title">
              ${["župnik", "vikar", "svećenik", "student"]
                .map((t) => `<option ${pr.title === t ? "selected" : ""}>${t}</option>`)
                .join("")}
            </select>
          </div>
          <div class="form-group"><label>E-mail</label><input name="email" type="email" value="${esc(pr.email)}"></div>
          <div class="form-group"><label>Telefon</label><input name="phone" value="${esc(pr.phone)}"></div>
          <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${esc(pr.notes)}"></div>
          <div class="form-group"><label><input type="checkbox" name="active" ${pr.active !== false ? "checked" : ""}> Aktivan u župi</label></div>
        </div>`,
      onSubmit: (form) => {
        const fd = new FormData(form);
        const row = {
          ...pr,
          name: fd.get("name")?.trim(),
          title: fd.get("title"),
          email: fd.get("email")?.trim(),
          phone: fd.get("phone")?.trim(),
          notes: fd.get("notes")?.trim(),
          active: !!fd.get("active"),
        };
        const idx = data.parishPriests.findIndex((x) => x.id === pr.id);
        if (idx >= 0) data.parishPriests[idx] = row;
        else data.parishPriests.push(row);
        saveData(api, data);
        api.showToast("Svećenik spremljen");
        rerender();
      },
    });
  }

  global.PastoralUsersGroups = { mountKorisniciPage };
})(typeof window !== "undefined" ? window : global);
