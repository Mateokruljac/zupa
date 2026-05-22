/**
 * Računi župe — izdavanje, status, veza na dugovanja
 */
(function (global) {
  const STATUS = [
    { id: "nacrt", label: "Nacrt" },
    { id: "izdan", label: "Izdan" },
    { id: "djelomicno", label: "Djelomično plaćen" },
    { id: "placen", label: "Plaćen" },
    { id: "storno", label: "Storno" },
  ];

  const CATEGORIES = [
    { id: "lukno", label: "Lukno" },
    { id: "nakane", label: "Misne nakane" },
    { id: "krsenje", label: "Krštenje" },
    { id: "prva-pricest", label: "Prva pričest" },
    { id: "krizma", label: "Krizma" },
    { id: "vjencanje", label: "Vjenčanje" },
    { id: "pogreb", label: "Pogreb" },
    { id: "ostalo", label: "Ostalo" },
  ];

  function catLabel(id) {
    return CATEGORIES.find((c) => c.id === id)?.label || id;
  }

  function statusLabel(id) {
    return STATUS.find((s) => s.id === id)?.label || id;
  }

  function nextInvoiceNumber(data, year) {
    const y = year || new Date().getFullYear();
    const prefix = `${y}-`;
    const nums = (data.invoices || [])
      .map((i) => i.number)
      .filter((n) => n && n.startsWith(prefix))
      .map((n) => Number(n.split("-")[1]) || 0);
    const seq = (nums.length ? Math.max(...nums) : 0) + 1;
    return `${prefix}${String(seq).padStart(3, "0")}`;
  }

  function migrate(data) {
    if (!Array.isArray(data.invoices)) data.invoices = [];
    data.invoices.forEach((inv) => {
      if (!inv.status) inv.status = inv.paidAmount >= inv.total ? "placen" : "izdan";
      if (inv.vatRate == null) inv.vatRate = 0;
      if (inv.paidAmount == null) inv.paidAmount = inv.status === "placen" ? inv.total : 0;
    });
    return data;
  }

  function summarize(data, yearFilter) {
    const list = (data.invoices || []).filter((i) => {
      if (!yearFilter || yearFilter === "all") return true;
      return String(i.issueDate || "").startsWith(String(yearFilter));
    });
    const open = list.filter((i) => i.status !== "placen" && i.status !== "storno");
    const unpaidSum = open.reduce((s, i) => s + Math.max(0, (Number(i.total) || 0) - (Number(i.paidAmount) || 0)), 0);
    const paidSum = list.filter((i) => i.status === "placen").reduce((s, i) => s + (Number(i.total) || 0), 0);
    return { count: list.length, open: open.length, unpaidSum, paidSum };
  }

  function createFromDebt(data, debtRow, payerDefaults) {
    migrate(data);
    const inv = {
      id: `inv_${Date.now().toString(36).slice(2, 8)}`,
      number: nextInvoiceNumber(data, debtRow.year),
      issueDate: new Date().toISOString().slice(0, 10),
      dueDate: debtRow.dueDate || new Date().toISOString().slice(0, 10),
      payerName: payerDefaults?.name || debtRow.contact || "—",
      payerAddress: payerDefaults?.address || "",
      payerOib: "",
      category: debtRow.category,
      description: debtRow.label,
      amount: debtRow.amount,
      vatRate: 0,
      total: debtRow.amount,
      status: "izdan",
      paidAmount: 0,
      paidAt: "",
      linkedSource: debtRow.source,
      notes: "",
    };
    data.invoices.unshift(inv);
    return inv;
  }

  function mountInvoicesPage(root, api) {
    if (!root) return;
    const esc = api.escapeHtml;
    const fmt = api.fmtDate;
    let yearFilter = "all";
    let statusFilter = "all";

    function openInvoiceModal(existing, preset) {
      const inv = existing || {
        number: nextInvoiceNumber(api.getData()),
        issueDate: new Date().toISOString().slice(0, 10),
        dueDate: new Date().toISOString().slice(0, 10),
        payerName: preset?.payerName || "",
        payerAddress: preset?.payerAddress || "",
        payerOib: "",
        category: preset?.category || "ostalo",
        description: preset?.description || "",
        amount: preset?.amount || 0,
        vatRate: 0,
        total: preset?.amount || 0,
        status: "izdan",
        paidAmount: 0,
        paidAt: "",
        notes: "",
        linkedSource: preset?.linkedSource || null,
      };

      const body = `
        <div class="form-grid">
          <div class="form-group"><label>Broj računa</label><input name="number" value="${esc(inv.number)}" required /></div>
          <div class="form-group"><label>Datum izdavanja</label><input name="issueDate" type="date" value="${inv.issueDate || ""}" /></div>
          <div class="form-group"><label>Rok plaćanja</label><input name="dueDate" type="date" value="${inv.dueDate || ""}" /></div>
          <div class="form-group form-wide"><label>Platitelj *</label><input name="payerName" value="${esc(inv.payerName)}" required /></div>
          <div class="form-group form-wide"><label>Adresa</label><input name="payerAddress" value="${esc(inv.payerAddress || "")}" /></div>
          <div class="form-group"><label>OIB</label><input name="payerOib" value="${esc(inv.payerOib || "")}" /></div>
          <div class="form-group"><label>Kategorija</label>
            <select name="category">${CATEGORIES.map((c) => `<option value="${c.id}" ${inv.category === c.id ? "selected" : ""}>${esc(c.label)}</option>`).join("")}</select>
          </div>
          <div class="form-group form-wide"><label>Opis / stavka *</label><input name="description" value="${esc(inv.description)}" required /></div>
          <div class="form-group"><label>Iznos (€)</label><input name="amount" type="number" min="0" step="0.01" value="${inv.amount ?? 0}" /></div>
          <div class="form-group"><label>PDV %</label><input name="vatRate" type="number" min="0" max="25" value="${inv.vatRate ?? 0}" /></div>
          <div class="form-group"><label>Status</label>
            <select name="status">${STATUS.map((s) => `<option value="${s.id}" ${inv.status === s.id ? "selected" : ""}>${esc(s.label)}</option>`).join("")}</select>
          </div>
          <div class="form-group"><label>Plaćeno (€)</label><input name="paidAmount" type="number" min="0" step="0.01" value="${inv.paidAmount ?? 0}" /></div>
          <div class="form-group"><label>Datum uplate</label><input name="paidAt" type="date" value="${(inv.paidAt || "").slice(0, 10)}" /></div>
          <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${esc(inv.notes || "")}" /></div>
        </div>`;

      global.PastoralModal?.openForm({
        title: existing ? "Uredi račun" : "Novi račun",
        size: "lg",
        body,
        onSubmit: (form) => {
          const fd = new FormData(form);
          const amount = Number(fd.get("amount")) || 0;
          const vatRate = Number(fd.get("vatRate")) || 0;
          const total = Math.round(amount * (1 + vatRate / 100) * 100) / 100;
          const paidAmount = Number(fd.get("paidAmount")) || 0;
          const row = existing || { id: api.uid("inv") };
          Object.assign(row, {
            number: fd.get("number")?.trim(),
            issueDate: fd.get("issueDate") || "",
            dueDate: fd.get("dueDate") || "",
            payerName: fd.get("payerName")?.trim(),
            payerAddress: fd.get("payerAddress")?.trim() || "",
            payerOib: fd.get("payerOib")?.trim() || "",
            category: fd.get("category"),
            description: fd.get("description")?.trim(),
            amount,
            vatRate,
            total,
            status: fd.get("status"),
            paidAmount,
            paidAt: fd.get("paidAt") || "",
            notes: fd.get("notes")?.trim() || "",
          });
          if (paidAmount >= total && total > 0) row.status = "placen";
          const data = api.getData();
          migrate(data);
          if (!existing) data.invoices.unshift(row);
          api.saveData(data);
          api.showToast(existing ? "Račun ažuriran" : "Račun izdan");
          render();
        },
      });
    }

    function render() {
      const data = api.getData();
      migrate(data);
      const summary = summarize(data, yearFilter);
      const years = [...new Set((data.invoices || []).map((i) => (i.issueDate || "").slice(0, 4)).filter(Boolean))];
      const cur = String(new Date().getFullYear());
      if (!years.includes(cur)) years.unshift(cur);
      years.sort((a, b) => b - a);

      let list = [...(data.invoices || [])];
      if (yearFilter !== "all") list = list.filter((i) => (i.issueDate || "").startsWith(yearFilter));
      if (statusFilter !== "all") list = list.filter((i) => i.status === statusFilter);

      root.innerHTML = `
        <div class="kpi-row">
          <article class="card kpi-card"><p class="card-label">Računa (filtar)</p><p class="card-value">${summary.count}</p></article>
          <article class="card kpi-card"><p class="card-label">Otvoreno</p><p class="card-value">${summary.open}</p><p class="card-sub">${summary.unpaidSum.toFixed(2)} €</p></article>
          <article class="card kpi-card"><p class="card-label">Plaćeno (filtar)</p><p class="card-value">${summary.paidSum.toFixed(2)} €</p></article>
        </div>
        <section class="card">
          <div class="racuni-toolbar">
            <button type="button" class="btn btn-primary btn-sm" id="inv-add-btn">+ Novi račun</button>
            <a href="${api.pageUrl("pages/dugovanja.html")}" class="btn btn-ghost btn-sm">Iz dugovanja</a>
            <a href="${api.pageUrl("pages/potvrde.html")}?vrsta=uplata" class="btn btn-ghost btn-sm">Potvrda uplate</a>
            <select id="inv-year-filter" class="racuni-filter-select">
              <option value="all">Sve godine</option>
              ${years.map((y) => `<option value="${y}" ${yearFilter === y ? "selected" : ""}>${y}</option>`).join("")}
            </select>
            <select id="inv-status-filter" class="racuni-filter-select">
              <option value="all">Svi statusi</option>
              ${STATUS.map((s) => `<option value="${s.id}" ${statusFilter === s.id ? "selected" : ""}>${esc(s.label)}</option>`).join("")}
            </select>
          </div>
          <div id="inv-table-mount"></div>
        </section>
        <p class="card-sub" style="margin-top:12px">Demo: nije fiskalizacija ni e-Račun. Za produkciju povežite knjigovodstvo župe ili vanjski ERP.</p>`;

      const rows = list.map((inv) => {
        const rest = Math.max(0, (Number(inv.total) || 0) - (Number(inv.paidAmount) || 0));
        const statusCls =
          inv.status === "placen" ? "badge-done" : inv.status === "storno" ? "" : rest > 0 ? "badge-urgent" : "";
        return {
          ...inv,
          categoryLabel: catLabel(inv.category),
          issueFmt: fmt(inv.issueDate),
          dueFmt: fmt(inv.dueDate),
          totalFmt: `${(inv.total ?? 0).toFixed(2)} €`,
          restFmt: rest > 0 ? `${rest.toFixed(2)} €` : "—",
          statusBadge: `<span class="badge ${statusCls}">${esc(statusLabel(inv.status))}</span>`,
          actions: `
            <button type="button" class="btn btn-ghost btn-sm" data-inv-edit="${esc(inv.id)}">Uredi</button>
            <button type="button" class="btn btn-ghost btn-sm" data-inv-paid="${esc(inv.id)}">Plaćeno</button>
            <a href="${api.pageUrl("pages/potvrde.html")}?vrsta=uplata" class="btn btn-ghost btn-sm" data-inv-potvrda="${esc(inv.id)}">Potvrda</a>`,
        };
      });

      global.PastoralTableKit?.mountDataTable({
        mount: root.querySelector("#inv-table-mount"),
        rows,
        columns: [
          { key: "number", label: "Broj", render: (r) => `<strong>${esc(r.number)}</strong>` },
          { key: "issueFmt", label: "Datum" },
          { key: "payerName", label: "Platitelj" },
          { key: "categoryLabel", label: "Kategorija" },
          { key: "description", label: "Opis" },
          { key: "totalFmt", label: "Ukupno" },
          { key: "restFmt", label: "Preostalo" },
          { key: "statusBadge", label: "Status", render: (r) => r.statusBadge },
          { key: "actions", label: "", render: (r) => r.actions },
        ],
        exportName: "racuni_zupe",
        pageSize: 12,
      });

      root.querySelector("#inv-add-btn")?.addEventListener("click", () => openInvoiceModal(null, null));
      root.querySelector("#inv-year-filter")?.addEventListener("change", (e) => {
        yearFilter = e.target.value;
        render();
      });
      root.querySelector("#inv-status-filter")?.addEventListener("change", (e) => {
        statusFilter = e.target.value;
        render();
      });

      if (!root.dataset.invBound) {
        root.dataset.invBound = "1";
        root.addEventListener("click", (ev) => {
          const edit = ev.target.closest("[data-inv-edit]");
          const paid = ev.target.closest("[data-inv-paid]");
          const data = api.getData();
          if (edit) {
            const inv = data.invoices.find((i) => i.id === edit.dataset.invEdit);
            if (inv) openInvoiceModal(inv);
          }
          if (paid) {
            const inv = data.invoices.find((i) => i.id === paid.dataset.invPaid);
            if (!inv) return;
            inv.paidAmount = inv.total;
            inv.paidAt = new Date().toISOString().slice(0, 10);
            inv.status = "placen";
            if (global.PastoralDebts?.markDebtPaid && inv.linkedSource) {
              global.PastoralDebts.markDebtPaid(data, inv.linkedSource);
            }
            api.saveData(data);
            api.showToast("Račun označen kao plaćen");
            render();
          }
        });
      }

      const params = new URLSearchParams(location.search);
      if (params.get("novi") === "1" && !root.dataset.invOpened) {
        root.dataset.invOpened = "1";
        const preset = {
          payerName: params.get("platitelj") || "",
          description: params.get("opis") || "",
          amount: Number(params.get("iznos")) || 0,
          category: params.get("kat") || "ostalo",
        };
        openInvoiceModal(null, preset);
      }
    }

    render();
  }

  global.PastoralInvoices = {
    STATUS,
    CATEGORIES,
    migrate,
    summarize,
    nextInvoiceNumber,
    createFromDebt,
    mountInvoicesPage,
  };
})(typeof window !== "undefined" ? window : global);
