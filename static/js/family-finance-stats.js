(function () {
  "use strict";

  function formatMoney(amount) {
    const number = Number(amount);
    if (!Number.isFinite(number)) return "—";
    return number.toFixed(2) + " €";
  }

  function fillCategoryList(list, rows) {
    if (!list) return;
    list.replaceChildren();
    if (!rows || !rows.length) {
      const empty = document.createElement("li");
      empty.className = "empty-state";
      empty.textContent = "Nema uplata.";
      list.append(empty);
      return;
    }
    const total = rows.reduce((sum, row) => {
      const amount = Number(row.total);
      return sum + (Number.isFinite(amount) ? amount : 0);
    }, 0);
    rows.forEach((row) => {
      const item = document.createElement("li");
      const rowLine = document.createElement("div");
      rowLine.className = "family-finance-stats__row";
      const label = document.createElement("span");
      label.textContent = row.label || row.category || "";
      const value = document.createElement("strong");
      value.textContent = formatMoney(row.total);
      rowLine.append(label, value);
      item.append(rowLine);
      if (total > 0) {
        const amount = Number(row.total);
        const share = Number.isFinite(amount) ? Math.max(0, Math.min(100, (amount / total) * 100)) : 0;
        const bar = document.createElement("span");
        bar.className = "family-finance-stats__bar";
        bar.setAttribute("aria-hidden", "true");
        const fill = document.createElement("i");
        fill.style.width = share.toFixed(1) + "%";
        bar.append(fill);
        item.append(bar);
      }
      list.append(item);
    });
  }

  function normalizeYear(value) {
    const trimmed = String(value || "").trim();
    if (!trimmed) return "";
    const year = Number(trimmed);
    if (!Number.isInteger(year) || year < 1900 || year > 2100) return null;
    return String(year);
  }

  function applyFilter(root, yearValue) {
    const totals = root._financeTotals;
    if (!totals) return;
    const categoryTitle = root.querySelector("[data-finance-category-title]");
    const categoryList = root.querySelector("[data-finance-totals-by-category]");
    const grandLabel = root.querySelector("[data-finance-grand-label]");
    const grandValue = root.querySelector("[data-finance-totals-grand]");
    const yearInput = root.querySelector("[data-finance-year-input]");
    const allButton = root.querySelector("[data-finance-year-all]");
    const selectedYear = yearValue === "" || yearValue == null ? "" : String(yearValue);

    if (yearInput && yearInput.value !== selectedYear) {
      yearInput.value = selectedYear;
    }
    if (allButton) {
      const isAll = !selectedYear;
      allButton.classList.toggle("is-selected", isAll);
      allButton.setAttribute("aria-pressed", isAll ? "true" : "false");
    }

    if (selectedYear) {
      const yearRow = (totals.byYear || []).find(
        (row) => String(row.year) === selectedYear
      );
      root.classList.add("is-year-filtered");
      if (categoryTitle) {
        categoryTitle.textContent = "Po kategoriji (" + selectedYear + ".)";
      }
      fillCategoryList(categoryList, yearRow ? yearRow.byCategory || [] : []);
      if (grandLabel) grandLabel.textContent = "Ukupno " + selectedYear + ".";
      if (grandValue) {
        grandValue.textContent = formatMoney(yearRow ? yearRow.total : 0);
      }
      return;
    }

    root.classList.remove("is-year-filtered");
    if (categoryTitle) categoryTitle.textContent = "Po kategoriji (ukupno)";
    fillCategoryList(categoryList, totals.byCategory || []);
    if (grandLabel) grandLabel.textContent = "Ukupno uplaćeno";
    if (grandValue) grandValue.textContent = formatMoney(totals.grandTotal || 0);
  }

  function commitYearInput(root) {
    const yearInput = root.querySelector("[data-finance-year-input]");
    if (!yearInput) return;
    const normalized = normalizeYear(yearInput.value);
    if (normalized === null) {
      yearInput.setCustomValidity("Unesite ispravnu godinu (npr. 2025).");
      yearInput.reportValidity();
      return;
    }
    yearInput.setCustomValidity("");
    applyFilter(root, normalized);
  }

  function bindRoot(root) {
    if (!root || root.dataset.financeBound === "1") return;
    root.dataset.financeBound = "1";
    root.addEventListener("click", (event) => {
      const allButton = event.target.closest("[data-finance-year-all]");
      if (allButton && root.contains(allButton)) {
        applyFilter(root, "");
        return;
      }
      const searchButton = event.target.closest("[data-finance-year-search]");
      if (searchButton && root.contains(searchButton)) {
        commitYearInput(root);
      }
    });
    root.addEventListener("keydown", (event) => {
      const yearInput = event.target.closest("[data-finance-year-input]");
      if (!yearInput || !root.contains(yearInput)) return;
      if (event.key !== "Enter") return;
      event.preventDefault();
      commitYearInput(root);
    });
  }

  function syncFilterControls(root) {
    const filters = root.querySelector("[data-finance-year-filter]");
    if (!filters) return;
    if (filters.querySelector("[data-finance-year-input]")) return;
    filters.replaceChildren();

    const allButton = document.createElement("button");
    allButton.type = "button";
    allButton.className = "family-finance-filter-pill is-selected";
    allButton.dataset.financeYearAll = "";
    allButton.setAttribute("aria-pressed", "true");
    allButton.textContent = "Sve ukupno";
    filters.append(allButton);

    const field = document.createElement("div");
    field.className = "family-finance-year-field";
    const input = document.createElement("input");
    input.className = "form-control family-finance-year-input";
    input.type = "number";
    input.inputMode = "numeric";
    input.min = "1900";
    input.max = "2100";
    input.step = "1";
    input.placeholder = "Godina";
    input.dataset.financeYearInput = "";
    input.setAttribute("aria-label", "Filtriraj po godini");
    const searchButton = document.createElement("button");
    searchButton.type = "button";
    searchButton.className = "family-finance-year-search";
    searchButton.dataset.financeYearSearch = "";
    searchButton.title = "Filtriraj po godini";
    searchButton.setAttribute("aria-label", "Filtriraj po godini");
    searchButton.innerHTML =
      '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M16.2 16.2 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
    field.append(input, searchButton);
    filters.append(field);
  }

  function initRoot(root, totals) {
    if (!root) return;
    bindRoot(root);
    root._financeTotals = totals || { byYear: [], byCategory: [], grandTotal: 0 };
    const hasTotals = Number(root._financeTotals.grandTotal) > 0;
    root.hidden = !hasTotals;
    if (!hasTotals) return;
    syncFilterControls(root);
    const yearInput = root.querySelector("[data-finance-year-input]");
    const currentYear = yearInput ? normalizeYear(yearInput.value) : "";
    applyFilter(root, currentYear || "");
    if (currentYear === null && yearInput) yearInput.value = "";
  }

  function readTotalsFromScript(scriptId) {
    const element = document.getElementById(scriptId);
    if (!element) return null;
    try {
      return JSON.parse(element.textContent);
    } catch (error) {
      return null;
    }
  }

  document.querySelectorAll("[data-finance-stats][data-finance-totals-script]").forEach((root) => {
    initRoot(root, readTotalsFromScript(root.dataset.financeTotalsScript));
  });

  window.familyFinanceStats = {
    formatMoney,
    paint(root, totals) {
      initRoot(root, totals || { byYear: [], byCategory: [], grandTotal: 0 });
    },
  };
})();
