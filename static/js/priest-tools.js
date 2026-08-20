/**
 * Ispis dnevnog pregleda župnog ureda.
 */
(function (global) {
  let api = null;

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }

  function getMassesForToday(dataOrSchedule) {
    const schedule = Array.isArray(dataOrSchedule) ? dataOrSchedule : dataOrSchedule?.massSchedule || [];
    const dow = new Date().getDay();
    const label = dow === 0 ? "Nedjelja" : dow === 6 ? "Subota" : "Pon–Pet";
    return schedule.filter((m) => m.day === label).map((m) => ({ time: m.time, celebrant: m.celebrant || "" }));
  }

  function printTodaySheet(data) {
    const today = todayIso();
    const settings = api.getSettings?.() || {};
    const masses = getMassesForToday(data);
    const intentions = (data.intentions || []).filter((n) => n.date === today);
    const tasks = (data.tasks || []).filter((t) => !t.done && (t.due === today || (t.due && t.due < today)));
    const dateLabel = new Date(today + "T12:00:00").toLocaleDateString("hr-HR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });

    const html = `<!DOCTYPE html><html lang="hr"><head><meta charset="UTF-8"><title>Župa — ${dateLabel}</title>
      <style>
        body{font-family:Georgia,serif;padding:24px;color:#222;max-width:720px;margin:0 auto}
        h1{font-size:1.4rem;margin:0 0 4px} h2{font-size:1rem;margin:24px 0 8px;border-bottom:1px solid #ccc}
        table{width:100%;border-collapse:collapse;font-size:0.9rem}
        th,td{border:1px solid #ddd;padding:8px;text-align:left}
        th{background:#f5f0e8}
        .meta{color:#555;font-size:0.85rem;margin-bottom:20px}
        @media print{body{padding:12px}}
      </style></head><body>
      <h1>${esc(settings.name || "Župa")}</h1>
      <p class="meta">${esc(dateLabel)} · ${esc(settings.pastor || "")}</p>
      <h2>Mise danas</h2>
      ${masses.length ? `<ul>${masses.map((m) => `<li><strong>${esc(m.time)}</strong></li>`).join("")}</ul>` : "<p>—</p>"}
      <h2>Misne nakane (${intentions.length})</h2>
      ${intentions.length
        ? `<table><thead><tr><th>Misa</th><th>Za koga</th><th>Naručitelj</th><th>Stipendij</th><th>Plaćeno</th></tr></thead><tbody>
        ${intentions
          .sort((a, b) => a.massTime.localeCompare(b.massTime))
          .map(
            (n) =>
              `<tr><td>${esc(n.massTime)}</td><td>${esc(n.intentionFor)}</td><td>${esc(n.requestedBy || "—")}</td><td>${n.stipend} €</td><td>${n.paid ? "da" : "ne"}</td></tr>`
          )
          .join("")}</tbody></table>`
        : "<p>Nema nakana za danas.</p>"}
      <h2>Zadaci (danas / zakašnjeli)</h2>
      ${tasks.length
        ? `<ul>${tasks.map((t) => `<li>${esc(t.title)} — rok ${esc(t.due || "—")} <em>(${esc(t.priority)})</em></li>`).join("")}</ul>`
        : "<p>Nema hitnih zadataka.</p>"}
      <p class="meta" style="margin-top:32px">Ispis iz Pastoral · ${new Date().toLocaleString("hr-HR")}</p>
      <script>window.onload=function(){window.print();}</script>
      </body></html>`;

    const w = window.open("", "_blank");
    if (!w) {
      api.showToast("Omogućite skočne prozore za ispis");
      return;
    }
    w.document.write(html);
    w.document.close();
  }


  global.PastoralPriestTools = {
    init(hooks) {
      api = hooks;
    },
    async printTodaySheet() {
      try {
        const parishData = await api.loadData();
        printTodaySheet(parishData);
      } catch {
        api.showToast("Dnevni pregled trenutno nije moguće učitati.");
      }
    },
  };
})(typeof window !== "undefined" ? window : global);
