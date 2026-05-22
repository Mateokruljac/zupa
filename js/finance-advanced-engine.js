/**
 * Financije — plavi/crveni dnevnik, izvješća, postavke (župni-ured priručnik)
 */
(function (global) {
  const DEFAULT_CATEGORIES = [
    { id: "lukno", label: "Lukno", type: "ulaz", ledger: "plavi", report: "A-1" },
    { id: "nakane", label: "Misne nakane", type: "ulaz", ledger: "plavi", report: "A-1" },
    { id: "vjenčanje", label: "Vjenčanje", type: "ulaz", ledger: "plavi", report: "A-1" },
    { id: "binacije", label: "Binacije i trinacije", type: "ulaz", ledger: "plavi", report: "A-1" },
    { id: "darovi", label: "Darovi i milostinje", type: "ulaz", ledger: "plavi", report: "B-1" },
    { id: "materijal", label: "Materijal / kateheza", type: "izlaz", ledger: "plavi", report: "C-1" },
    { id: "nadbiskupija", label: "Nadbiskupiji BIH", type: "izlaz", ledger: "crveni", report: "D-1" },
    { id: "zupni-fond", label: "Župni fond", type: "izlaz", ledger: "crveni", report: "D-1" },
  ];

  function migrate(data) {
    if (!Array.isArray(data.cashbookCategories)) data.cashbookCategories = JSON.parse(JSON.stringify(DEFAULT_CATEGORIES));
    if (!Array.isArray(data.cashbookCalculations)) {
      data.cashbookCalculations = [
        { id: "calc1", reportCategory: "binacije", journalCategory: "binacije", reportType: "kvartalno" },
        { id: "calc2", reportCategory: "darovi", journalCategory: "darovi", reportType: "godisnje" },
      ];
    }
    (data.cashbook || []).forEach((e) => {
      if (!e.ledger) e.ledger = "plavi";
      if (!e.reportCode) {
        const cat = data.cashbookCategories.find((c) => c.id === e.category);
        e.reportCode = cat?.report || "";
      }
    });
    if (!Array.isArray(data.cashbookAutoRules)) {
      data.cashbookAutoRules = [
        {
          id: "ar1",
          trigger: "nadbiskupija",
          triggerLedger: "crveni",
          mirror: "darovi",
          mirrorLedger: "plavi",
          mirrorType: "ulaz",
        },
      ];
    }
    return data;
  }

  function applyAutoRules(data, entry, uid) {
    const added = [];
    (data.cashbookAutoRules || []).forEach((rule) => {
      if (rule.trigger !== entry.category) return;
      if ((rule.triggerLedger || "crveni") !== entry.ledger) return;
      added.push({
        id: uid("cb"),
        date: entry.date,
        type: rule.mirrorType || "ulaz",
        ledger: rule.mirrorLedger || "plavi",
        category: rule.mirror,
        description: `(auto) ${entry.description}`,
        amount: entry.amount,
        paymentMethod: entry.paymentMethod,
        reportCode: "",
        autoFrom: entry.id,
      });
    });
    return added;
  }

  function quarterRows(data, year, q) {
    const startM = (q - 1) * 3 + 1;
    const endM = q * 3;
    return (data.cashbook || []).filter((e) => {
      if (e.ledger !== "plavi") return false;
      const d = new Date(e.date + "T12:00:00");
      return d.getFullYear() === year && d.getMonth() + 1 >= startM && d.getMonth() + 1 <= endM;
    });
  }

  function summarizeQuarter(data, year, q) {
    const rows = quarterRows(data, year, q);
    let inSum = 0;
    let outSum = 0;
    rows.forEach((e) => {
      const a = Number(e.amount) || 0;
      if (e.type === "ulaz") inSum += a;
      else outSum += a;
    });
    return { rows, inSum, outSum, diff: inSum - outSum };
  }

  function summarizeYearFinancial(data, year) {
    const y = String(year);
    const rows = (data.cashbook || []).filter((e) => (e.date || "").startsWith(y));
    let cash = 0;
    let bankIn = 0;
    let bankOut = 0;
    rows.forEach((e) => {
      const a = Number(e.amount) || 0;
      if (e.paymentMethod === "žiro") {
        if (e.type === "ulaz") bankIn += a;
        else bankOut += a;
      } else if (e.type === "ulaz") cash += a;
      else cash -= a;
    });
    return { cash, bank: bankIn - bankOut, total: cash + (bankIn - bankOut), count: rows.length };
  }

  function renderSettingsPanel(data, api, tab) {
    const esc = api.escapeHtml;
    if (tab === "stavke") {
      return `<table class="data-table"><thead><tr><th>ID</th><th>Naziv</th><th>Tip</th><th>Dnevnik</th><th>Izvještaj</th></tr></thead>
        <tbody>${(data.cashbookCategories || []).map((c) => `<tr><td>${esc(c.id)}</td><td>${esc(c.label)}</td><td>${esc(c.type)}</td><td>${esc(c.ledger)}</td><td>${esc(c.report)}</td></tr>`).join("")}</tbody></table>`;
    }
    if (tab === "kalkulacije") {
      return `<table class="data-table"><thead><tr><th>Izvještaj stavka</th><th>Dnevnik stavka</th><th>Vrsta</th></tr></thead>
        <tbody>${(data.cashbookCalculations || []).map((c) => `<tr><td>${esc(c.reportCategory)}</td><td>${esc(c.journalCategory)}</td><td>${esc(c.reportType)}</td></tr>`).join("")}</tbody></table>`;
    }
    if (tab === "auto") {
      return `<table class="data-table"><thead><tr><th>Ručni unos</th><th>Dnevnik</th><th>→ Automatski</th><th>Dnevnik</th><th>Tip</th></tr></thead>
        <tbody>${(data.cashbookAutoRules || []).map((r) => `<tr><td>${esc(r.trigger)}</td><td>${esc(r.triggerLedger)}</td><td>${esc(r.mirror)}</td><td>${esc(r.mirrorLedger)}</td><td>${esc(r.mirrorType)}</td></tr>`).join("")}</tbody></table>`;
    }
    return "";
  }

  function mountFinanceReportsPage(root, api) {
    migrate(api.getData());
    const year = new Date().getFullYear();
    const q = Math.ceil((new Date().getMonth() + 1) / 3);
    let settingsTab = "stavke";

    function render() {
      const data = api.getData();
      const qSum = summarizeQuarter(data, year, q);
      const ySum = summarizeYearFinancial(data, year);
      const esc = api.escapeHtml;

      root.innerHTML = `
        <section class="card">
          <h2 class="section-title">Kvartalno — Obračunski list (plavi)</h2>
          <p class="card-sub">Q${q} / ${year} · +${qSum.inSum.toFixed(2)} / −${qSum.outSum.toFixed(2)} €</p>
          <button type="button" class="btn btn-secondary btn-sm" id="fr-q-print">Ispis</button>
        </section>
        <section class="card">
          <h2 class="section-title">Godišnje — Financijski list</h2>
          <p class="card-sub">Gotovina: ${ySum.cash.toFixed(2)} € · Žiro: ${ySum.bank.toFixed(2)} € · Ukupno: ${ySum.total.toFixed(2)} €</p>
          <button type="button" class="btn btn-secondary btn-sm" id="fr-y-print">Ispis</button>
        </section>
        <section class="card wide">
          <h2 class="section-title">Postavke financija</h2>
          <nav class="family-tab-nav">
            <button type="button" class="finance-set-tab ${settingsTab === "stavke" ? "is-on" : ""}" data-ftab="stavke">Stavke dnevnika</button>
            <button type="button" class="finance-set-tab ${settingsTab === "kalkulacije" ? "is-on" : ""}" data-ftab="kalkulacije">Kalkulacije</button>
            <button type="button" class="finance-set-tab ${settingsTab === "auto" ? "is-on" : ""}" data-ftab="auto">Automatski unosi</button>
          </nav>
          <div id="finance-settings-body" style="margin-top:12px">${renderSettingsPanel(data, api, settingsTab)}</div>
          <a href="${api.pageUrl("pages/blagajna.html")}" class="btn btn-primary btn-sm" style="margin-top:12px">Blagajnički dnevnici</a>
        </section>`;

      const printDoc = (title, body) => {
        const w = window.open("", "_blank");
        if (!w) return api.showToast("Omogućite skočne prozore");
        w.document.write(`<html><head><title>${title}</title></head><body class="print-doc">${body}</body></html>`);
        w.document.close();
        w.print();
      };

      root.querySelector("#fr-q-print")?.addEventListener("click", () => {
        printDoc(`Obračunski Q${q}/${year}`, `<h2>OBRAČUNSKI LIST</h2><p>Q${q} ${year}</p><p>Primitci: ${qSum.inSum.toFixed(2)} €</p><p>Izdaci: ${qSum.outSum.toFixed(2)} €</p>`);
      });
      root.querySelector("#fr-y-print")?.addEventListener("click", () => {
        printDoc(`Financijski ${year}`, `<h2>FINANCIJSKI LIST ${year}</h2><p>Ukupno: ${ySum.total.toFixed(2)} €</p>`);
      });
      root.querySelectorAll(".finance-set-tab").forEach((btn) => {
        btn.addEventListener("click", () => {
          settingsTab = btn.dataset.ftab;
          render();
        });
      });
    }

    render();
  }

  function enhanceCashbookToolbar(root, api) {
    migrate(api.getData());
    const bar = root.querySelector(".racuni-toolbar");
    if (!bar || bar.querySelector("#cb-ledger")) return;

    const sel = document.createElement("select");
    sel.id = "cb-ledger";
    sel.innerHTML = `<option value="sve">Svi dnevnici</option><option value="plavi">Plavi dnevnik</option><option value="crveni">Crveni dnevnik</option>`;
    bar.insertBefore(sel, bar.children[1] || null);

    const link = document.createElement("a");
    link.href = api.pageUrl("pages/financijska-izvjestaja.html");
    link.className = "btn btn-ghost btn-sm";
    link.textContent = "Izvješća i postavke";
    bar.appendChild(link);
    return sel;
  }

  global.PastoralFinanceAdv = {
    migrate,
    DEFAULT_CATEGORIES,
    applyAutoRules,
    summarizeQuarter,
    summarizeYearFinancial,
    mountFinanceReportsPage,
    enhanceCashbookToolbar,
  };
})(typeof window !== "undefined" ? window : global);
