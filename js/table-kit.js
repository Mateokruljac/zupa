/**
 * Tablice: paginacija, pretraga, CSV/Excel export & import
 */
(function (global) {
  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function parseCsv(text) {
    const lines = text.trim().split(/\r?\n/).filter(Boolean);
    if (!lines.length) return { headers: [], rows: [] };
    const split = (line) => line.split(/[,;\t]/).map((c) => c.trim().replace(/^"|"$/g, ""));
    const headers = split(lines[0]);
    const rows = lines.slice(1).map((line) => {
      const cells = split(line);
      const o = {};
      headers.forEach((h, i) => {
        o[h] = cells[i] ?? "";
      });
      return o;
    });
    return { headers, rows };
  }

  function rowsToCsv(headers, rows) {
    const esc = (v) => {
      const s = String(v ?? "");
      return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
    };
    return [headers.map(esc).join(","), ...rows.map((r) => headers.map((h) => esc(r[h])).join(","))].join("\n");
  }

  function downloadText(filename, content, mime) {
    const blob = new Blob(["\ufeff" + content], { type: mime || "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function parseExcelFile(file) {
    return new Promise((resolve, reject) => {
      if (!global.XLSX) {
        reject(new Error("XLSX biblioteka nije učitana"));
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const wb = XLSX.read(e.target.result, { type: "array" });
          const sheet = wb.Sheets[wb.SheetNames[0]];
          const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });
          const headers = json.length ? Object.keys(json[0]) : [];
          resolve({ headers, rows: json });
        } catch (err) {
          reject(err);
        }
      };
      reader.onerror = () => reject(new Error("Čitanje datoteke nije uspjelo"));
      reader.readAsArrayBuffer(file);
    });
  }

  /**
   * @param {object} opts
   * @param {HTMLElement} opts.mount
   * @param {Array} opts.rows
   * @param {Array<{key:string,label:string,render?}>} opts.columns
   * @param {string} opts.exportName
   * @param {function} [opts.onImport] (rows) => void
   * @param {number} [opts.pageSize]
   */
  function mountDataTable(opts) {
    let pageSize = opts.pageSize || 10;
    let allRows = [...(opts.rows || [])];
    let page = 1;
    let search = "";

    const state = { get rows() { return allRows; }, set rows(v) { allRows = v; page = 1; render(); }, refresh: () => render() };

    function getFiltered() {
      if (!search.trim()) return allRows;
      const q = search.toLowerCase();
      return allRows.filter((row) =>
        opts.columns.some((c) => String(row[c.key] ?? "").toLowerCase().includes(q))
      );
    }

    function render() {
      const filtered = getFiltered();
      const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
      if (page > totalPages) page = totalPages;
      const start = (page - 1) * pageSize;
      const pageRows = filtered.slice(start, start + pageSize);

      opts.mount.innerHTML = `
        <div class="table-kit-toolbar">
          <input type="search" class="table-kit-search" placeholder="Pretraži…" value="${escapeHtml(search)}" />
          <span class="table-kit-meta">${filtered.length} zapisa · str. ${page}/${totalPages}</span>
          <div class="table-kit-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-tk-prev ${page <= 1 ? "disabled" : ""}>‹</button>
            <button type="button" class="btn btn-ghost btn-sm" data-tk-next ${page >= totalPages ? "disabled" : ""}>›</button>
            <select class="table-kit-pagesize" title="Po stranici">
              ${[5, 10, 25, 50].map((n) => `<option value="${n}" ${n === pageSize ? "selected" : ""}>${n}/str</option>`).join("")}
            </select>
            <button type="button" class="btn btn-secondary btn-sm" data-tk-export-csv">CSV</button>
            <button type="button" class="btn btn-secondary btn-sm" data-tk-export-xlsx">Excel</button>
            <label class="btn btn-ghost btn-sm" style="cursor:pointer">Import<input type="file" data-tk-import hidden accept=".csv,.xlsx,.xls,text/csv" /></label>
          </div>
        </div>
        <div class="table-wrap"><table class="data-table"><thead><tr>${opts.columns.map((c) => `<th>${escapeHtml(c.label)}</th>`).join("")}</tr></thead>
        <tbody>${pageRows.length
          ? pageRows.map((row) => {
              const attrs = opts.rowAttrs
                ? Object.entries(opts.rowAttrs(row))
                    .map(([k, v]) => `${k}="${escapeHtml(String(v))}"`)
                    .join(" ")
                : "";
              return `<tr ${attrs}>${opts.columns.map((c) => `<td>${c.render ? c.render(row) : escapeHtml(row[c.key] ?? "—")}</td>`).join("")}</tr>`;
            }).join("")
          : `<tr><td colspan="${opts.columns.length}" class="empty-state">Nema podataka.</td></tr>`}</tbody></table></div>`;

      const mount = opts.mount;

      mount.querySelector(".table-kit-search")?.addEventListener("input", (e) => {
        search = e.target.value;
        page = 1;
        render();
      });

      mount.querySelector("[data-tk-prev]")?.addEventListener("click", () => {
        if (page > 1) {
          page--;
          render();
        }
      });
      mount.querySelector("[data-tk-next]")?.addEventListener("click", () => {
        const tp = Math.max(1, Math.ceil(getFiltered().length / pageSize));
        if (page < tp) {
          page++;
          render();
        }
      });

      mount.querySelector(".table-kit-pagesize")?.addEventListener("change", (e) => {
        pageSize = Number(e.target.value);
        page = 1;
        render();
      });

      mount.querySelector("[data-tk-export-csv]")?.addEventListener("click", () => {
        const labels = opts.columns.map((c) => c.label);
        const exportRows = getFiltered().map((row) => {
          const o = {};
          opts.columns.forEach((c) => {
            o[c.label] = row[c.key];
          });
          return o;
        });
        downloadText(`${opts.exportName || "export"}.csv`, rowsToCsv(labels, exportRows));
      });

      mount.querySelector("[data-tk-export-xlsx]")?.addEventListener("click", () => {
        if (!global.XLSX) {
          alert("Učitaj stranicu s Excel podrškom ili koristi CSV.");
          return;
        }
        const data = getFiltered().map((row) => {
          const o = {};
          opts.columns.forEach((c) => { o[c.label] = row[c.key]; });
          return o;
        });
        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Podaci");
        XLSX.writeFile(wb, `${opts.exportName || "export"}.xlsx`);
      });

      mount.querySelector("[data-tk-import]")?.addEventListener("change", async (e) => {
        const file = e.target.files?.[0];
        if (!file || !opts.onImport) return;
        try {
          let parsed;
          if (file.name.match(/\.xlsx?$/i)) parsed = await parseExcelFile(file);
          else parsed = parseCsv(await file.text());
          opts.onImport(parsed.rows);
          e.target.value = "";
        } catch (err) {
          alert(err.message || "Import nije uspio");
        }
      });
    }

    render();
    return state;
  }

  global.PastoralTableKit = {
    mountDataTable,
    parseCsv,
    parseExcelFile,
    rowsToCsv,
    downloadText,
  };
})(typeof window !== "undefined" ? window : global);
