/**
 * Blagajna župe — dnevnik i godišnji izvještaj
 */
(function (global) {
  const ENTRY_TYPES = [
    { id: "ulaz", label: "Ulaz" },
    { id: "izlaz", label: "Izlaz" },
  ];

  function migrate(data) {
    if (!Array.isArray(data.cashbook)) data.cashbook = [];
    return data;
  }

  function summarizeYear(data, year) {
    const y = String(year);
    const rows = (data.cashbook || []).filter((e) => (e.date || "").startsWith(y));
    let inSum = 0;
    let outSum = 0;
    const byCategory = {};
    rows.forEach((e) => {
      const amt = Number(e.amount) || 0;
      if (e.type === "ulaz") inSum += amt;
      else outSum += amt;
      const cat = e.category || "ostalo";
      if (!byCategory[cat]) byCategory[cat] = { in: 0, out: 0 };
      if (e.type === "ulaz") byCategory[cat].in += amt;
      else byCategory[cat].out += amt;
    });
    const invPaid = (data.invoices || [])
      .filter((i) => (i.paidAt || i.issueDate || "").startsWith(y) && i.status === "placen")
      .reduce((s, i) => s + (Number(i.paidAmount) || Number(i.total) || 0), 0);
    return { inSum, outSum, balance: inSum - outSum, byCategory, invPaid, count: rows.length };
  }

  function mountCashbookPage(root, api) {
    if (global.PastoralFinanceAdv) global.PastoralFinanceAdv.migrate(api.getData());
    migrate(api.getData());
    let yearFilter = new Date().getFullYear();
    let ledgerFilter = "sve";

    function render() {
      const data = api.getData();
      const summary = summarizeYear(data, yearFilter);
      const esc = api.escapeHtml;
      const fmt = api.fmtDate;
      let rows = (data.cashbook || [])
        .filter((e) => (e.date || "").startsWith(String(yearFilter)))
        .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
      if (ledgerFilter !== "sve") rows = rows.filter((e) => (e.ledger || "plavi") === ledgerFilter);

      root.innerHTML = `
        ${
          global.PastoralKpi
            ? global.PastoralKpi.row([
                { tone: "success", label: `Ulaz ${yearFilter}`, value: `${summary.inSum.toFixed(2)} €` },
                { tone: "alert", label: `Izlaz ${yearFilter}`, value: `${summary.outSum.toFixed(2)} €` },
                { tone: "finance", label: "Saldo", value: `${summary.balance.toFixed(2)} €` },
                { tone: "neutral", label: "Plaćeni računi", value: `${summary.invPaid.toFixed(2)} €` },
              ])
            : `<div class="kpi-row">
          <article class="card kpi-card"><p class="card-label">Ulaz ${yearFilter}</p><p class="card-value">${summary.inSum.toFixed(2)} €</p></article>
          <article class="card kpi-card"><p class="card-label">Izlaz ${yearFilter}</p><p class="card-value">${summary.outSum.toFixed(2)} €</p></article>
          <article class="card kpi-card"><p class="card-label">Saldo</p><p class="card-value">${summary.balance.toFixed(2)} €</p></article>
          <article class="card kpi-card"><p class="card-label">Plaćeni računi</p><p class="card-value">${summary.invPaid.toFixed(2)} €</p></article>
        </div>`
        }
        <section class="card page-table-section">
          <div class="racuni-toolbar">
            <button type="button" class="btn btn-primary btn-sm" id="cb-add">+ Unos</button>
            <select id="cb-year">${[yearFilter, yearFilter - 1, yearFilter - 2].map((y) => `<option value="${y}" ${y === yearFilter ? "selected" : ""}>${y}</option>`).join("")}</select>
            <button type="button" class="btn btn-secondary btn-sm" id="cb-report">🖨 Izvještaj ŽEV ${yearFilter}</button>
            <a href="${api.pageUrl("pages/racuni.html")}" class="btn btn-ghost btn-sm">Računi</a>
          </div>
          <div id="cb-table-mount"></div>
        </section>
        <section class="card wide">
          <h2 class="section-title">Po kategorijama (${yearFilter})</h2>
          <div class="debts-cat-summary">${Object.entries(summary.byCategory)
            .map(([cat, v]) => `<div class="debts-cat-stat"><span class="debts-cat-stat-label">${esc(cat)}</span><strong>+${v.in.toFixed(0)} / −${v.out.toFixed(0)} €</strong></div>`)
            .join("") || '<p class="empty-state">—</p>'}</div>
        </section>`;

      global.PastoralTableKit?.mountDataTable({
        mount: root.querySelector("#cb-table-mount"),
        rows: rows.map((e) => ({
          ...e,
          dateFmt: fmt(e.date),
          amountFmt: `${e.type === "ulaz" ? "+" : "−"}${(Number(e.amount) || 0).toFixed(2)} €`,
          typeBadge: e.type === "ulaz" ? '<span class="badge badge-done">ulaz</span>' : '<span class="badge badge-urgent">izlaz</span>',
        })),
        columns: [
          { key: "dateFmt", label: "Datum" },
          { key: "ledger", label: "Dnevnik", render: (r) => `<span class="badge">${esc(r.ledger || "plavi")}</span>` },
          { key: "typeBadge", label: "Tip", render: (r) => r.typeBadge },
          { key: "category", label: "Kategorija" },
          { key: "description", label: "Opis" },
          { key: "amountFmt", label: "Iznos" },
          { key: "paymentMethod", label: "Način" },
        ],
        exportName: `blagajna_${yearFilter}`,
        pageSize: 15,
      });

      global.PastoralFinanceAdv?.enhanceCashbookToolbar(root, api);
      root.querySelector("#cb-ledger")?.addEventListener("change", (e) => {
        ledgerFilter = e.target.value;
        render();
      });

      root.querySelector("#cb-year")?.addEventListener("change", (e) => {
        yearFilter = Number(e.target.value);
        render();
      });

      root.querySelector("#cb-add")?.addEventListener("click", () => {
        global.PastoralModal?.openForm({
          title: "Blagajnički unos",
          body: `
            <div class="form-grid">
              <div class="form-group"><label>Datum</label><input name="date" type="date" value="${new Date().toISOString().slice(0, 10)}" /></div>
              <div class="form-group"><label>Tip</label><select name="type">${ENTRY_TYPES.map((t) => `<option value="${t.id}">${t.label}</option>`).join("")}</select></div>
              <div class="form-group"><label>Dnevnik</label><select name="ledger"><option value="plavi">Plavi</option><option value="crveni">Crveni</option></select></div>
              <div class="form-group"><label>Kategorija</label><input name="category" placeholder="lukno, nakane, župni fond…" /></div>
              <div class="form-group"><label>Iznos (€)</label><input name="amount" type="number" min="0" step="0.01" required /></div>
              <div class="form-group form-wide"><label>Opis</label><input name="description" required /></div>
              <div class="form-group"><label>Način</label><select name="paymentMethod"><option>gotovina</option><option>žiro</option></select></div>
            </div>`,
          onSubmit: (form) => {
            const fd = new FormData(form);
            const d = api.getData();
            migrate(d);
            const entry = {
              id: api.uid("cb"),
              date: fd.get("date") || "",
              type: fd.get("type"),
              ledger: fd.get("ledger") || "plavi",
              category: fd.get("category")?.trim() || "ostalo",
              description: fd.get("description")?.trim(),
              amount: Number(fd.get("amount")) || 0,
              paymentMethod: fd.get("paymentMethod"),
            };
            d.cashbook.unshift(entry);
            const FA = global.PastoralFinanceAdv;
            if (FA) {
              const auto = FA.applyAutoRules(d, entry, api.uid);
              auto.forEach((a) => d.cashbook.unshift(a));
              if (auto.length) api.showToast(`Unos + ${auto.length} automatskih`);
              else api.showToast("Unos dodan");
            } else api.showToast("Unos dodan");
            api.saveData(d);
            render();
          },
        });
      });

      root.querySelector("#cb-report")?.addEventListener("click", () => {
        const settings = api.getSettings?.() || {};
        const html = `
          <div class="print-doc">
            <h2 style="text-align:center">GODIŠNJI FINANCIJSKI PREGLED — ŽEV</h2>
            <p>Župa: <strong>${esc(settings.name || "")}</strong> · Godina: <strong>${yearFilter}</strong></p>
            <p>Ulaz: <strong>${summary.inSum.toFixed(2)} €</strong> · Izlaz: <strong>${summary.outSum.toFixed(2)} €</strong> · Saldo: <strong>${summary.balance.toFixed(2)} €</strong></p>
            <p>Plaćeni računi (evidencija): ${summary.invPaid.toFixed(2)} €</p>
            <table border="1" cellpadding="6" style="width:100%;border-collapse:collapse;margin-top:1em">
              <thead><tr><th>Kategorija</th><th>Ulaz</th><th>Izlaz</th></tr></thead>
              <tbody>${Object.entries(summary.byCategory)
                .map(([cat, v]) => `<tr><td>${esc(cat)}</td><td>${v.in.toFixed(2)}</td><td>${v.out.toFixed(2)}</td></tr>`)
                .join("")}</tbody>
            </table>
            <p style="margin-top:2em">Datum ispisa: ${new Date().toLocaleDateString("hr-HR")}</p>
          </div>`;
        global.PastoralDocuments?.printHtml(html, `Izvještaj ${yearFilter}`);
      });
    }

    render();
  }

  global.PastoralCashbook = { migrate, summarizeYear, mountCashbookPage };
})(typeof window !== "undefined" ? window : global);
