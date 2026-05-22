/**
 * Poruke između korisnika ureda (župni-ured priručnik)
 */
(function (global) {
  function migrate(data) {
    if (!Array.isArray(data.staffMessages)) {
      data.staffMessages = [
        {
          id: "msg1",
          from: "vlč. Krunoslav Karas",
          fromRole: "zupnik",
          to: "Marija Kovač",
          toRole: "kateheta",
          subject: "Krizma — raspored sastanaka",
          body: "Molim provjeru popisa krizmanika prije sljedećeg ŽPV-a.",
          at: new Date(Date.now() - 86400000).toISOString(),
          read: false,
        },
        {
          id: "msg2",
          from: "Josip Marić",
          fromRole: "upravitelj",
          to: "vlč. Krunoslav Karas",
          toRole: "zupnik",
          subject: "Pregled blagajne za ŽEV",
          body: "Plavi dnevnik za ožujak spreman za pregled u petak.",
          at: new Date(Date.now() - 3600000).toISOString(),
          read: false,
        },
      ];
    }
    return data;
  }

  function staffUserFromSession() {
    const key = global.PastoralParish?.SESSION_KEY || "pastoral_session";
    let session = {};
    try {
      session = JSON.parse(localStorage.getItem(key) || "{}");
    } catch {
      /* ignore */
    }
    if (session.role === "zupnik") return "vlč. Krunoslav Karas";
    if (session.role === "kateheta") return "Marija Kovač";
    return "Josip Marić";
  }

  function unreadCount(data, userName) {
    return (data.staffMessages || []).filter((m) => !m.read && m.to === userName).length;
  }

  function mountPorukePage(root, api) {
    migrate(api.getData());
    const me = staffUserFromSession();

    function renderList() {
      const data = api.getData();
      const esc = api.escapeHtml;
      const msgs = [...(data.staffMessages || [])].sort((a, b) => (b.at || "").localeCompare(a.at || ""));

      root.innerHTML = `
        <section class="card">
          <div class="racuni-toolbar">
            <button type="button" class="btn btn-primary btn-sm" id="msg-new">Nova poruka</button>
            <span class="card-sub">Prijavljeni: <strong>${esc(me)}</strong></span>
          </div>
          <table class="data-table">
            <thead><tr><th></th><th>Od</th><th>Za</th><th>Predmet</th><th>Datum</th></tr></thead>
            <tbody>
              ${msgs
                .map(
                  (m) => `<tr data-msg-id="${esc(m.id)}" class="list-item--clickable ${!m.read && m.to === me ? "msg-unread" : ""}">
                    <td>${!m.read && m.to === me ? "●" : ""}</td>
                    <td>${esc(m.from)}</td>
                    <td>${esc(m.to)}</td>
                    <td><strong>${esc(m.subject)}</strong></td>
                    <td>${new Date(m.at).toLocaleString("hr-HR")}</td>
                  </tr>`
                )
                .join("")}
            </tbody>
          </table>
        </section>`;

      root.querySelector("#msg-new")?.addEventListener("click", () => renderCompose());
      root.querySelectorAll("[data-msg-id]").forEach((tr) => {
        tr.addEventListener("click", () => {
          const m = msgs.find((x) => x.id === tr.dataset.msgId);
          if (m) renderRead(m);
        });
      });
    }

    function renderRead(m) {
      const esc = api.escapeHtml;
      if (m.to === me) m.read = true;
      api.saveData(api.getData());
      root.innerHTML = `
        <section class="card">
          <button type="button" class="btn btn-ghost btn-sm" id="msg-back">← Natrag</button>
          <button type="button" class="btn btn-ghost btn-sm" id="msg-del">Obriši</button>
          <h2 class="section-title">${esc(m.subject)}</h2>
          <p class="card-sub">Od: ${esc(m.from)} → ${esc(m.to)} · ${new Date(m.at).toLocaleString("hr-HR")}</p>
          <p style="margin-top:16px;white-space:pre-wrap">${esc(m.body)}</p>
        </section>`;
      root.querySelector("#msg-back")?.addEventListener("click", renderList);
      root.querySelector("#msg-del")?.addEventListener("click", () => {
        const d = api.getData();
        d.staffMessages = (d.staffMessages || []).filter((x) => x.id !== m.id);
        api.saveData(d);
        api.showToast("Obrisano");
        renderList();
      });
    }

    function renderCompose() {
      root.innerHTML = `
        <section class="card">
          <button type="button" class="btn btn-ghost btn-sm" id="msg-back">← Natrag</button>
          <h2 class="section-title">Nova poruka</h2>
          <div class="form-grid">
            <div class="form-group"><label>Primatelj</label>
              <select id="msg-to">
                <option>vlč. Krunoslav Karas</option>
                <option>Marija Kovač</option>
                <option>Josip Marić</option>
                <option>Ana Horvat</option>
              </select>
            </div>
            <div class="form-group form-wide"><label>Predmet</label><input id="msg-subject" type="text"></div>
            <div class="form-group form-wide"><label>Tekst</label><textarea id="msg-body" rows="6"></textarea></div>
          </div>
          <button type="button" class="btn btn-primary" id="msg-send">Pošalji</button>
        </section>`;
      root.querySelector("#msg-back")?.addEventListener("click", renderList);
      root.querySelector("#msg-send")?.addEventListener("click", () => {
        const d = api.getData();
        migrate(d);
        d.staffMessages.unshift({
          id: `msg_${Date.now()}`,
          from: me,
          fromRole: session.role || "",
          to: document.getElementById("msg-to")?.value || "",
          toRole: "",
          subject: document.getElementById("msg-subject")?.value.trim() || "(bez predmeta)",
          body: document.getElementById("msg-body")?.value.trim() || "",
          at: new Date().toISOString(),
          read: false,
        });
        api.saveData(d);
        api.showToast("Poslano");
        renderList();
      });
    }

    renderList();
  }

  global.PastoralStaffMessages = { migrate, staffUserFromSession, unreadCount, mountPorukePage };
})(typeof window !== "undefined" ? window : global);
