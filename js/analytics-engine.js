/**
 * Dashboard analitika
 */
(function (global) {
  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  }

  function monthKey(d) {
    const x = d instanceof Date ? d : new Date(d);
    return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}`;
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
    const tasksOpen = data.tasks.filter((t) => !t.done).length;
    const tasksDone = data.tasks.filter((t) => t.done).length;
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
      tasksOpen,
      tasksDone,
      luknoPaid,
      luknoUnpaid,
      donationYear,
    };
  }

  function drawBarChart(canvas, items, color) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.parentElement?.clientWidth || 320;
    const h = 140;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const max = Math.max(...items.map((i) => i.count), 1);
    const pad = 24;
    const bw = (w - pad * 2) / items.length - 8;
    items.forEach((item, i) => {
      const bh = ((item.count / max) * (h - 50));
      const x = pad + i * (bw + 8);
      const y = h - 30 - bh;
      ctx.fillStyle = color || "#5c2e3a";
      ctx.fillRect(x, y, bw, bh);
      ctx.fillStyle = "#6d6760";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(item.label, x + bw / 2, h - 8);
      ctx.fillText(String(item.count), x + bw / 2, y - 4);
    });
  }

  function drawDonut(canvas, segments) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const size = 120;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = size + "px";
    canvas.style.height = size + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const total = segments.reduce((s, x) => s + x.value, 0) || 1;
    let start = -Math.PI / 2;
    const cx = size / 2;
    const cy = size / 2;
    const r = 40;
    segments.forEach((seg) => {
      const slice = (seg.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, r, start, start + slice);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();
      start += slice;
    });
    ctx.fillStyle = "#2c2824";
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(total), cx, cy + 5);
  }

  function renderAnalyticsHtml(data, parish) {
    const s = computeStats(data);
    const sc = s.sacramentCounts;
    return `
      <section class="card analytics-section wide">
        <h2 class="section-title">Analitika župe</h2>
        <div class="analytics-grid">
          <article class="card analytics-stat">
            <p class="card-label">Nakane ovaj mjesec</p>
            <p class="card-value">${s.intentionsMonth}</p>
            <p class="card-sub">${s.paidPct}% plaćeno · ${s.stipendSum} € stipendija</p>
            <canvas id="chart-intentions" class="chart-canvas" height="140"></canvas>
          </article>
          <article class="card analytics-stat">
            <p class="card-label">Evidencija sakramenata</p>
            <canvas id="chart-sacraments" width="120" height="120"></canvas>
            <ul class="analytics-legend">
              <li><span style="background:#5c2e3a"></span> Krštenja ${sc.krštenja}</li>
              <li><span style="background:#3d5a80"></span> Vjenčanja ${sc.vjenčanja}</li>
              <li><span style="background:#6d6760"></span> Pogrebi ${sc.pogrebi}</li>
              <li><span style="background:#b8922a"></span> Krizmanici ${sc.krizmanici}</li>
            </ul>
          </article>
          <article class="card analytics-stat">
            <p class="card-label">Župni ured</p>
            <p class="card-sub">Otvoreno: <strong>${s.tasksOpen}</strong> · Završeno: ${s.tasksDone}</p>
            <p class="card-sub">Lukno ${new Date().getFullYear()}: <strong>${s.luknoPaid}</strong> plaćeno · <strong>${s.luknoUnpaid}</strong> neplaćeno</p>
            <p class="card-sub">Davanja ove godine: <strong>${s.donationYear} €</strong></p>
            <p class="card-sub">Krizma ${data.confirmations[0]?.year || ""}: ${sc.krizmanici} kandidata</p>
          </article>
        </div>
      </section>`;
  }

  function paintCharts(data) {
    const s = computeStats(data);
    drawBarChart(document.getElementById("chart-intentions"), s.last6, "#5c2e3a");
    const sc = s.sacramentCounts;
    drawDonut(document.getElementById("chart-sacraments"), [
      { value: sc.krštenja, color: "#5c2e3a" },
      { value: sc.vjenčanja, color: "#3d5a80" },
      { value: sc.pogrebi, color: "#6d6760" },
      { value: sc.krizmanici, color: "#b8922a" },
    ]);
  }

  global.PastoralAnalytics = { computeStats, renderAnalyticsHtml, paintCharts };
})(typeof window !== "undefined" ? window : global);
