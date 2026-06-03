/**
 * Raspored misa — tjedni plan, danas, iznimke, CRUD, veza na nakane
 */
(function (global) {
  const MODES = ["today", "week", "manage"];
  const MODE_KEY = "mise-view-mode";
  const WEEK_HEADERS = [
    { dow: 1, label: "Pon" },
    { dow: 2, label: "Uto" },
    { dow: 3, label: "Sri" },
    { dow: 4, label: "Čet" },
    { dow: 5, label: "Pet" },
    { dow: 6, label: "Sub" },
    { dow: 0, label: "Ned" },
  ];
  const DOW_LABEL = { 0: "Nedjelja", 1: "Ponedjeljak", 2: "Utorak", 3: "Srijeda", 4: "Četvrtak", 5: "Petak", 6: "Subota" };
  const DAY_PRESETS = [
    { label: "Pon–Pet", weekdays: [1, 2, 3, 4, 5] },
    { label: "Nedjelja", weekdays: [0] },
    { label: "Subota", weekdays: [6] },
  ];

  let api = null;

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }

  function uid(prefix) {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
  }

  function getMode() {
    try {
      const m = sessionStorage.getItem(MODE_KEY);
      if (MODES.includes(m)) return m;
    } catch {
      /* ignore */
    }
    return "today";
  }

  function setMode(mode) {
    if (!MODES.includes(mode)) return;
    try {
      sessionStorage.setItem(MODE_KEY, mode);
    } catch {
      /* ignore */
    }
  }

  function weekdaysFromEntry(entry) {
    if (Array.isArray(entry.weekdays) && entry.weekdays.length) return entry.weekdays.slice();
    const day = entry.day || "";
    if (day === "Nedjelja") return [0];
    if (day === "Subota") return [6];
    if (day === "Pon–Pet" || day === "Pon-Pet") return [1, 2, 3, 4, 5];
    if (day.startsWith("Pon")) return [1];
    if (day.startsWith("Uto")) return [2];
    if (day.startsWith("Sri")) return [3];
    if (day.startsWith("Čet") || day.startsWith("Cet")) return [4];
    if (day.startsWith("Pet")) return [5];
    return [];
  }

  function dayLabelFromWeekdays(weekdays) {
    const w = [...new Set(weekdays)].sort((a, b) => a - b);
    if (w.length === 5 && w.join() === "1,2,3,4,5") return "Pon–Pet";
    if (w.length === 1 && w[0] === 0) return "Nedjelja";
    if (w.length === 1 && w[0] === 6) return "Subota";
    return w.map((d) => DOW_LABEL[d]?.slice(0, 3) || "?").join(", ");
  }

  function normalizeScheduleEntry(entry) {
    const weekdays = weekdaysFromEntry(entry);
    return {
      ...entry,
      weekdays,
      day: entry.day || dayLabelFromWeekdays(weekdays),
      celebrant: entry.celebrant || "",
      location: entry.location || "",
      notes: entry.notes || "",
    };
  }

  function getMassesForDate(data, iso) {
    const exc = (data.massExceptions || []).find((e) => e.date === iso);
    const dow = new Date(iso + "T12:00:00").getDay();
    let slots = [];

    if (!exc?.cancelAll) {
      (data.massSchedule || []).forEach((raw) => {
        const entry = normalizeScheduleEntry(raw);
        if (!weekdaysFromEntry(entry).includes(dow)) return;
        if ((exc?.cancelTimes || []).includes(entry.time)) return;
        slots.push({
          time: entry.time,
          celebrant: entry.celebrant,
          location: entry.location,
          notes: entry.notes,
          scheduleId: entry.id,
          kind: "regular",
        });
      });
    }

    (exc?.addSlots || []).forEach((add) => {
      slots.push({
        time: add.time,
        celebrant: add.celebrant || "",
        location: add.location || "",
        notes: add.note || exc?.note || "",
        kind: "exception",
      });
    });

    slots.sort((a, b) => String(a.time).localeCompare(String(b.time)));
    return slots;
  }

  function getAllScheduleTimes(data) {
    const times = new Set();
    (data.massSchedule || []).forEach((m) => {
      if (m.time) times.add(m.time);
    });
    ["07:30", "09:00", "11:00", "18:00"].forEach((t) => times.add(t));
    return [...times].sort();
  }

  function getMassTimesForDate(data, iso) {
    if (iso) return getMassesForDate(data, iso).map((s) => s.time);
    return getAllScheduleTimes(data);
  }

  function getNakaneForSlot(data, iso, massTime) {
    return (data.intentions || []).filter((n) => n.date === iso && n.massTime === massTime);
  }

  function getNextMassHint(data, iso) {
    if (iso !== todayIso()) return "";
    const slots = getMassesForDate(data, iso);
    if (!slots.length) return "Danas nema upisanih misa.";
    const nowMins = new Date().getHours() * 60 + new Date().getMinutes();
    const toMins = (t) => {
      const [h, m] = String(t || "0:0").split(":").map(Number);
      return h * 60 + m;
    };
    const upcoming = slots.filter((s) => toMins(s.time) >= nowMins - 30).sort((a, b) => toMins(a.time) - toMins(b.time))[0];
    if (!upcoming) return "Sve mise za danas su prošle.";
    const nakane = getNakaneForSlot(data, iso, upcoming.time);
    return `Sljedeća misa: ${upcoming.time} — ${nakane.length} nakana`;
  }

  function logChange(data, summary) {
    if (!Array.isArray(data.massScheduleLog)) data.massScheduleLog = [];
    data.massScheduleLog.unshift({
      id: uid("mslog"),
      at: new Date().toISOString(),
      summary,
    });
    data.massScheduleLog = data.massScheduleLog.slice(0, 50);
  }

  function formatMassScheduleText(data) {
    const lines = (data.massSchedule || []).map((raw) => {
      const e = normalizeScheduleEntry(raw);
      const extra = [e.celebrant, e.location, e.notes].filter(Boolean).join(" · ");
      return `${e.day} — ${e.time}${extra ? ` (${extra})` : ""}`;
    });
    const excLines = (data.massExceptions || [])
      .filter((e) => e.date >= todayIso())
      .slice(0, 8)
      .map((e) => {
        if (e.cancelAll) return `${api.fmtDate(e.date)}: nema redovitih misa${e.note ? ` — ${e.note}` : ""}`;
        const parts = [];
        if (e.cancelTimes?.length) parts.push(`otkaz: ${e.cancelTimes.join(", ")}`);
        if (e.addSlots?.length) parts.push(`dodatno: ${e.addSlots.map((a) => a.time).join(", ")}`);
        return `${api.fmtDate(e.date)}: ${parts.join("; ")}${e.note ? ` — ${e.note}` : ""}`;
      });
    return [...lines, ...(excLines.length ? ["", "Iznimke:", ...excLines] : [])].join("\n");
  }

  function formatMassScheduleHtml(data) {
    const rows = data.massSchedule || [];
    if (!rows.length) return "<p>Raspored misa nije unesen.</p>";
    return `<ul class="listic-ul">${rows
      .map((raw) => {
        const e = normalizeScheduleEntry(raw);
        const extra = [e.celebrant, e.notes].filter(Boolean).join(" · ");
        return `<li><strong>${esc(e.day)}</strong> — ${esc(e.time)}${extra ? ` <span class="card-sub">(${esc(extra)})</span>` : ""}</li>`;
      })
      .join("")}</ul>`;
  }

  function buildWeeklyGrid(data) {
    const timeSet = new Set();
    (data.massSchedule || []).forEach((e) => {
      if (e.time) timeSet.add(e.time);
    });
    const times = [...timeSet].sort();
    const grid = {};
    times.forEach((t) => {
      grid[t] = {};
      WEEK_HEADERS.forEach(({ dow }) => {
        grid[t][dow] = null;
      });
    });
    (data.massSchedule || []).forEach((raw) => {
      const entry = normalizeScheduleEntry(raw);
      weekdaysFromEntry(entry).forEach((dow) => {
        if (!grid[entry.time]) grid[entry.time] = {};
        grid[entry.time][dow] = entry;
      });
    });
    return { times: Object.keys(grid).sort(), grid };
  }

  function countIntentionsOnSlot(data, scheduleEntry) {
    const wds = weekdaysFromEntry(scheduleEntry);
    let count = 0;
    (data.intentions || []).forEach((n) => {
      if (n.massTime !== scheduleEntry.time) return;
      const dow = new Date(n.date + "T12:00:00").getDay();
      if (wds.includes(dow)) count += 1;
    });
    return count;
  }

  function migrate(data) {
    if (!Array.isArray(data.massSchedule)) data.massSchedule = [];
    data.massSchedule = data.massSchedule.map((e) => normalizeScheduleEntry(e));
    if (!Array.isArray(data.massExceptions)) data.massExceptions = [];
    if (!Array.isArray(data.massScheduleLog)) data.massScheduleLog = [];
    return data;
  }

  function M() {
    return global.PastoralModal;
  }

  function openForm(opts) {
    return M()?.openForm?.(opts);
  }

  function scheduleFormBody(entry) {
    const wds = entry ? weekdaysFromEntry(entry) : [0];
    const checks = WEEK_HEADERS.concat([{ dow: 0, label: "Ned" }])
      .filter((v, i, a) => a.findIndex((x) => x.dow === v.dow) === i)
      .sort((a, b) => {
        const order = [1, 2, 3, 4, 5, 6, 0];
        return order.indexOf(a.dow) - order.indexOf(b.dow);
      });
    const uniqueChecks = [
      { dow: 1, label: "Pon" },
      { dow: 2, label: "Uto" },
      { dow: 3, label: "Sri" },
      { dow: 4, label: "Čet" },
      { dow: 5, label: "Pet" },
      { dow: 6, label: "Sub" },
      { dow: 0, label: "Ned" },
    ];
    return `
      <div class="form-group"><label>Sat misa *</label><input name="time" type="time" value="${entry?.time || "09:00"}" required /></div>
      <div class="form-group form-wide"><label>Dani</label>
        <div class="mise-weekday-checks">${uniqueChecks
          .map(
            (c) =>
              `<label class="mise-weekday-check"><input type="checkbox" name="wd" value="${c.dow}" ${wds.includes(c.dow) ? "checked" : ""} /> ${c.label}</label>`
          )
          .join("")}</div>
        <p class="card-sub">Brzo: ${DAY_PRESETS.map(
          (p, i) => `<button type="button" class="btn btn-ghost btn-sm" data-preset-wd="${i}">${p.label}</button>`
        ).join(" ")}</p>
      </div>
      <div class="form-group"><label>Svećenik / služitelj</label><input name="celebrant" value="${esc(entry?.celebrant || "")}" placeholder="vlč. …" /></div>
      <div class="form-group"><label>Mjesto</label><input name="location" value="${esc(entry?.location || "")}" placeholder="Crkva, kapela…" /></div>
      <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${esc(entry?.notes || "")}" placeholder="npr. samo ljeti" /></div>`;
  }

  function readScheduleForm(form) {
    const fd = new FormData(form);
    const time = fd.get("time");
    if (!time) {
      api.showToast("Unesite sat misa");
      return null;
    }
    const weekdays = [...form.querySelectorAll('[name="wd"]:checked')].map((el) => Number(el.value));
    if (!weekdays.length) {
      api.showToast("Odaberite barem jedan dan");
      return null;
    }
    return {
      time: String(time).slice(0, 5),
      weekdays,
      day: dayLabelFromWeekdays(weekdays),
      celebrant: fd.get("celebrant")?.trim() || "",
      location: fd.get("location")?.trim() || "",
      notes: fd.get("notes")?.trim() || "",
    };
  }

  function bindPresetButtons(form) {
    form.querySelectorAll("[data-preset-wd]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const preset = DAY_PRESETS[Number(btn.dataset.presetWd)];
        if (!preset) return;
        form.querySelectorAll('[name="wd"]').forEach((cb) => {
          cb.checked = preset.weekdays.includes(Number(cb.value));
        });
      });
    });
  }

  function openScheduleForm(entry, onDone) {
    openForm({
      title: entry ? "Uredi termin misa" : "Novi termin misa",
      size: "lg",
      body: scheduleFormBody(entry),
      submitLabel: "Spremi",
      onOpen: (_overlay, form) => bindPresetButtons(form),
      onSubmit: async (form) => {
        const fields = readScheduleForm(form);
        if (!fields) return false;
        const data = api.getData();
        if (entry) {
          const row = data.massSchedule.find((x) => x.id === entry.id);
          if (row) Object.assign(row, fields);
          logChange(data, `Uređen termin ${fields.time} (${fields.day})`);
        } else {
          data.massSchedule.push({ id: uid("ms"), ...fields });
          logChange(data, `Dodan termin ${fields.time} (${fields.day})`);
        }
        api.saveData(data);
        api.showToast("Raspored spremljen");
        onDone?.();
      },
    });
  }

  function exceptionFormBody(entry) {
    const data = api.getData();
    const times = getAllScheduleTimes(data);
    return `
      <div class="form-group"><label>Datum *</label><input name="date" type="date" value="${entry?.date || ""}" required /></div>
      <div class="form-group form-wide"><label>Vrsta iznimke</label>
        <select name="excType">
          <option value="add" ${entry?.addSlots?.length && !entry?.cancelAll ? "selected" : ""}>Dodatna / zamjenska misa</option>
          <option value="cancel_times" ${entry?.cancelTimes?.length ? "selected" : ""}>Otkaz određenih termina</option>
          <option value="cancel_all" ${entry?.cancelAll ? "selected" : ""}>Nema redovitih misa toga dana</option>
        </select>
      </div>
      <div class="form-group form-wide" data-exc-cancel-times>
        <label>Otkazani termini (redoviti raspored)</label>
        <div class="mise-weekday-checks">${times
          .map(
            (t) =>
              `<label class="mise-weekday-check"><input type="checkbox" name="cancelTime" value="${esc(t)}" ${entry?.cancelTimes?.includes(t) ? "checked" : ""} /> ${esc(t)}</label>`
          )
          .join("")}</div>
      </div>
      <div class="form-group" data-exc-add-time><label>Sat dodatne mise</label><input name="addTime" type="time" value="${entry?.addSlots?.[0]?.time || "10:00"}" /></div>
      <div class="form-group" data-exc-add-celebrant><label>Svećenik (iznimka)</label><input name="addCelebrant" value="${esc(entry?.addSlots?.[0]?.celebrant || "")}" /></div>
      <div class="form-group form-wide"><label>Napomena</label><input name="note" value="${esc(entry?.note || "")}" placeholder="Božić, blagdan…" /></div>`;
  }

  function readExceptionForm(form) {
    const fd = new FormData(form);
    const date = fd.get("date");
    if (!date) {
      api.showToast("Unesite datum");
      return null;
    }
    const type = fd.get("excType");
    const note = fd.get("note")?.trim() || "";
    if (type === "cancel_all") {
      return { date, cancelAll: true, cancelTimes: [], addSlots: [], note };
    }
    if (type === "cancel_times") {
      const cancelTimes = [...form.querySelectorAll('[name="cancelTime"]:checked')].map((el) => el.value);
      if (!cancelTimes.length) {
        api.showToast("Odaberite termin(e) za otkaz");
        return null;
      }
      return { date, cancelAll: false, cancelTimes, addSlots: [], note };
    }
    const addTime = String(fd.get("addTime") || "").slice(0, 5);
    if (!addTime) {
      api.showToast("Unesite sat dodatne mise");
      return null;
    }
    return {
      date,
      cancelAll: false,
      cancelTimes: [],
      addSlots: [{ time: addTime, celebrant: fd.get("addCelebrant")?.trim() || "", note }],
      note,
    };
  }

  function openExceptionForm(entry, onDone) {
    openForm({
      title: entry ? "Uredi iznimku" : "Nova iznimka rasporeda",
      size: "lg",
      body: exceptionFormBody(entry),
      submitLabel: "Spremi",
      onSubmit: async (form) => {
        const fields = readExceptionForm(form);
        if (!fields) return false;
        const data = api.getData();
        if (entry) {
          const row = data.massExceptions.find((x) => x.id === entry.id);
          if (row) Object.assign(row, { ...fields, id: row.id });
          logChange(data, `Uređena iznimka ${api.fmtDate(fields.date)}`);
        } else {
          data.massExceptions.push({ id: uid("mexc"), ...fields });
          logChange(data, `Dodana iznimka ${api.fmtDate(fields.date)}`);
        }
        api.saveData(data);
        api.showToast("Iznimka spremljena");
        onDone?.();
      },
    });
  }

  async function deleteScheduleEntry(id, onDone) {
    const ok = await api.confirm("Obrisati ovaj termin iz stalnog rasporeda?", { danger: true, title: "Brisanje" });
    if (!ok) return;
    const data = api.getData();
    const row = data.massSchedule.find((x) => x.id === id);
    data.massSchedule = data.massSchedule.filter((x) => x.id !== id);
    logChange(data, `Obrisan termin ${row?.time || ""} (${row?.day || ""})`);
    api.saveData(data);
    api.showToast("Termin obrisan");
    onDone?.();
  }

  async function deleteException(id, onDone) {
    const ok = await api.confirm("Obrisati ovu iznimku?", { danger: true, title: "Brisanje" });
    if (!ok) return;
    const data = api.getData();
    const row = data.massExceptions.find((x) => x.id === id);
    data.massExceptions = data.massExceptions.filter((x) => x.id !== id);
    logChange(data, `Obrisana iznimka ${row ? api.fmtDate(row.date) : ""}`);
    api.saveData(data);
    api.showToast("Iznimka obrisana");
    onDone?.();
  }

  function renderTodaySlot(data, iso, slot) {
    const nakane = getNakaneForSlot(data, iso, slot.time);
    const unpaid = nakane.filter((n) => !n.paid).length;
    const preview = nakane.slice(0, 2);
    const nakaneUrl = `${api.pageUrl("pages/nakane.html")}?date=${iso}&mode=calendar`;
    return `<article class="mise-slot-card card ${slot.kind === "exception" ? "mise-slot-card--exception" : ""}">
      <div class="mise-slot-head">
        <div>
          <h3 class="mise-slot-time">${esc(slot.time)}</h3>
          ${slot.celebrant ? `<p class="card-sub">${esc(slot.celebrant)}</p>` : ""}
          ${slot.location ? `<p class="card-sub">📍 ${esc(slot.location)}</p>` : ""}
          ${slot.notes ? `<p class="card-sub">${esc(slot.notes)}</p>` : ""}
          ${slot.kind === "exception" ? '<span class="badge">iznimka</span>' : ""}
        </div>
        <div class="mise-slot-stats">
          <strong>${nakane.length}</strong> nakana
          ${unpaid ? `<span class="badge badge-urgent">${unpaid} neplaćeno</span>` : ""}
        </div>
      </div>
      ${nakane.length
        ? `<ul class="mise-slot-nakane">${preview
            .map((n) => `<li>${esc(n.intentionFor)}${n.paid ? "" : " · neplaćeno"}</li>`)
            .join("")}${nakane.length > 2 ? `<li class="card-sub">+ ${nakane.length - 2} više</li>` : ""}</ul>`
        : '<p class="empty-state">Nema nakana za ovu misu.</p>'}
      <div class="mise-slot-actions">
        <a href="${nakaneUrl}" class="btn btn-ghost btn-sm">Nakane</a>
        <button type="button" class="btn btn-secondary btn-sm" data-print-slot="${esc(slot.time)}">🖨 Ispis</button>
        <button type="button" class="btn btn-primary btn-sm" data-add-nakana="${esc(slot.time)}">+ Nakana</button>
      </div>
    </article>`;
  }

  function renderTodayPanel(data) {
    const iso = todayIso();
    const slots = getMassesForDate(data, iso);
    const litSlot = `<div id="mise-lit-detail">${global.PastoralLiturgical?.renderNakaneLitLoading?.(iso) || ""}</div>`;
    return `<section class="mise-panel">
      ${litSlot}
      ${slots.length
        ? `<div class="mise-slots-grid">${slots.map((s) => renderTodaySlot(data, iso, s)).join("")}</div>`
        : '<p class="empty-state">Danas nema misa prema rasporedu. Provjerite iznimke ili dodajte termin.</p>'}
    </section>`;
  }

  function renderWeekPanel(data) {
    const { times, grid } = buildWeeklyGrid(data);
    const todayDow = new Date().getDay();
    if (!times.length) return '<p class="empty-state">Nema unesenog rasporeda.</p>';
    return `<section class="card mise-week-card">
      <p class="card-sub">Stalni tjedni raspored — iznimke po datumu uređujte u Upravljanju.</p>
      <div class="table-wrap">
        <table class="data-table mise-week-table">
          <thead><tr><th>Misa</th>${WEEK_HEADERS.map((h) => `<th class="${h.dow === todayDow ? "mise-week-today-col" : ""}">${h.label}</th>`).join("")}</tr></thead>
          <tbody>${times
            .map((time) => {
              return `<tr><th scope="row">${esc(time)}</th>${WEEK_HEADERS.map(({ dow }) => {
                const entry = grid[time]?.[dow];
                if (!entry) return `<td class="mise-week-empty">—</td>`;
                const isToday = dow === todayDow;
                return `<td class="mise-week-cell${isToday ? " mise-week-today-col" : ""}">
                  <span class="mise-week-dot" title="${esc(entry.notes || entry.celebrant || "Misa")}">●</span>
                  ${entry.celebrant ? `<small>${esc(entry.celebrant.split(" ")[0])}</small>` : ""}
                </td>`;
              }).join("")}</tr>`;
            })
            .join("")}</tbody>
        </table>
      </div>
    </section>`;
  }

  function renderManagePanel(data) {
    const scheduleRows = (data.massSchedule || [])
      .slice()
      .sort((a, b) => String(a.time).localeCompare(String(b.time)) || String(a.day).localeCompare(String(b.day)));
    const exceptions = (data.massExceptions || [])
      .slice()
      .sort((a, b) => String(a.date).localeCompare(String(b.date)));
    const log = (data.massScheduleLog || []).slice(0, 15);

    return `<div class="mise-manage-grid">
      <section class="card">
        <div class="mise-manage-head">
          <h2 class="section-title">Stalni raspored</h2>
          <button type="button" class="btn btn-primary btn-sm" id="mise-add-schedule">+ Termin</button>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Dan</th><th>Misa</th><th>Svećenik</th><th>Napomena</th><th></th></tr></thead>
            <tbody>${scheduleRows.length
              ? scheduleRows
                  .map((e) => {
                    const n = normalizeScheduleEntry(e);
                    return `<tr>
                      <td>${esc(n.day)}</td><td><strong>${esc(n.time)}</strong></td>
                      <td>${esc(n.celebrant || "—")}</td><td>${esc(n.notes || n.location || "—")}</td>
                      <td class="mise-table-actions">
                        <button type="button" class="btn btn-ghost btn-sm" data-edit-schedule="${esc(n.id)}">✎</button>
                        <button type="button" class="btn btn-ghost btn-sm" data-del-schedule="${esc(n.id)}">×</button>
                      </td>
                    </tr>`;
                  })
                  .join("")
              : `<tr><td colspan="5" class="empty-state">Nema termina — dodajte prvi.</td></tr>`}</tbody>
          </table>
        </div>
      </section>
      <section class="card">
        <div class="mise-manage-head">
          <h2 class="section-title">Iznimke po datumu</h2>
          <button type="button" class="btn btn-secondary btn-sm" id="mise-add-exception">+ Iznimka</button>
        </div>
        ${exceptions.length
          ? `<div class="mise-exception-list">${exceptions
              .map((e) => {
                let desc = "";
                if (e.cancelAll) desc = "Nema redovitih misa";
                else {
                  const p = [];
                  if (e.cancelTimes?.length) p.push(`Otkaz: ${e.cancelTimes.join(", ")}`);
                  if (e.addSlots?.length) p.push(`Dodatno: ${e.addSlots.map((a) => a.time).join(", ")}`);
                  desc = p.join(" · ") || "Iznimka";
                }
                return `<div class="list-item">
                  <div><strong>${esc(api.fmtDate(e.date))}</strong><br><small>${esc(desc)}</small>${e.note ? `<br><small class="card-sub">${esc(e.note)}</small>` : ""}</div>
                  <div class="mise-table-actions">
                    <button type="button" class="btn btn-ghost btn-sm" data-edit-exception="${esc(e.id)}">✎</button>
                    <button type="button" class="btn btn-ghost btn-sm" data-del-exception="${esc(e.id)}">×</button>
                  </div>
                </div>`;
              })
              .join("")}</div>`
          : '<p class="empty-state">Nema iznimki — blagdani, jednokratne promjene.</p>'}
      </section>
      <section class="card">
        <div class="mise-manage-head">
          <h2 class="section-title">Za objavu / listić</h2>
          <button type="button" class="btn btn-ghost btn-sm" id="mise-copy-schedule">Kopiraj tekst</button>
          <a href="${api.pageUrl("pages/zupni-listic.html")}" class="btn btn-secondary btn-sm">Župni listić</a>
        </div>
        <div class="mise-copy-preview card-sub">${formatMassScheduleHtml(data)}</div>
      </section>
      <section class="card">
        <h2 class="section-title">Povijest promjena</h2>
        ${log.length
          ? `<ul class="mise-log-list">${log
              .map(
                (l) =>
                  `<li><small>${new Date(l.at).toLocaleString("hr-HR")}</small> — ${esc(l.summary)}</li>`
              )
              .join("")}</ul>`
          : '<p class="empty-state">Još nema zabilježenih promjena.</p>'}
      </section>
    </div>`;
  }

  function renderCommandBar(data) {
    const mode = getMode();
    const iso = todayIso();
    const slots = getMassesForDate(data, iso);
    const hint = mode === "today" ? getNextMassHint(data, iso) : "";
    const meta =
      mode === "today"
        ? `<strong>${esc(api.fmtDate(iso))}</strong>
           <span class="card-sub">${slots.length} misa danas</span>
           ${hint ? `<span class="mise-next-mass">${esc(hint)}</span>` : ""}`
        : mode === "week"
          ? `<strong>Tjedni raspored</strong><span class="card-sub">${(data.massSchedule || []).length} termina</span>`
          : `<strong>Upravljanje</strong><span class="card-sub">${(data.massExceptions || []).length} iznimki</span>`;

    return `<section class="card mise-command-bar">
      <div class="mise-command-inner">
        <div class="mise-mode-tabs" role="tablist">
          ${[
            ["today", "Danas"],
            ["week", "Tjedni raspored"],
            ["manage", "Upravljanje"],
          ]
            .map(
              ([id, label]) =>
                `<button type="button" class="mise-mode-tab${mode === id ? " is-active" : ""}" data-mise-mode="${id}">${label}</button>`
            )
            .join("")}
        </div>
        <div class="mise-command-meta">${meta}</div>
        <div class="mise-command-actions">
          <a href="${api.pageUrl("pages/nakane.html")}?date=today" class="btn btn-secondary btn-sm">☩ Nakane</a>
          ${mode === "today" && slots.length ? `<button type="button" class="btn btn-secondary btn-sm" id="mise-print-day">🖨 Ispis dana</button>` : ""}
        </div>
      </div>
    </section>`;
  }

  async function loadLiturgy(iso) {
    const L = global.PastoralLiturgical;
    const slot = document.getElementById("mise-lit-detail");
    if (!L || !slot) return;
    try {
      const day = await L.getDay(iso);
      slot.outerHTML = L.renderNakaneDayLiturgy(day);
    } catch {
      slot.outerHTML = L.renderNakaneDayLiturgy({ source: "offline", date: iso, title: null, hilpUrl: L.hilpUrlForDate(iso) });
    }
  }

  function bindPanel(root, render) {
    root.querySelectorAll("[data-mise-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        setMode(btn.dataset.miseMode);
        render();
        requestAnimationFrame(() => {
          document.getElementById("mise-panel-root")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });
    });

    root.querySelector("#mise-print-day")?.addEventListener("click", () => {
      api.printNakaneDay?.(todayIso());
    });

    root.querySelectorAll("[data-print-slot]").forEach((btn) => {
      btn.addEventListener("click", () => {
        api.printNakaneDay?.(todayIso(), btn.dataset.printSlot);
      });
    });

    root.querySelectorAll("[data-add-nakana]").forEach((btn) => {
      btn.addEventListener("click", () => {
        api.openNakanaForDate?.(todayIso(), btn.dataset.addNakana, render);
      });
    });

    root.querySelector("#mise-add-schedule")?.addEventListener("click", () => openScheduleForm(null, render));
    root.querySelector("#mise-add-exception")?.addEventListener("click", () => openExceptionForm(null, render));
    root.querySelectorAll("[data-edit-schedule]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const row = api.getData().massSchedule.find((x) => x.id === btn.dataset.editSchedule);
        if (row) openScheduleForm(row, render);
      });
    });
    root.querySelectorAll("[data-del-schedule]").forEach((btn) => {
      btn.addEventListener("click", () => deleteScheduleEntry(btn.dataset.delSchedule, render));
    });
    root.querySelectorAll("[data-edit-exception]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const row = api.getData().massExceptions.find((x) => x.id === btn.dataset.editException);
        if (row) openExceptionForm(row, render);
      });
    });
    root.querySelectorAll("[data-del-exception]").forEach((btn) => {
      btn.addEventListener("click", () => deleteException(btn.dataset.delException, render));
    });
    root.querySelector("#mise-copy-schedule")?.addEventListener("click", async () => {
      const text = formatMassScheduleText(api.getData());
      try {
        await navigator.clipboard.writeText(text);
        api.showToast("Raspored kopiran u međuspremnik");
      } catch {
        api.showToast("Kopiranje nije uspjelo");
      }
    });
  }

  function mountMisePage(mount, hooks) {
    api = hooks;
    migrate(api.getData());

    function render() {
      if (!mount) return;
      const data = api.getData();
      const mode = getMode();
      mount.className = `content mise-layout mise-mode-${mode}`;
      mount.innerHTML = `${renderCommandBar(data)}
        <div id="mise-panel-root">${
          mode === "today" ? renderTodayPanel(data) : mode === "week" ? renderWeekPanel(data) : renderManagePanel(data)
        }</div>`;
      bindPanel(mount, render);
      if (mode === "today") loadLiturgy(todayIso());
    }

    const params = new URLSearchParams(location.search);
    if (params.get("mode") === "manage" || params.get("mode") === "week" || params.get("mode") === "today") {
      setMode(params.get("mode"));
    }
    render();
  }

  global.PastoralMise = {
    migrate,
    getMassesForDate,
    getMassTimesForDate,
    getNextMassHint,
    formatMassScheduleHtml,
    formatMassScheduleText,
    weekdaysFromEntry,
    mountMisePage,
  };
})(typeof window !== "undefined" ? window : global);
