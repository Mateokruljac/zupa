/**
 * Župni list — export misnih nakana za tjedan
 */
(function (global) {
  function weekStartFrom(iso) {
    const d = new Date((iso || new Date().toISOString().slice(0, 10)) + "T12:00:00");
    const day = (d.getDay() + 6) % 7;
    d.setDate(d.getDate() - day);
    return d.toISOString().slice(0, 10);
  }

  function weekEndFrom(start) {
    const d = new Date(start + "T12:00:00");
    d.setDate(d.getDate() + 6);
    return d.toISOString().slice(0, 10);
  }

  function getWeekIntentions(data, startIso) {
    const start = weekStartFrom(startIso);
    const end = weekEndFrom(start);
    return (data.intentions || [])
      .filter((n) => n.date >= start && n.date <= end)
      .sort((a, b) => (a.date + a.massTime).localeCompare(b.date + b.massTime));
  }

  function buildBulletinHtml(data, parish, startIso) {
    const start = weekStartFrom(startIso);
    const end = weekEndFrom(start);
    const rows = getWeekIntentions(data, start);
    const fmt = (iso) =>
      new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", { weekday: "short", day: "numeric", month: "short" });
    const tablica = rows.length
      ? rows
          .map(
            (n) =>
              `<tr><td>${fmt(n.date)}</td><td>${n.massTime}</td><td>${escape(n.intentionFor)}</td><td>${escape(n.requestedBy || "—")}</td><td>${n.paid ? "✓" : "—"}</td></tr>`
          )
          .join("")
      : "<tr><td colspan=\"5\">Nema nakan u tom tjednu</td></tr>";

    function escape(s) {
      return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    }

    return global.PastoralDocuments?.mergeTemplate(
      global.PastoralDocuments.getTemplate("raspored_nakana").body,
      {
        zupa: parish.name,
        tjedan_od: new Date(start + "T12:00:00").toLocaleDateString("hr-HR"),
        tablica_nakana: tablica,
      }
    );
  }

  function printWeekBulletin(data, parish, startIso) {
    const html = buildBulletinHtml(data, parish, startIso);
    global.PastoralDocuments?.printHtml(html, "Raspored misnih nakana");
  }

  function mountBulletinToolbar(mount, api) {
    if (!mount) return;
    const start = weekStartFrom();
    mount.innerHTML = `
      <button type="button" class="btn btn-secondary btn-sm" id="bulletin-week-btn" title="Ispis nakana za ovaj tjedan">
        🖨 Župni list (nakane)
      </button>`;
    mount.querySelector("#bulletin-week-btn")?.addEventListener("click", () => {
      const data = api.getData();
      const parish = api.getSettings();
      printWeekBulletin(data, parish, start);
      api.showToast?.("Otvoren ispis za tjedan");
    });
  }

  global.PastoralBulletin = { weekStartFrom, getWeekIntentions, buildBulletinHtml, printWeekBulletin, mountBulletinToolbar };
})(typeof window !== "undefined" ? window : global);
