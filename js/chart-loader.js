/**
 * Učitavanje Chart.js (CDN) — jednom po sesiji
 */
(function (global) {
  const CHART_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js";

  function loadChartJs() {
    if (global.Chart) return Promise.resolve(global.Chart);
    if (global.__pastoralChartLoad) return global.__pastoralChartLoad;

    global.__pastoralChartLoad = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = CHART_URL;
      s.async = true;
      s.onload = () => resolve(global.Chart);
      s.onerror = () => {
        global.__pastoralChartLoad = null;
        reject(new Error("Chart.js nije učitan"));
      };
      document.head.appendChild(s);
    });

    return global.__pastoralChartLoad;
  }

  global.PastoralChartLoader = { loadChartJs };
})(typeof window !== "undefined" ? window : global);
