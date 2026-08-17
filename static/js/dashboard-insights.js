/**
 * Chart.js integracija za operativni dashboard i izvještaje.
 * Podaci dolaze iz Django json_script elemenata, bez inline JavaScripta.
 */
(function (global) {
  "use strict";

  const chartInstances = new Map();
  const HR_MONTHS = {
    Jan: "Sij", Feb: "Velj", Mar: "Ožu", Apr: "Tra", May: "Svi", Jun: "Lip",
    Jul: "Srp", Aug: "Kol", Sep: "Ruj", Oct: "Lis", Nov: "Stu", Dec: "Pro",
  };

  function parseData(id) {
    const source = document.getElementById(id);
    if (!source) return [];
    try {
      return JSON.parse(source.textContent || "[]");
    } catch {
      return [];
    }
  }

  function palette() {
    const dark = document.documentElement.dataset.colorScheme === "dark";
    return {
      text: dark ? "#d6d3d1" : "#6d6760",
      grid: dark ? "rgba(255,255,255,.09)" : "rgba(73,65,57,.10)",
      surface: dark ? "#292524" : "#ffffff",
      green: "#2f6a56",
      greenSoft: dark ? "rgba(71,143,112,.28)" : "rgba(47,106,86,.16)",
      rose: "#9a5962",
      roseSoft: dark ? "rgba(185,96,108,.25)" : "rgba(154,89,98,.14)",
      blue: "#456b86",
      blueSoft: dark ? "rgba(86,137,174,.28)" : "rgba(69,107,134,.14)",
    };
  }

  function monthLabel(label) {
    return HR_MONTHS[label] || label || "—";
  }

  function money(value) {
    return `${Number(value || 0).toLocaleString("hr-HR", { maximumFractionDigits: 2 })} €`;
  }

  function ensureCanvas(container) {
    let canvas = container.querySelector("canvas");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.setAttribute("role", "img");
      canvas.setAttribute("aria-label", container.getAttribute("aria-label") || "Grafički prikaz podataka");
      container.replaceChildren(canvas);
    }
    return canvas;
  }

  function emptyChart(container) {
    const empty = document.createElement("p");
    empty.className = "pro-chart-empty";
    empty.textContent = "Još nema dovoljno podataka za graf.";
    container.replaceChildren(empty);
  }

  function baseOptions(colors, currency) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 650, easing: "easeOutQuart" },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: colors.surface,
          titleColor: colors.text,
          bodyColor: colors.text,
          borderColor: colors.grid,
          borderWidth: 1,
          padding: 11,
          displayColors: true,
          callbacks: {
            label(context) {
              const value = context.parsed.y ?? context.parsed;
              return ` ${context.dataset.label}: ${currency ? money(value) : Number(value).toLocaleString("hr-HR")}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: { color: colors.text, font: { family: "Source Sans 3", size: 11 } },
        },
        y: {
          beginAtZero: true,
          border: { display: false },
          grid: { color: colors.grid, drawTicks: false },
          ticks: {
            color: colors.text,
            padding: 8,
            font: { family: "Source Sans 3", size: 10 },
            callback: (value) => currency && Number(value) >= 1000 ? `${Number(value) / 1000}k` : value,
          },
        },
      },
    };
  }

  function groupedBarsConfig(container, rows, colors) {
    const series = (container.dataset.series || "in,out").split(",");
    const labels = (container.dataset.labels || "Ulaz,Izlaz").split(",");
    return {
      type: "bar",
      data: {
        labels: rows.map((row) => monthLabel(row.label)),
        datasets: series.map((key, index) => ({
          label: labels[index] || key,
          data: rows.map((row) => Number(row[key]) || 0),
          backgroundColor: index === 0 ? colors.green : colors.rose,
          hoverBackgroundColor: index === 0 ? "#3f8068" : "#ad6a73",
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 30,
          categoryPercentage: 0.66,
          barPercentage: 0.86,
        })),
      },
      options: baseOptions(colors, true),
    };
  }

  function lineConfig(container, rows, colors) {
    const key = (container.dataset.series || "count").split(",")[0];
    const label = (container.dataset.labels || "Vrijednost").split(",")[0];
    const options = baseOptions(colors, false);
    options.elements = { point: { radius: 4, hoverRadius: 6, borderWidth: 2 } };
    return {
      type: "line",
      data: {
        labels: rows.map((row) => monthLabel(row.label)),
        datasets: [{
          label,
          data: rows.map((row) => Number(row[key]) || 0),
          borderColor: colors.blue,
          backgroundColor: colors.blueSoft,
          pointBackgroundColor: colors.surface,
          pointBorderColor: colors.blue,
          fill: true,
          tension: 0.36,
          borderWidth: 3,
        }],
      },
      options,
    };
  }

  function renderChart(container) {
    const rows = parseData(container.dataset.source);
    if (!Array.isArray(rows) || !rows.length) return emptyChart(container);
    if (!global.Chart) {
      container.dataset.chartError = "missing-chartjs";
      return emptyChart(container);
    }
    const previous = chartInstances.get(container);
    if (previous) previous.destroy();
    const canvas = ensureCanvas(container);
    const colors = palette();
    const config = container.dataset.pastoralChart === "line"
      ? lineConfig(container, rows, colors)
      : groupedBarsConfig(container, rows, colors);
    chartInstances.set(container, new global.Chart(canvas, config));
    container.dataset.chartReady = "1";
  }

  function renderCharts() {
    document.querySelectorAll("[data-pastoral-chart]").forEach(renderChart);
  }

  function watchTheme() {
    const observer = new MutationObserver((mutations) => {
      if (mutations.some((item) => item.attributeName === "data-color-scheme")) renderCharts();
    });
    observer.observe(document.documentElement, { attributes: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => { renderCharts(); watchTheme(); });
  } else {
    renderCharts();
    watchTheme();
  }

  global.PastoralInsights = {
    render: renderCharts,
    instances: chartInstances,
  };
})(typeof window !== "undefined" ? window : this);
