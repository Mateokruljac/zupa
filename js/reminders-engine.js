/**
 * Podsjetnici — agregacija obaveza za župni ured
 */
(function (global) {
  const DISMISS_KEY = "pastoral_dismissed_reminders";

  function loadDismissed() {
    try {
      return JSON.parse(localStorage.getItem(DISMISS_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function saveDismissed(map) {
    localStorage.setItem(DISMISS_KEY, JSON.stringify(map));
  }

  function addDaysIso(n) {
    const d = new Date();
    d.setDate(d.getDate() + n);
    return d.toISOString().slice(0, 10);
  }

  function daysSince(iso) {
    if (!iso) return 999;
    const a = new Date(iso + "T12:00:00");
    const b = new Date();
    b.setHours(12, 0, 0, 0);
    return Math.floor((b - a) / 86400000);
  }

  function collectReminders(data, opts = {}) {
    const today = new Date().toISOString().slice(0, 10);
    const y = new Date().getFullYear();
    const dismissed = opts.includeDismissed ? {} : loadDismissed();
    const FC = global.PastoralFamilyCrud;
    const Prep = global.PastoralPreparation;
    const items = [];

    function push(r) {
      if (dismissed[r.id]) return;
      items.push(r);
    }

    (data.publicSubmissions || [])
      .filter((s) => s.status === "nova")
      .forEach((s) => {
        push({
          id: `sub_${s.id}`,
          priority: "visoka",
          category: "prijava",
          title: `Nova javna prijava: ${s.type}`,
          sub: new Date(s.submittedAt).toLocaleString("hr-HR"),
          href: "pages/javne-prijave.html",
          due: today,
        });
      });

    (data.tasks || [])
      .filter((t) => !t.done)
      .forEach((t) => {
        const late = t.due && t.due < today;
        push({
          id: `task_${t.id}`,
          priority: late || t.priority === "visoka" ? "visoka" : "srednja",
          category: "zadatak",
          title: t.title,
          sub: `${t.category} · rok ${t.due || "—"}`,
          href: "pages/zadaci.html",
          due: t.due || today,
        });
      });

    (data.intentions || [])
      .filter((n) => !n.paid && Number(n.stipend) > 0)
      .forEach((n) => {
        push({
          id: `nak_${n.id}`,
          priority: n.date <= today ? "visoka" : "srednja",
          category: "nakana",
          title: `Neplaćena nakana: ${n.intentionFor}`,
          sub: `${n.date} ${n.massTime}`,
          href: `pages/nakane.html?date=${n.date}`,
          due: n.date,
        });
      });

    (data.families || []).forEach((fam) => {
      const row = (fam.contributions || []).find((c) => c.year === y);
      if (row && !row.luknoPaid) {
        push({
          id: `lukno_${fam.id}_${y}`,
          priority: "srednja",
          category: "lukno",
          title: `Lukno ${y} — obitelj ${fam.surname}`,
          sub: fam.address || fam.phone || "",
          href: `pages/obitelji.html?family=${encodeURIComponent(fam.id)}`,
          due: today,
        });
      }
      if (fam.pastoralNotes?.toLowerCase().includes("posjetiti") || daysSince(fam.lastVisit) > 90) {
        if (fam.status === "aktivna" && daysSince(fam.lastVisit) > 60) {
          push({
            id: `visit_fam_${fam.id}`,
            priority: daysSince(fam.lastVisit) > 120 ? "visoka" : "srednja",
            category: "posjet",
            title: `Posjet obitelji ${fam.surname}`,
            sub: fam.lastVisit ? `Zadnji posjet: ${fam.lastVisit}` : "Još nema zabilježenog posjeta",
            href: `pages/posjete.html?family=${encodeURIComponent(fam.id)}`,
            due: today,
          });
        }
      }
    });

    (data.visits || [])
      .filter((v) => !v.done && v.scheduled && v.scheduled <= addDaysIso(7))
      .forEach((v) => {
        push({
          id: `visit_${v.id}`,
          priority: v.scheduled < today ? "visoka" : "srednja",
          category: "posjet",
          title: v.purpose || "Pastoralni posjet",
          sub: `${v.person || v.familyLabel || ""} · ${v.scheduled}`,
          href: "pages/posjete.html",
          due: v.scheduled,
        });
      });

    ["baptisms", "weddings"].forEach((key) => {
      const page = key === "baptisms" ? "krsenja" : "vjencanja";
      (data[key] || []).forEach((rec) => {
        const dt = rec.baptismDate || rec.weddingDate;
        if (Prep && dt && dt >= today && dt <= addDaysIso(21)) {
          const prog = Prep.getProgress(rec, key);
          if (prog.percent < 100) {
            push({
              id: `prep_${key}_${rec.id}`,
              priority: "srednja",
              category: "priprema",
              title: `Priprema (${prog.percent}%): ${rec.childName || rec.couple}`,
              sub: `Obred ${dt}`,
              href: `pages/${page}.html`,
              due: dt,
            });
          }
        }
        if (dt && dt >= today && dt <= addDaysIso(14)) {
          push({
            id: `sac_${key}_${rec.id}`,
            priority: "srednja",
            category: "sakrament",
            title: `${key === "baptisms" ? "Krštenje" : "Vjenčanje"}: ${rec.childName || rec.couple}`,
            sub: dt,
            href: `pages/${page}.html`,
            due: dt,
          });
        }
      });
    });

    (data.funerals || []).forEach((f) => {
      if (f.funeralDate && f.funeralDate >= today && f.funeralDate <= addDaysIso(7)) {
        push({
          id: `fun_${f.id}`,
          priority: "visoka",
          category: "pogreb",
          title: `Pogreb: ${f.deceased}`,
          sub: f.funeralDate,
          href: "pages/pogrebi.html",
          due: f.funeralDate,
        });
      }
    });

    (data.invoices || [])
      .filter((i) => i.status !== "placen" && i.status !== "storno")
      .forEach((i) => {
        const rest = (Number(i.total) || 0) - (Number(i.paidAmount) || 0);
        if (rest > 0) {
          push({
            id: `inv_${i.id}`,
            priority: i.dueDate && i.dueDate < today ? "visoka" : "srednja",
            category: "racun",
            title: `Račun ${i.number} — ${i.payerName}`,
            sub: `${rest.toFixed(2)} € preostalo`,
            href: "pages/racuni.html",
            due: i.dueDate || today,
          });
        }
      });

    const order = { visoka: 0, srednja: 1, niska: 2 };
    return items.sort((a, b) => (order[a.priority] ?? 9) - (order[b.priority] ?? 9) || (a.due || "").localeCompare(b.due || ""));
  }

  function renderInboxHtml(items, api) {
    const esc = api.escapeHtml;
    const purl = api.pageUrl;
    if (!items.length) {
      return '<p class="empty-state">Nema aktivnih podsjetnika. Odlično!</p>';
    }
    return `<ul class="reminders-inbox">${items
      .map(
        (r) => `
      <li class="reminders-item reminders-item--${r.priority}" data-reminder-id="${esc(r.id)}">
        <a href="${purl(r.href)}" class="reminders-item-main">
          <span class="badge">${esc(r.category)}</span>
          <strong>${esc(r.title)}</strong>
          <small>${esc(r.sub)}</small>
        </a>
        <button type="button" class="btn btn-ghost btn-sm" data-dismiss-reminder="${esc(r.id)}" title="Sakrij do sutra">×</button>
      </li>`
      )
      .join("")}</ul>`;
  }

  function bindInbox(root, api, getData) {
    root?.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-dismiss-reminder]");
      if (!btn) return;
      ev.preventDefault();
      ev.stopPropagation();
      const map = loadDismissed();
      map[btn.dataset.dismissReminder] = Date.now();
      saveDismissed(map);
      api.showToast?.("Podsjetnik sakriven");
      if (root.dataset.remount) {
        global[root.dataset.remount]?.();
      } else {
        root.dispatchEvent(new CustomEvent("pastoral-reminders-refresh"));
      }
    });
  }

  function mountPodsjetniciPage(root, api) {
    function render() {
      const data = api.getData();
      const items = collectReminders(data);
      root.innerHTML = `
        <section class="card">
          <div class="reminders-toolbar">
            <button type="button" class="btn btn-ghost btn-sm" id="rem-clear-dismissed">Očisti skrivene</button>
            <a href="${api.pageUrl("app.html")}" class="btn btn-ghost btn-sm">Nadzorna ploča</a>
          </div>
          <h2 class="section-title">Inbox podsjetnika <span class="badge">${items.length}</span></h2>
          <p class="card-sub">Prioritet: javne prijave, zakašnjeli zadaci, posjeti, neplaćeno, pripreme sakramenata.</p>
          <div id="reminders-list-mount">${renderInboxHtml(items, api)}</div>
        </section>`;
      const mount = root.querySelector("#reminders-list-mount");
      mount.dataset.remount = "PastoralReminders_rerender";
      global.PastoralReminders_rerender = render;
      bindInbox(mount, api, api.getData);
      root.querySelector("#rem-clear-dismissed")?.addEventListener("click", () => {
        saveDismissed({});
        api.showToast("Skriveni podsjetnici očišćeni");
        render();
      });
      mount.addEventListener("pastoral-reminders-refresh", render);
    }
    render();
  }

  global.PastoralReminders = {
    collectReminders,
    renderInboxHtml,
    bindInbox,
    mountPodsjetniciPage,
    getCount(data) {
      return collectReminders(data).length;
    },
  };
})(typeof window !== "undefined" ? window : global);
