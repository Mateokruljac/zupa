/**
 * Pastoralni posjeti — bolesnici, obitelji, kućna pričest
 */
(function (global) {
  const TYPES = [
    { id: "obitelj", label: "Obitelj" },
    { id: "bolesnik", label: "Bolesnik / starost" },
    { id: "kucna-pricest", label: "Kućna sv. Pričest" },
    { id: "pomazanje", label: "Pomazanje" },
    { id: "ostalo", label: "Ostalo" },
  ];

  function migrate(data) {
    if (!Array.isArray(data.visits)) data.visits = [];
    return data;
  }

  function familyLabel(data, familyId) {
    return data.families?.find((f) => f.id === familyId)?.surname || "";
  }

  function mountVisitsPage(root, api) {
    migrate(api.getData());

    function render() {
      const data = api.getData();
      const params = new URLSearchParams(location.search);
      const filterFam = params.get("family");
      let list = [...(data.visits || [])].sort((a, b) => (b.scheduled || "").localeCompare(a.scheduled || ""));
      if (filterFam) list = list.filter((v) => v.familyId === filterFam);

      const esc = api.escapeHtml;
      const fmt = api.fmtDate;

      root.innerHTML = `
        <section class="card">
          <div class="racuni-toolbar">
            <button type="button" class="btn btn-primary btn-sm" id="visit-add">+ Zakaži posjet</button>
            <a href="${api.pageUrl("pages/obitelji.html")}" class="btn btn-ghost btn-sm">Obitelji</a>
            <a href="${api.pageUrl("pages/pomazanje.html")}" class="btn btn-ghost btn-sm">Pomazanje</a>
          </div>
          <div id="visits-table-mount"></div>
        </section>`;

      const rows = list.map((v) => ({
        ...v,
        familyLabel: v.familyId ? `Obitelj ${familyLabel(data, v.familyId)}` : "—",
        typeLabel: TYPES.find((t) => t.id === v.type)?.label || v.type,
        scheduledFmt: fmt(v.scheduled),
        statusBadge: v.done
          ? '<span class="badge badge-done">obavljeno</span>'
          : v.scheduled < new Date().toISOString().slice(0, 10)
            ? '<span class="badge badge-urgent">zakašnjelo</span>'
            : '<span class="badge">zakazano</span>',
        actions: `
          <button type="button" class="btn btn-ghost btn-sm" data-visit-done="${esc(v.id)}">${v.done ? "Poništi" : "Obavljeno"}</button>
          <button type="button" class="btn btn-ghost btn-sm" data-visit-edit="${esc(v.id)}">Uredi</button>`,
      }));

      global.PastoralTableKit?.mountDataTable({
        mount: root.querySelector("#visits-table-mount"),
        rows,
        columns: [
          { key: "scheduledFmt", label: "Datum" },
          { key: "typeLabel", label: "Vrsta" },
          { key: "person", label: "Osoba / obitelj", render: (r) => `<strong>${esc(r.person || r.familyLabel)}</strong>` },
          { key: "address", label: "Adresa" },
          { key: "priest", label: "Svećenik" },
          { key: "statusBadge", label: "Status", render: (r) => r.statusBadge },
          { key: "actions", label: "", render: (r) => r.actions },
        ],
        exportName: "posjete",
        pageSize: 12,
      });

      function openVisitModal(record) {
        const families = data.families || [];
        global.PastoralModal?.openForm({
          title: record ? "Uredi posjet" : "Novi pastoralni posjet",
          size: "lg",
          body: `
            <div class="form-grid">
              <div class="form-group"><label>Datum *</label><input name="scheduled" type="date" value="${record?.scheduled || ""}" required /></div>
              <div class="form-group"><label>Vrsta</label>
                <select name="type">${TYPES.map((t) => `<option value="${t.id}" ${record?.type === t.id ? "selected" : ""}>${t.label}</option>`).join("")}</select>
              </div>
              <div class="form-group form-wide"><label>Osoba / opis</label><input name="person" value="${esc(record?.person || "")}" /></div>
              <div class="form-group form-wide"><label>Obitelj</label>
                <select name="familyId"><option value="">—</option>${families.map((f) => `<option value="${f.id}" ${record?.familyId === f.id ? "selected" : ""}>${esc(f.surname)} — ${esc(f.address || "")}</option>`).join("")}</select>
              </div>
              <div class="form-group form-wide"><label>Adresa</label><input name="address" value="${esc(record?.address || "")}" /></div>
              <div class="form-group"><label>Svećenik</label><input name="priest" value="${esc(record?.priest || "")}" /></div>
              <div class="form-group form-wide"><label>Svrha / bilješka</label><input name="purpose" value="${esc(record?.purpose || "")}" /></div>
              ${record ? `<div class="form-group"><label>Obavljeno</label><input type="checkbox" name="done" ${record.done ? "checked" : ""} /></div>` : ""}
              ${record ? `<div class="form-group form-wide"><label>Bilješka nakon posjeta</label><textarea name="report" rows="3">${esc(record?.report || "")}</textarea></div>` : ""}
            </div>`,
          onSubmit: (form) => {
            const fd = new FormData(form);
            const d = api.getData();
            migrate(d);
            const row = record || { id: api.uid("vis") };
            Object.assign(row, {
              scheduled: fd.get("scheduled") || "",
              type: fd.get("type") || "obitelj",
              person: fd.get("person")?.trim() || "",
              familyId: fd.get("familyId") || "",
              address: fd.get("address")?.trim() || "",
              priest: fd.get("priest")?.trim() || "",
              purpose: fd.get("purpose")?.trim() || "",
              done: !!form.querySelector('[name="done"]')?.checked,
              report: fd.get("report")?.trim() || "",
            });
            if (!record) {
              row.done = false;
              row.report = "";
              d.visits.push(row);
            }
            if (row.done && row.familyId) {
              const fam = d.families.find((f) => f.id === row.familyId);
              if (fam) fam.lastVisit = row.scheduled;
            }
            api.saveData(d);
            api.showToast(record ? "Posjet spremljen" : "Posjet zakazan");
            render();
          },
        });
      }

      root.querySelector("#visit-add")?.addEventListener("click", () => {
        const famId = filterFam || "";
        const fam = data.families?.find((f) => f.id === famId);
        openVisitModal(
          fam
            ? {
                familyId: fam.id,
                person: `Obitelj ${fam.surname}`,
                address: fam.address,
                type: "obitelj",
                purpose: fam.pastoralNotes || "",
              }
            : null
        );
      });

      if (!root.dataset.visBound) {
        root.dataset.visBound = "1";
        root.addEventListener("click", (ev) => {
          const done = ev.target.closest("[data-visit-done]");
          const edit = ev.target.closest("[data-visit-edit]");
          const d = api.getData();
          if (edit) {
            const v = d.visits.find((x) => x.id === edit.dataset.visitEdit);
            if (v) openVisitModal(v);
          }
          if (done) {
            const v = d.visits.find((x) => x.id === done.dataset.visitDone);
            if (!v) return;
            v.done = !v.done;
            if (v.done && v.familyId) {
              const fam = d.families.find((f) => f.id === v.familyId);
              if (fam) fam.lastVisit = v.scheduled;
            }
            api.saveData(d);
            api.showToast(v.done ? "Posjet obavljen" : "Ponovno otvoreno");
            render();
          }
        });
      }
    }

    render();
  }

  global.PastoralVisits = { TYPES, migrate, mountVisitsPage };
})(typeof window !== "undefined" ? window : global);
