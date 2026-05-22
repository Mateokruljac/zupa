/**
 * Dugovanja prema župi — agregacija lukna, nakana, sakramenata
 */
(function (global) {
  const CATEGORIES = [
    { id: "lukno", label: "Lukno", color: "#5c2e3a" },
    { id: "nakane", label: "Misne nakane", color: "#3d5a80" },
    { id: "krsenje", label: "Krštenja", color: "#2d6a4f" },
    { id: "prva-pricest", label: "Prva pričest", color: "#7c5c2e" },
    { id: "krizma", label: "Krizma", color: "#6b4c9a" },
    { id: "vjencanje", label: "Vjenčanja", color: "#9b2c5c" },
    { id: "pogreb", label: "Pogrebi", color: "#4a4a4a" },
    { id: "pomazanje", label: "Pomazanje", color: "#b45309" },
    { id: "ostalo", label: "Ostalo", color: "#6d6760" },
  ];

  function yearFromIso(iso) {
    if (!iso || iso.length < 4) return new Date().getFullYear();
    return Number(iso.slice(0, 4)) || new Date().getFullYear();
  }

  function catMeta(id) {
    return CATEGORIES.find((c) => c.id === id) || { id, label: id, color: "#6d6760" };
  }

  function push(rows, item) {
    if (!item || Number(item.amount) <= 0) return;
    rows.push(item);
  }

  function collectDebts(data, opts = {}) {
    const onlyUnpaid = opts.onlyUnpaid !== false;
    const rows = [];
    const defLukno = data.luknoDefaultAmount ?? 150;

    (data.families || []).forEach((fam) => {
      (fam.contributions || []).forEach((c) => {
        const amt = Number(c.luknoAmount) || defLukno;
        const paid = !!c.luknoPaid;
        if (onlyUnpaid && paid) return;
        if (!onlyUnpaid && !paid && amt <= 0) return;
        push(rows, {
          id: `lukno_${fam.id}_${c.year}`,
          category: "lukno",
          year: Number(c.year),
          amount: amt,
          label: `Lukno ${c.year} — ${fam.surname}`,
          sublabel: fam.address || "",
          contact: fam.phone || fam.surname,
          dueDate: c.luknoPaidAt || "",
          paid,
          familyId: fam.id,
          link: `pages/obitelji.html?family=${encodeURIComponent(fam.id)}`,
          source: { type: "contribution", familyId: fam.id, year: c.year },
        });
      });
    });

    (data.intentions || []).forEach((n) => {
      const amt = Number(n.stipend) || 0;
      if (amt <= 0) return;
      const paid = !!n.paid;
      if (onlyUnpaid && paid) return;
      push(rows, {
        id: `nakana_${n.id}`,
        category: "nakane",
        year: yearFromIso(n.date),
        amount: amt,
        label: n.intentionFor || "Nakana",
        sublabel: `${n.date || ""} · misa ${n.massTime || ""}`,
        contact: n.requestedBy || "",
        dueDate: n.date || "",
        paid,
        link: `pages/nakane.html?date=${encodeURIComponent(n.date || "")}`,
        source: { type: "intention", id: n.id },
      });
    });

    const sacrament = (list, key, category, labelFn, dateFn) => {
      (list || []).forEach((r) => {
        const amt = Number(r.stipend) || 0;
        if (amt <= 0) return;
        const paid = !!r.stipendPaid;
        if (onlyUnpaid && paid) return;
        const dt = dateFn(r);
        push(rows, {
          id: `${category}_${r.id}`,
          category,
          year: yearFromIso(dt),
          amount: amt,
          label: labelFn(r),
          sublabel: dt ? dt : "",
          contact: r.parents || r.familyContact || r.couple || "",
          dueDate: dt,
          paid,
          link: null,
          source: { type: key, id: r.id },
        });
      });
    };

    sacrament(data.baptisms, "baptisms", "krsenje", (b) => b.childName, (b) => b.baptismDate);
    sacrament(data.weddings, "weddings", "vjencanje", (w) => w.couple, (w) => w.weddingDate);
    sacrament(data.funerals, "funerals", "pogreb", (f) => f.deceased, (f) => f.funeralDate);
    sacrament(data.anointing, "anointing", "pomazanje", (a) => a.person, (a) => a.scheduled);

    (data.firstCommunion || []).forEach((g) => {
      const amt = Number(g.groupFee) || 0;
      if (amt <= 0) return;
      const paid = !!g.groupFeePaid;
      if (onlyUnpaid && paid) return;
      push(rows, {
        id: `pricest_${g.id}`,
        category: "prva-pricest",
        year: Number(g.year) || yearFromIso(g.ceremonyDate),
        amount: amt,
        label: g.groupName || "Skupina prve pričesti",
        sublabel: g.ceremonyDate || "",
        contact: (g.catechists || [])[0]?.name || "",
        dueDate: g.ceremonyDate || "",
        paid,
        link: "pages/prva-pricest.html",
        source: { type: "firstCommunion", id: g.id },
      });
    });

    (data.confirmations || []).forEach((g) => {
      const amt = Number(g.groupFee) || 0;
      if (amt <= 0) return;
      const paid = !!g.groupFeePaid;
      if (onlyUnpaid && paid) return;
      push(rows, {
        id: `krizma_${g.id}`,
        category: "krizma",
        year: Number(g.year) || yearFromIso(g.ceremonyDate),
        amount: amt,
        label: `Krizma ${g.year}`,
        sublabel: `${g.candidates?.length || 0} kandidata`,
        contact: (g.catechists || [])[0]?.name || "",
        dueDate: g.ceremonyDate || "",
        paid,
        link: "pages/krizma.html",
        source: { type: "confirmations", id: g.id },
      });
    });

    (data.parishDebts || []).forEach((d) => {
      const amt = Number(d.amount) || 0;
      if (amt <= 0) return;
      const paid = !!d.paid;
      if (onlyUnpaid && paid) return;
      push(rows, {
        id: `misc_${d.id}`,
        category: d.category || "ostalo",
        year: Number(d.year) || yearFromIso(d.dueDate),
        amount: amt,
        label: d.label || "Stavka",
        sublabel: d.notes || "",
        contact: d.contact || "",
        dueDate: d.dueDate || "",
        paid,
        link: null,
        source: { type: "parishDebts", id: d.id },
      });
    });

    return rows.sort((a, b) => {
      if (a.paid !== b.paid) return a.paid ? 1 : -1;
      if (a.year !== b.year) return b.year - a.year;
      return (b.dueDate || "").localeCompare(a.dueDate || "");
    });
  }

  function getYearsFromDebts(rows) {
    const set = new Set(rows.map((r) => r.year));
    const cur = new Date().getFullYear();
    set.add(cur);
    set.add(cur - 1);
    return [...set].filter(Boolean).sort((a, b) => b - a);
  }

  function filterDebts(rows, filters) {
    let out = rows;
    if (filters.category && filters.category !== "all") {
      out = out.filter((r) => r.category === filters.category);
    }
    if (filters.year && filters.year !== "all") {
      out = out.filter((r) => r.year === Number(filters.year));
    }
    if (filters.status === "unpaid") out = out.filter((r) => !r.paid);
    else if (filters.status === "paid") out = out.filter((r) => r.paid);
    if (filters.q) {
      const q = filters.q.toLowerCase();
      out = out.filter(
        (r) =>
          r.label.toLowerCase().includes(q) ||
          (r.contact || "").toLowerCase().includes(q) ||
          (r.sublabel || "").toLowerCase().includes(q) ||
          catMeta(r.category).label.toLowerCase().includes(q)
      );
    }
    return out;
  }

  function summarize(rows) {
    const unpaid = rows.filter((r) => !r.paid);
    const totalUnpaid = unpaid.reduce((s, r) => s + r.amount, 0);
    const byCategory = {};
    CATEGORIES.forEach((c) => {
      byCategory[c.id] = { count: 0, sum: 0 };
    });
    unpaid.forEach((r) => {
      if (!byCategory[r.category]) byCategory[r.category] = { count: 0, sum: 0 };
      byCategory[r.category].count++;
      byCategory[r.category].sum += r.amount;
    });
    return { totalUnpaid, unpaidCount: unpaid.length, paidCount: rows.filter((r) => r.paid).length, byCategory };
  }

  function markDebtPaid(data, source) {
    if (!source) return false;
    const FC = global.PastoralFamilyCrud;
    switch (source.type) {
      case "contribution": {
        const fam = (data.families || []).find((f) => f.id === source.familyId);
        const row = fam?.contributions?.find((c) => c.year === source.year);
        if (!row) return false;
        row.luknoPaid = true;
        row.luknoPaidAt = new Date().toISOString().slice(0, 10);
        return true;
      }
      case "intention": {
        const n = data.intentions?.find((x) => x.id === source.id);
        if (!n) return false;
        n.paid = true;
        n.paymentId = n.paymentId || `MAN-${Date.now().toString(36).slice(-6).toUpperCase()}`;
        n.paidAt = new Date().toISOString();
        return true;
      }
      case "baptisms":
      case "weddings":
      case "funerals":
      case "anointing": {
        const n = data[source.type]?.find((x) => x.id === source.id);
        if (!n) return false;
        n.stipendPaid = true;
        n.stipendPaidAt = new Date().toISOString().slice(0, 10);
        return true;
      }
      case "firstCommunion": {
        const g = data.firstCommunion?.find((x) => x.id === source.id);
        if (!g) return false;
        g.groupFeePaid = true;
        g.groupFeePaidAt = new Date().toISOString().slice(0, 10);
        return true;
      }
      case "confirmations": {
        const g = data.confirmations?.find((x) => x.id === source.id);
        if (!g) return false;
        g.groupFeePaid = true;
        g.groupFeePaidAt = new Date().toISOString().slice(0, 10);
        return true;
      }
      case "parishDebts": {
        const d = data.parishDebts?.find((x) => x.id === source.id);
        if (!d) return false;
        d.paid = true;
        d.paidAt = new Date().toISOString().slice(0, 10);
        return true;
      }
      default:
        return false;
    }
  }

  function migrateFees(data) {
    const touch = (arr) => {
      (arr || []).forEach((r) => {
        if (r.stipend == null) r.stipend = 0;
        if (r.stipendPaid == null) r.stipendPaid = r.stipend === 0;
        if (!r.stipendPaidAt) r.stipendPaidAt = "";
      });
    };
    touch(data.baptisms);
    touch(data.weddings);
    touch(data.funerals);
    touch(data.anointing);
    (data.firstCommunion || []).forEach((g) => {
      if (g.groupFee == null) g.groupFee = 0;
      if (g.groupFeePaid == null) g.groupFeePaid = g.groupFee === 0;
    });
    (data.confirmations || []).forEach((g) => {
      if (g.groupFee == null) g.groupFee = 0;
      if (g.groupFeePaid == null) g.groupFeePaid = g.groupFee === 0;
    });
    if (!Array.isArray(data.parishDebts)) data.parishDebts = [];
    return data;
  }

  function mountDebtsPage(root, api) {
    if (!root) return;

    let filters = {
      category: new URLSearchParams(location.search).get("cat") || "all",
      year: new URLSearchParams(location.search).get("year") || "all",
      status: "unpaid",
      q: "",
    };

    function render() {
      const data = api.getData();
      const allRows = collectDebts(data, { onlyUnpaid: false });
      const years = getYearsFromDebts(allRows);
      const filtered = filterDebts(allRows, filters);
      const summary = summarize(filtered);
      const esc = api.escapeHtml;
      const fmt = api.fmtDate;

      const catChips = [{ id: "all", label: "Sve" }, ...CATEGORIES]
        .map((c) => {
          const active = filters.category === c.id;
          const cnt =
            c.id === "all"
              ? allRows.filter((r) => !r.paid).length
              : allRows.filter((r) => !r.paid && r.category === c.id).length;
          return `<button type="button" class="debts-cat-chip ${active ? "is-active" : ""}" data-cat="${c.id}">${esc(c.label)}${cnt ? `<span class="debts-cat-count">${cnt}</span>` : ""}</button>`;
        })
        .join("");

      const yearOpts = `<option value="all">Sve godine</option>${years.map((y) => `<option value="${y}" ${filters.year === String(y) ? "selected" : ""}>${y}</option>`).join("")}`;

      const catSummary = CATEGORIES.filter((c) => summary.byCategory[c.id]?.count)
        .map((c) => {
          const s = summary.byCategory[c.id];
          return `<div class="debts-cat-stat" style="--cat-color:${c.color}"><span class="debts-cat-stat-label">${esc(c.label)}</span><strong>${s.count}</strong><small>${s.sum.toFixed(2)} €</small></div>`;
        })
        .join("");

      root.innerHTML = `
        <div class="debts-toolbar card">
          <div class="debts-filters-row">
            <div class="form-group"><label>Godina</label><select id="debts-year">${yearOpts}</select></div>
            <div class="form-group"><label>Status</label><select id="debts-status">
              <option value="unpaid" ${filters.status === "unpaid" ? "selected" : ""}>Samo neplaćeno</option>
              <option value="all" ${filters.status === "all" ? "selected" : ""}>Sve stavke</option>
              <option value="paid" ${filters.status === "paid" ? "selected" : ""}>Plaćeno</option>
            </select></div>
            <div class="form-group form-wide"><label>Pretraži</label><input type="search" id="debts-search" value="${esc(filters.q)}" placeholder="Prezime, nakana, sakrament…" /></div>
          </div>
          <div class="debts-cat-chips" role="group" aria-label="Kategorija">${catChips}</div>
        </div>
        <div class="kpi-row debts-kpi-row">
          <article class="card kpi-card"><p class="card-label">Neplaćeno (filtar)</p><p class="card-value">${summary.unpaidCount}</p><p class="card-sub">${summary.totalUnpaid.toFixed(2)} €</p></article>
          <article class="card kpi-card"><p class="card-label">Plaćeno u prikazu</p><p class="card-value">${summary.paidCount}</p></article>
          ${catSummary ? `<section class="card wide debts-cat-summary">${catSummary}</section>` : ""}
        </div>
        <section class="card">
          <div id="debts-table-mount"></div>
        </section>`;

      const tableRows = filtered.map((r) => {
        const cm = catMeta(r.category);
        return {
          ...r,
          categoryLabel: cm.label,
          categoryBadge: `<span class="badge debts-badge" style="background:${cm.color}22;color:${cm.color}">${esc(cm.label)}</span>`,
          amountFmt: `${r.amount.toFixed(2)} €`,
          statusBadge: r.paid
            ? '<span class="badge badge-done">plaćeno</span>'
            : '<span class="badge badge-urgent">duguje</span>',
          dueFmt: r.dueDate ? fmt(r.dueDate) : "—",
          actions: r.paid
            ? (r.link ? `<a href="${api.pageUrl(r.link)}" class="btn btn-ghost btn-sm">Otvori</a>` : "")
            : `<button type="button" class="btn btn-primary btn-sm" data-mark-paid="${esc(r.id)}">Označi plaćeno</button>
               <a href="${api.pageUrl(`pages/racuni.html?novi=1&platitelj=${encodeURIComponent(r.contact || r.label)}&opis=${encodeURIComponent(r.label)}&iznos=${r.amount}&kat=${r.category}`)}" class="btn btn-ghost btn-sm">Račun</a>
               ${r.category === "nakane" ? `<button type="button" class="btn btn-ghost btn-sm" data-pay-nakana="${esc(r.id)}">Plati</button>` : ""}
               ${r.link ? `<a href="${api.pageUrl(r.link)}" class="btn btn-ghost btn-sm">Detalj</a>` : ""}`,
        };
      });

      global.PastoralTableKit?.mountDataTable({
        mount: document.getElementById("debts-table-mount"),
        rows: tableRows,
        columns: [
          { key: "categoryBadge", label: "Kategorija", render: (row) => row.categoryBadge },
          { key: "year", label: "Godina" },
          { key: "label", label: "Opis", render: (row) => `<strong>${esc(row.label)}</strong><br><small>${esc(row.sublabel || "")}</small>` },
          { key: "contact", label: "Kontakt / obitelj" },
          { key: "dueFmt", label: "Datum" },
          { key: "amountFmt", label: "Iznos" },
          { key: "statusBadge", label: "Status", render: (row) => row.statusBadge },
          { key: "actions", label: "", render: (row) => row.actions },
        ],
        exportName: "dugovanja_zupe",
        pageSize: 15,
      });

      root.querySelectorAll(".debts-cat-chip").forEach((btn) => {
        btn.addEventListener("click", () => {
          filters.category = btn.dataset.cat || "all";
          render();
        });
      });
      root.querySelector("#debts-year")?.addEventListener("change", (e) => {
        filters.year = e.target.value;
        render();
      });
      root.querySelector("#debts-status")?.addEventListener("change", (e) => {
        filters.status = e.target.value;
        render();
      });
      let searchTimer;
      root.querySelector("#debts-search")?.addEventListener("input", (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
          filters.q = e.target.value.trim();
          render();
        }, 200);
      });

      if (!root.dataset.debtsBound) {
        root.dataset.debtsBound = "1";
        root.addEventListener("click", (ev) => {
          const mark = ev.target.closest("[data-mark-paid]");
          const pay = ev.target.closest("[data-pay-nakana]");
          const data = api.getData();
          const all = collectDebts(data, { onlyUnpaid: false });
          if (mark) {
            const row = all.find((r) => r.id === mark.dataset.markPaid);
            if (row && markDebtPaid(data, row.source)) {
              api.saveData(data);
              api.showToast("Označeno kao plaćeno");
              render();
            }
          }
          if (pay) {
            const row = all.find((r) => r.id === pay.dataset.payNakana);
            const n = data.intentions?.find((x) => x.id === row?.source?.id);
            if (!n || !global.PastoralPayment) {
              api.showToast("Modul plaćanja nije dostupan");
              return;
            }
            global.PastoralPayment.runSimulation({
              amount: Number(n.stipend) || 0,
              title: n.intentionFor,
              subtitle: `${n.date} · ${n.massTime}`,
              onSuccess: () => {
                n.paid = true;
                n.paymentId = `PAY-${Date.now().toString(36).slice(-8).toUpperCase()}`;
                n.paidAt = new Date().toISOString();
                api.saveData(data);
                api.showToast("Nakana plaćena");
                render();
              },
            });
          }
        });
      }
    }

    render();
  }

  global.PastoralDebts = {
    CATEGORIES,
    collectDebts,
    filterDebts,
    summarize,
    markDebtPaid,
    migrateFees,
    mountDebtsPage,
    getUnpaidCount(data) {
      return collectDebts(data, { onlyUnpaid: true }).length;
    },
  };
})(typeof window !== "undefined" ? window : global);
