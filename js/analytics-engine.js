/**
 * Analitika — Chart.js (nadzorna ploča + traka ispod navigacije)
 */
(function (global) {
  const chartRegistry = new Map();

  const PALETTE = {
    primary: "#5c2e3a",
    accent: "#b8922a",
    liturgy: "#3d5a80",
    finance: "#2d5a45",
    neutral: "#6d6760",
    alert: "#9b3d3d",
    success: "#2d6a4f",
  };

  function themeColor(cssVar, fallback) {
    try {
      const v = getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
      return v || fallback;
    } catch {
      return fallback;
    }
  }

  function getPalette() {
    return {
      primary: themeColor("--primary", PALETTE.primary),
      accent: themeColor("--accent", PALETTE.accent),
      liturgy: PALETTE.liturgy,
      finance: PALETTE.finance,
      neutral: PALETTE.neutral,
      alert: PALETTE.alert,
      success: PALETTE.success,
    };
  }

  function monthKey(d) {
    const x = d instanceof Date ? d : new Date(d);
    return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}`;
  }

  function computeCashbookMonths(data, months = 6) {
    const now = new Date();
    const rows = [];
    for (let i = months - 1; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const mk = monthKey(d);
      const entries = (data.cashbook || []).filter((e) => (e.date || "").startsWith(mk));
      rows.push({
        label: d.toLocaleDateString("hr-HR", { month: "short" }),
        in: entries.filter((e) => e.type === "ulaz").reduce((s, e) => s + (Number(e.amount) || 0), 0),
        out: entries.filter((e) => e.type === "izlaz").reduce((s, e) => s + (Number(e.amount) || 0), 0),
      });
    }
    return rows;
  }

  function computeDebtCategories(data) {
    if (global.PastoralDebts?.collectDebts) {
      const rows = global.PastoralDebts.collectDebts(data, { onlyUnpaid: true });
      const by = {};
      rows.forEach((r) => {
        by[r.category] = (by[r.category] || 0) + 1;
      });
      return Object.entries(by).map(([id, count]) => ({
        id,
        label: global.PastoralDebts.CATEGORIES?.find((c) => c.id === id)?.label || id,
        count,
      }));
    }
    return [];
  }

  function computeStats(data) {
    const now = new Date();
    const thisMonth = monthKey(now);
    const intentionsMonth = data.intentions.filter((n) => n.date?.startsWith(thisMonth));
    const paidMonth = intentionsMonth.filter((n) => n.paid).length;
    const stipendSum = intentionsMonth.reduce((s, n) => s + (Number(n.stipend) || 0), 0);
    const conf = data.confirmations.find((c) => c.year === now.getFullYear()) || data.confirmations[0];
    const sacramentCounts = {
      krštenja: data.baptisms.length,
      vjenčanja: data.weddings.length,
      pogrebi: data.funerals.length,
      krizmanici: conf?.candidates?.length || 0,
    };
    const last6 = [];
    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const mk = monthKey(d);
      last6.push({
        label: d.toLocaleDateString("hr-HR", { month: "short" }),
        count: data.intentions.filter((n) => n.date?.startsWith(mk)).length,
      });
    }
    const y = new Date().getFullYear();
    const families = data.families || [];
    let luknoPaid = 0;
    let luknoUnpaid = 0;
    families.forEach((f) => {
      const row = (f.contributions || []).find((c) => c.year === y);
      if (row?.luknoPaid) luknoPaid++;
      else luknoUnpaid++;
    });
    const donationYear = families.reduce((s, f) => {
      const row = (f.contributions || []).find((c) => c.year === y);
      return s + (Number(row?.churchDonation) || 0);
    }, 0);
    return {
      intentionsMonth: intentionsMonth.length,
      paidPct: intentionsMonth.length ? Math.round((paidMonth / intentionsMonth.length) * 100) : 0,
      stipendSum,
      sacramentCounts,
      last6,
      luknoPaid,
      luknoUnpaid,
      donationYear,
      cashbookMonths: computeCashbookMonths(data),
      debtCategories: computeDebtCategories(data),
    };
  }

  function destroyChart(id) {
    const inst = chartRegistry.get(id);
    if (inst) {
      inst.destroy();
      chartRegistry.delete(id);
    }
  }

  function destroyAllCharts() {
    chartRegistry.forEach((c) => c.destroy());
    chartRegistry.clear();
  }

  function baseOptions(extra = {}) {
    const p = getPalette();
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: extra.legend !== false,
          labels: { boxWidth: 10, font: { size: 11 }, color: p.neutral },
        },
        tooltip: {
          backgroundColor: "rgba(44, 40, 36, 0.92)",
          titleFont: { size: 12 },
          bodyFont: { size: 11 },
          padding: 10,
        },
      },
      ...extra,
    };
  }

  function upsertChart(id, config) {
    if (!global.Chart) return null;
    const canvas = document.getElementById(id);
    if (!canvas) return null;
    destroyChart(id);
    const chart = new global.Chart(canvas, config);
    chartRegistry.set(id, chart);
    return chart;
  }

  function chartIntentionsBar(id, stats, compact) {
    const p = getPalette();
    return upsertChart(id, {
      type: "bar",
      data: {
        labels: stats.last6.map((x) => x.label),
        datasets: [
          {
            label: "Nakane",
            data: stats.last6.map((x) => x.count),
            backgroundColor: colorMix(p.liturgy, compact ? 0.9 : 0.75),
            borderRadius: 4,
            maxBarThickness: compact ? 14 : 28,
          },
        ],
      },
      options: baseOptions({
        legend: false,
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: compact ? 8 : 10 }, maxRotation: 0 } },
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: compact ? 8 : 10 }, display: !compact },
            grid: { color: "rgba(0,0,0,0.06)", display: !compact },
          },
        },
      }),
    });
  }

  function colorMix(hex, alpha) {
    return `color-mix(in srgb, ${hex} ${Math.round(alpha * 100)}%, transparent)`;
  }

  function chartSacramentsDoughnut(id, stats, compact) {
    const p = getPalette();
    const sc = stats.sacramentCounts;
    return upsertChart(id, {
      type: "doughnut",
      data: {
        labels: ["Krštenja", "Vjenčanja", "Pogrebi", "Krizmanici"],
        datasets: [
          {
            data: [sc.krštenja, sc.vjenčanja, sc.pogrebi, sc.krizmanici],
            backgroundColor: [p.primary, p.liturgy, p.neutral, p.accent],
            borderWidth: 0,
          },
        ],
      },
      options: baseOptions({
        cutout: compact ? "62%" : "58%",
        plugins: { legend: { display: !compact, position: "bottom" } },
      }),
    });
  }

  function chartLuknoBar(id, stats, compact) {
    const p = getPalette();
    return upsertChart(id, {
      type: "bar",
      data: {
        labels: ["Plaćeno", "Neplaćeno"],
        datasets: [
          {
            label: `Lukno ${new Date().getFullYear()}`,
            data: [stats.luknoPaid, stats.luknoUnpaid],
            backgroundColor: [p.success, p.alert],
            borderRadius: 6,
            maxBarThickness: 36,
          },
        ],
      },
      options: baseOptions({
        legend: false,
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: compact ? 9 : 11 } } },
          y: { beginAtZero: true, ticks: { stepSize: 1, display: !compact } },
        },
      }),
    });
  }

  function chartCashflowLine(id, stats, compact) {
    const p = getPalette();
    const m = stats.cashbookMonths;
    return upsertChart(id, {
      type: "line",
      data: {
        labels: m.map((x) => x.label),
        datasets: [
          {
            label: "Ulaz",
            data: m.map((x) => x.in),
            borderColor: p.success,
            backgroundColor: colorMix(p.success, 0.15),
            fill: true,
            tension: 0.35,
            pointRadius: 3,
          },
          {
            label: "Izlaz",
            data: m.map((x) => x.out),
            borderColor: p.alert,
            backgroundColor: colorMix(p.alert, 0.1),
            fill: true,
            tension: 0.35,
            pointRadius: 3,
          },
        ],
      },
      options: baseOptions({
        plugins: { legend: { display: !compact, position: "bottom" } },
        scales: {
          y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.06)", display: !compact }, ticks: { display: !compact } },
          x: { grid: { display: false }, ticks: { font: { size: compact ? 8 : 10 } } },
        },
      }),
    });
  }

  function chartDebtsCategory(id, stats, maxItems = 6, compact) {
    const p = getPalette();
    const cats = stats.debtCategories.slice(0, maxItems);
    if (!cats.length) return null;
    return upsertChart(id, {
      type: "bar",
      data: {
        labels: cats.map((c) => c.label),
        datasets: [
          {
            label: "Neplaćeno",
            data: cats.map((c) => c.count),
            backgroundColor: p.primary,
            borderRadius: 4,
          },
        ],
      },
      options: baseOptions({
        indexAxis: "y",
        legend: false,
        scales: {
          x: { beginAtZero: true, ticks: { stepSize: 1, font: { size: compact ? 8 : 10 } } },
          y: { grid: { display: false }, ticks: { font: { size: compact ? 8 : 10 } } },
        },
      }),
    });
  }

  function removeNavChartsStrip() {
    document.getElementById("ui-nav-charts-strip")?.remove();
  }

  function renderAnalyticsHtml(data) {
    const s = computeStats(data);
    const y = new Date().getFullYear();
    return `
      <section class="card analytics-section analytics-section--dashboard wide" data-no-stagger>
        <h2 class="section-title">Pregled župe</h2>
        <p class="card-sub">Grafički sažetak iz evidencije — samo na nadzornoj ploči.</p>
        <div class="analytics-grid analytics-grid--dashboard">
          <article class="card analytics-stat analytics-stat--wide card-section--liturgy">
            <p class="card-label">Misne nakane — zadnjih 6 mjeseci</p>
            <p class="card-sub">Ovaj mjesec: <strong>${s.intentionsMonth}</strong> nakana · ${s.paidPct}% plaćeno · ${s.stipendSum} € stipendija</p>
            <div class="chart-wrap chart-wrap--xl"><canvas id="chart-intentions"></canvas></div>
          </article>
          <article class="card analytics-stat analytics-stat--tall card-section--finance">
            <p class="card-label">Blagajna — ulaz i izlaz</p>
            <div class="chart-wrap chart-wrap--lg"><canvas id="chart-cashflow"></canvas></div>
          </article>
          <article class="card analytics-stat analytics-stat--tall card-section--sacrament">
            <p class="card-label">Sakramenti u evidenciji</p>
            <div class="chart-wrap chart-wrap--lg"><canvas id="chart-sacraments"></canvas></div>
          </article>
          <article class="card analytics-stat card-section--finance">
            <p class="card-label">Lukno ${y}</p>
            <p class="card-sub">Davanja: <strong>${s.donationYear} €</strong></p>
            <div class="chart-wrap chart-wrap--md"><canvas id="chart-lukno"></canvas></div>
          </article>
          <article class="card analytics-stat">
            <p class="card-label">Dugovanja po kategoriji</p>
            <div class="chart-wrap chart-wrap--md"><canvas id="chart-debts-cat"></canvas></div>
          </article>
        </div>
      </section>`;
  }

  function paintDashboardCharts(data) {
    if (!global.Chart) return;
    removeNavChartsStrip();
    const s = computeStats(data);
    chartIntentionsBar("chart-intentions", s);
    chartSacramentsDoughnut("chart-sacraments", s);
    chartLuknoBar("chart-lukno", s);
    chartCashflowLine("chart-cashflow", s);
    chartDebtsCategory("chart-debts-cat", s);
  }

  function paintCharts(data) {
    if (document.body.dataset.page === "dashboard") {
      paintDashboardCharts(data);
    }
  }

  function refreshAll() {
    const data = global.PastoralData?.load?.();
    if (!data || document.body.dataset.page !== "dashboard") return;
    paintDashboardCharts(data);
  }

  global.PastoralAnalytics = {
    computeStats,
    renderAnalyticsHtml,
    paintCharts,
    paintDashboardCharts,
    refreshAll,
    destroyAllCharts,
    removeNavChartsStrip,
  };
})(typeof window !== "undefined" ? window : global);
