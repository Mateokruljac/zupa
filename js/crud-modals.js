/**
 * CRUD forme i modali — poziva se iz app.js (PastoralCrudModals.init)
 */
(function (global) {
  let api = null;

  function syncObiteljiView(root, opts = {}) {
    api.renderObiteljiPage();
    if (opts.openFamilyId) {
      setTimeout(() => api.openFamilyDetailModal(opts.openFamilyId, root), 0);
    } else {
      api.refreshFamilyDetailModal(root);
    }
  }

  function M() {
    return global.PastoralModal;
  }

  function openForm(opts) {
    if (!M()) return null;
    return M().openForm(opts);
  }

  function streetOptions(streets, selectedId) {
    return (streets || [])
      .map((s) => `<option value="${s.id}" ${s.id === selectedId ? "selected" : ""}>${api.escapeHtml(s.name)}</option>`)
      .join("");
  }

  function familyFormBody(fam, streets, isNew) {
    const y = new Date().getFullYear();
    const defAmt = api.getData().luknoDefaultAmount ?? (global.PastoralFamilyCrud?.DEFAULT_LUKNO ?? 150);
    const luknoBlock = isNew
      ? `
      <div class="form-group"><label>Lukno (${y}) plaćeno</label><input type="checkbox" name="luknoPaid" /></div>
      <div class="form-group"><label>Iznos lukna (€)</label><input type="number" name="luknoAmount" value="${defAmt}" min="0" /></div>
      <div class="form-group"><label>Davanje za crkvu (€)</label><input type="number" name="churchDonation" value="0" min="0" /></div>`
      : "";
    return `
      ${fam ? `<input type="hidden" name="id" value="${fam.id}" />` : ""}
      <div class="form-group"><label>Prezime *</label><input name="surname" value="${api.escapeHtml(fam?.surname || "")}" required /></div>
      <div class="form-group"><label>Ulica</label><select name="streetId">${streetOptions(streets, fam?.streetId)}</select></div>
      <div class="form-group form-wide"><label>Adresa (kućni br.)</label><input name="address" value="${api.escapeHtml(fam?.address || "")}" /></div>
      <div class="form-group"><label>Telefon</label><input name="phone" value="${api.escapeHtml(fam?.phone || "")}" /></div>
      <div class="form-group"><label>E-mail</label><input name="email" type="email" value="${api.escapeHtml(fam?.email || "")}" /></div>
      ${
        isNew
          ? ""
          : `<div class="form-group"><label>Status</label><select name="status">
        <option ${fam?.status === "aktivna" ? "selected" : ""}>aktivna</option>
        <option ${fam?.status === "nedostupna" ? "selected" : ""}>nedostupna</option>
        <option ${fam?.status === "odseljena" ? "selected" : ""}>odseljena</option>
      </select></div>
      <div class="form-group"><label>Željena misa</label><input name="preferredMass" value="${api.escapeHtml(fam?.preferredMass || "")}" placeholder="09:00" /></div>
      <div class="form-group form-wide"><label>Oznake (zarezom)</label><input name="tags" value="${api.escapeHtml((fam?.tags || []).join(", "))}" /></div>
      <div class="form-group form-wide"><label>Pastoralna bilješka</label><textarea name="pastoralNotes" rows="2">${api.escapeHtml(fam?.pastoralNotes || "")}</textarea></div>`
      }
      ${luknoBlock}`;
  }

  function memberFormBody(m) {
    return `
      <div class="form-group"><label>Ime *</label><input name="name" value="${api.escapeHtml(m?.name || "")}" required /></div>
      <div class="form-group"><label>Srodstvo</label><input name="relation" value="${api.escapeHtml(m?.relation || "")}" placeholder="otac, majka…" /></div>
      <div class="form-group"><label>God. rođenja</label><input name="birthYear" type="number" min="1920" max="2030" value="${m?.birthYear || ""}" /></div>
      <div class="form-group form-wide"><label>Uloge (zarezom)</label><input name="roles" value="${api.escapeHtml((m?.roles || []).join(", "))}" placeholder="ŽPV, kateheta" /></div>
      <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${api.escapeHtml(m?.notes || "")}" /></div>`;
  }

  function yearFormBody(row, defAmt) {
    return `
      <div class="form-group"><label>Godina</label><input name="year" type="number" value="${row?.year || new Date().getFullYear()}" min="1990" max="2100" required ${row ? "readonly" : ""} /></div>
      <div class="form-group"><label>Lukno plaćeno</label><input type="checkbox" name="luknoPaid" ${row?.luknoPaid ? "checked" : ""} /></div>
      <div class="form-group"><label>Iznos lukna (€)</label><input name="luknoAmount" type="number" min="0" value="${row?.luknoAmount ?? defAmt}" /></div>
      <div class="form-group"><label>Datum uplate lukna</label><input name="luknoPaidAt" type="date" value="${row?.luknoPaidAt || ""}" /></div>
      <div class="form-group"><label>Davanje za crkvu (€)</label><input name="churchDonation" type="number" min="0" value="${row?.churchDonation || 0}" /></div>
      <div class="form-group"><label>Datum davanja</label><input name="donationDate" type="date" value="${row?.donationDate || ""}" /></div>
      <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${api.escapeHtml(row?.notes || "")}" /></div>`;
  }

  const modals = {
    openFamilyCreate(root) {
      const data = api.getData();
      openForm({
        title: "Nova obitelj",
        size: "lg",
        body: familyFormBody(null, data.streets, true),
        onSubmit: (form) => {
          const fd = new FormData(form);
          const surname = fd.get("surname")?.trim();
          if (!surname) {
            api.showToast("Unesite prezime");
            return false;
          }
          const FC = global.PastoralFamilyCrud;
          const y = new Date().getFullYear();
          const fam = {
            id: api.uid("fam"),
            surname,
            streetId: fd.get("streetId"),
            address: fd.get("address")?.trim() || "",
            phone: fd.get("phone")?.trim() || "",
            email: fd.get("email")?.trim() || "",
            status: "aktivna",
            preferredMass: "",
            pastoralNotes: "",
            tags: [],
            members: [],
            contributions: [],
          };
          if (FC) {
            const row = FC.defaultContribution(y);
            row.luknoPaid = !!form.querySelector('[name="luknoPaid"]')?.checked;
            row.luknoAmount = Number(fd.get("luknoAmount")) || FC.DEFAULT_LUKNO;
            row.churchDonation = Number(fd.get("churchDonation")) || 0;
            if (row.luknoPaid) row.luknoPaidAt = new Date().toISOString().slice(0, 10);
            fam.contributions.push(row);
          }
          data.families.push(fam);
          api.persistFamilies(data, fam.id, root);
          api.showToast("Obitelj dodana");
          syncObiteljiView(root, { openFamilyId: fam.id });
        },
      });
    },

    openFamilyEdit(famId, root) {
      const data = api.getData();
      const fam = api.findFamily(data, famId);
      if (!fam) return;
      openForm({
        title: `Uredi — ${fam.surname}`,
        size: "lg",
        body: familyFormBody(fam, data.streets, false),
        onSubmit: (form) => {
          const fd = new FormData(form);
          fam.surname = fd.get("surname")?.trim() || fam.surname;
          fam.streetId = fd.get("streetId");
          fam.address = fd.get("address")?.trim() || "";
          fam.phone = fd.get("phone")?.trim() || "";
          fam.email = fd.get("email")?.trim() || "";
          fam.status = fd.get("status");
          fam.preferredMass = fd.get("preferredMass")?.trim() || "";
          fam.pastoralNotes = fd.get("pastoralNotes")?.trim() || "";
          fam.tags = fd.get("tags")?.trim()
            ? fd.get("tags").split(",").map((t) => t.trim()).filter(Boolean)
            : [];
          api.persistFamilies(data, fam.id, root);
          api.showToast("Obitelj spremljena");
          syncObiteljiView(root);
        },
      });
    },

    openMember(famId, memberId, root) {
      const data = api.getData();
      const fam = api.findFamily(data, famId);
      if (!fam) return;
      const m = memberId ? fam.members?.find((x) => x.id === memberId) : null;
      openForm({
        title: m ? "Uredi člana" : "Novi član",
        body: memberFormBody(m),
        onSubmit: (form) => {
          const fd = new FormData(form);
          const name = fd.get("name")?.trim();
          if (!name) {
            api.showToast("Unesite ime");
            return false;
          }
          const payload = {
            name,
            relation: fd.get("relation")?.trim() || "",
            birthYear: fd.get("birthYear") ? Number(fd.get("birthYear")) : "",
            roles: fd.get("roles")?.trim() ? fd.get("roles").split(",").map((t) => t.trim()) : [],
            notes: fd.get("notes")?.trim() || "",
          };
          if (m) {
            Object.assign(m, payload);
          } else {
            fam.members = fam.members || [];
            fam.members.push({ id: api.uid("m"), sacraments: [], ...payload });
          }
          api.persistFamilies(data, fam.id, root);
          api.showToast(m ? "Član ažuriran" : "Član dodan");
          syncObiteljiView(root);
        },
      });
    },

    openYear(famId, year, root) {
      const data = api.getData();
      const fam = api.findFamily(data, famId);
      const FC = global.PastoralFamilyCrud;
      if (!fam || !FC) return;
      const defAmt = data.luknoDefaultAmount ?? FC.DEFAULT_LUKNO;
      const row = year ? FC.ensureYear(fam, year) : null;
      openForm({
        title: year ? `Evidencija ${year}.` : "Nova godina",
        body: yearFormBody(row, defAmt),
        onSubmit: (form) => {
          const fd = new FormData(form);
          const yr = Number(fd.get("year"));
          if (!yr) {
            api.showToast("Unesite godinu");
            return false;
          }
          let c = FC.getContribution(fam, yr);
          if (!c) {
            if (year) {
              api.showToast("Godina nije pronađena");
              return false;
            }
            if (FC.getContribution(fam, yr)) {
              api.showToast("Ta godina već postoji");
              return false;
            }
            c = FC.defaultContribution(yr);
            fam.contributions.push(c);
          }
          c.luknoPaid = !!form.querySelector('[name="luknoPaid"]')?.checked;
          c.luknoAmount = Number(fd.get("luknoAmount")) || defAmt;
          c.luknoPaidAt = fd.get("luknoPaidAt") || "";
          c.churchDonation = Number(fd.get("churchDonation")) || 0;
          c.donationDate = fd.get("donationDate") || "";
          c.notes = fd.get("notes")?.trim() || "";
          if (c.luknoPaid && !c.luknoPaidAt) c.luknoPaidAt = new Date().toISOString().slice(0, 10);
          api.persistFamilies(data, fam.id, root);
          api.showToast("Evidencija spremljena");
          syncObiteljiView(root);
        },
      });
    },

    openStreet(streetId, onDone) {
      const data = api.getData();
      const st = streetId ? data.streets.find((s) => s.id === streetId) : null;
      openForm({
        title: st ? "Uredi ulicu" : "Nova ulica",
        body: `
          <div class="form-group"><label>Naziv ulice *</label><input name="name" value="${api.escapeHtml(st?.name || "")}" required /></div>
          <div class="form-group"><label>Kvart / zona</label><input name="zone" value="${api.escapeHtml(st?.zone || "")}" /></div>
          <div class="form-group form-wide"><label>Napomena</label><input name="notes" value="${api.escapeHtml(st?.notes || "")}" /></div>`,
        onSubmit: (form) => {
          const fd = new FormData(form);
          const name = fd.get("name")?.trim();
          if (!name) {
            api.showToast("Unesite naziv");
            return false;
          }
          if (st) {
            st.name = name;
            st.zone = fd.get("zone")?.trim() || "";
            st.notes = fd.get("notes")?.trim() || "";
          } else {
            data.streets.push({
              id: api.uid("st"),
              name,
              zone: fd.get("zone")?.trim() || "",
              sortOrder: data.streets.length + 1,
              notes: fd.get("notes")?.trim() || "",
            });
          }
          api.saveData(data);
          api.showToast(st ? "Ulica ažurirana" : "Ulica dodana");
          onDone?.();
        },
      });
    },

    openNakana(onDone) {
      const data = api.getData();
      const day = api.getSelectedCalendarDay();
      const times = data.massSchedule.map((ms) => ms.time);
      const opts = ["07:30", "09:00", "11:00", "18:00", ...times].filter((v, i, a) => a.indexOf(v) === i);
      openForm({
        title: `Nova nakana — ${api.fmtDate(day)}`,
        size: "lg",
        body: `
          <div class="form-group"><label>Misa (sat)</label><select name="massTime">${opts.map((t) => `<option>${t}</option>`).join("")}</select></div>
          <div class="form-group form-wide"><label>Za koga / namjera *</label><input name="intentionFor" required placeholder="Pokoj duše…" /></div>
          <div class="form-group"><label>Naručitelj</label><input name="requestedBy" placeholder="Ime i prezime" /></div>
          <div class="form-group"><label>Stipendij (€)</label><input name="stipend" type="number" min="0" value="30" /></div>
          <div class="form-group form-wide"><label>Bilješka</label><input name="notes" placeholder="Gregorian…" /></div>
          <p class="card-sub form-wide">Nakon spremanja odaberite način plaćanja u sljedećem koraku.</p>`,
        submitLabel: "Nastavi",
        onSubmit: (form) => {
          const fd = new FormData(form);
          const intentionFor = fd.get("intentionFor")?.trim();
          if (!intentionFor) {
            api.showToast("Unesite namjeru molitve");
            return false;
          }
          const fields = {
            date: day,
            massTime: fd.get("massTime"),
            intentionFor,
            requestedBy: fd.get("requestedBy")?.trim() || "",
            stipend: Number(fd.get("stipend")) || 0,
            notes: fd.get("notes")?.trim() || "",
          };
          M().close();
          M().confirm({
            title: "Plaćanje nakane",
            message: "Kako želite zabilježiti stipendij?",
            confirmLabel: "Plaćanje odmah",
            onConfirm: () => {
              const Pay = global.PastoralPayment;
              if (!Pay) {
                api.showToast("Modul plaćanja nije učitan");
                return;
              }
              Pay.runSimulation({
                amount: fields.stipend,
                title: fields.intentionFor,
                subtitle: `${fields.massTime} · ${fields.requestedBy || "—"}`,
                onSuccess: (payment) => api.saveIntentionPaid(fields, payment, onDone),
              });
            },
            onCancel: () => {
              M().confirm({
                title: "Platiti kasnije",
                message: "Spremiti nakanu bez plaćanja?",
                confirmLabel: "Spremi neplaćeno",
                onConfirm: () => api.saveIntentionUnpaid(fields, onDone),
              });
            },
          });
          return false;
        },
      });
    },

    openSacrament(arrayKey, record, onDone) {
      const forms = {
        baptisms: {
          title: record ? "Uredi krštenje" : "Novo krštenje",
          body: `
            <div class="form-group"><label>Dijete *</label><input name="childName" value="${api.escapeHtml(record?.childName || "")}" required /></div>
            <div class="form-group"><label>Datum krštenja</label><input name="baptismDate" type="date" value="${record?.baptismDate || ""}" /></div>
            <div class="form-group"><label>Roditelji</label><input name="parents" value="${api.escapeHtml(record?.parents || "")}" /></div>
            <div class="form-group"><label>Kum(ovi)</label><input name="godparents" value="${api.escapeHtml(record?.godparents || "")}" /></div>
            <div class="form-group"><label>Matica br.</label><input name="registryNo" value="${api.escapeHtml(record?.registryNo || "")}" /></div>
            <div class="form-group"><label>Naknada (€)</label><input name="stipend" type="number" min="0" step="1" value="${record?.stipend ?? 80}" /></div>
            <div class="form-group"><label>Plaćeno</label><input type="checkbox" name="stipendPaid" ${record?.stipendPaid ? "checked" : ""} /></div>`,
          apply: (fd, row, form) => {
            row.childName = fd.get("childName")?.trim();
            row.baptismDate = fd.get("baptismDate") || "";
            row.parents = fd.get("parents")?.trim() || "";
            row.godparents = fd.get("godparents")?.trim() || "";
            row.registryNo = fd.get("registryNo")?.trim() || "";
            row.stipend = Number(fd.get("stipend")) || 0;
            row.stipendPaid = !!form?.querySelector('[name="stipendPaid"]')?.checked;
          },
          defaults: { birthDate: "", celebrant: "", status: "upis", stipend: 80, stipendPaid: false },
        },
        weddings: {
          title: record ? "Uredi vjenčanje" : "Novo vjenčanje",
          body: `
            <div class="form-group form-wide"><label>Par *</label><input name="couple" value="${api.escapeHtml(record?.couple || "")}" required /></div>
            <div class="form-group"><label>Datum</label><input name="weddingDate" type="date" value="${record?.weddingDate || ""}" /></div>
            <div class="form-group"><label>Svećenik</label><input name="celebrant" value="${api.escapeHtml(record?.celebrant || "")}" /></div>
            <div class="form-group"><label>Status</label><select name="status"><option ${record?.status === "dogovoreno" ? "selected" : ""}>dogovoreno</option><option ${record?.status === "upis" ? "selected" : ""}>upis</option><option ${record?.status === "obavljeno" ? "selected" : ""}>obavljeno</option></select></div>
            <div class="form-group"><label>Naknada (€)</label><input name="stipend" type="number" min="0" value="${record?.stipend ?? 200}" /></div>
            <div class="form-group"><label>Plaćeno</label><input type="checkbox" name="stipendPaid" ${record?.stipendPaid ? "checked" : ""} /></div>`,
          apply: (fd, row, form) => {
            row.couple = fd.get("couple")?.trim();
            row.weddingDate = fd.get("weddingDate") || "";
            row.celebrant = fd.get("celebrant")?.trim() || "";
            row.status = fd.get("status");
            row.stipend = Number(fd.get("stipend")) || 0;
            row.stipendPaid = !!form?.querySelector('[name="stipendPaid"]')?.checked;
          },
          defaults: { church: "", preparatorySessions: 0, documentsOk: false, witnesses: "", stipend: 200, stipendPaid: false },
        },
        funerals: {
          title: record ? "Uredi pogreb" : "Novi pogreb",
          body: `
            <div class="form-group"><label>Pokojnik *</label><input name="deceased" value="${api.escapeHtml(record?.deceased || "")}" required /></div>
            <div class="form-group"><label>Datum pogreba</label><input name="funeralDate" type="date" value="${record?.funeralDate || ""}" /></div>
            <div class="form-group"><label>Groblje</label><input name="cemetery" value="${api.escapeHtml(record?.cemetery || "")}" /></div>
            <div class="form-group form-wide"><label>Kontakt obitelji</label><input name="familyContact" value="${api.escapeHtml(record?.familyContact || "")}" /></div>
            <div class="form-group"><label>Status</label><select name="status"><option ${record?.status === "potvrđeno" ? "selected" : ""}>potvrđeno</option><option ${record?.status === "upis" ? "selected" : ""}>upis</option></select></div>
            <div class="form-group"><label>Naknada (€)</label><input name="stipend" type="number" min="0" value="${record?.stipend ?? 50}" /></div>
            <div class="form-group"><label>Plaćeno</label><input type="checkbox" name="stipendPaid" ${record?.stipendPaid ? "checked" : ""} /></div>`,
          apply: (fd, row, form) => {
            row.deceased = fd.get("deceased")?.trim();
            row.funeralDate = fd.get("funeralDate") || "";
            row.cemetery = fd.get("cemetery")?.trim() || "";
            row.familyContact = fd.get("familyContact")?.trim() || "";
            row.status = fd.get("status");
            row.stipend = Number(fd.get("stipend")) || 0;
            row.stipendPaid = !!form?.querySelector('[name="stipendPaid"]')?.checked;
          },
          defaults: { deathDate: "", celebrant: "", stipend: 50, stipendPaid: false },
        },
      };
      const cfg = forms[arrayKey];
      if (!cfg) return;
      openForm({
        title: cfg.title,
        size: "lg",
        body: cfg.body,
        onSubmit: (form) => {
          const fd = new FormData(form);
          const data = api.getData();
          if (record) {
            cfg.apply(fd, record, form);
          } else {
            const row = { id: api.uid(arrayKey.slice(0, 1)), ...cfg.defaults };
            cfg.apply(fd, row, form);
            data[arrayKey].push(row);
          }
          api.saveData(data);
          api.showToast(record ? "Zapis spremljen" : "Zapis dodan");
          onDone?.();
        },
      });
    },

    openTask(task, onDone) {
      openForm({
        title: task ? "Uredi zadatak" : "Novi zadatak",
        body: `
          <div class="form-group form-wide"><label>Naslov *</label><input name="title" value="${api.escapeHtml(task?.title || "")}" required /></div>
          <div class="form-group"><label>Rok</label><input name="due" type="date" value="${task?.due || ""}" /></div>
          <div class="form-group"><label>Kategorija</label><input name="category" value="${api.escapeHtml(task?.category || "ŽPV")}" /></div>
          <div class="form-group"><label>Prioritet</label><select name="priority">
            <option ${task?.priority === "visoka" ? "selected" : ""}>visoka</option>
            <option ${!task || task.priority === "srednja" ? "selected" : ""}>srednja</option>
            <option ${task?.priority === "niska" ? "selected" : ""}>niska</option>
          </select></div>
          ${task ? `<div class="form-group"><label>Gotovo</label><input type="checkbox" name="done" ${task.done ? "checked" : ""} /></div>` : ""}`,
        onSubmit: (form) => {
          const fd = new FormData(form);
          const title = fd.get("title")?.trim();
          if (!title) {
            api.showToast("Unesite naslov");
            return false;
          }
          const data = api.getData();
          if (task) {
            task.title = title;
            task.due = fd.get("due") || "";
            task.category = fd.get("category")?.trim() || task.category;
            task.priority = fd.get("priority");
            task.done = !!form.querySelector('[name="done"]')?.checked;
          } else {
            data.tasks.push({
              id: api.uid("t"),
              title,
              due: fd.get("due") || "",
              category: fd.get("category")?.trim() || "ŽPV",
              priority: fd.get("priority"),
              done: false,
            });
          }
          api.saveData(data);
          api.showToast(task ? "Zadatak spremljen" : "Zadatak dodan");
          onDone?.();
        },
      });
    },

    openKrizmaYear(root) {
      openForm({
        title: "Nova godina krizme",
        body: `<div class="form-group"><label>Godina</label><input name="year" type="number" value="${new Date().getFullYear() + 1}" min="2020" max="2100" required /></div>
          <div class="form-group"><label>Datum obreda</label><input name="ceremonyDate" type="date" /></div>
          <div class="form-group form-wide"><label>Biskup / celebrant</label><input name="bishop" /></div>`,
        onSubmit: (form) => {
          const fd = new FormData(form);
          const y = Number(fd.get("year"));
          if (!y) {
            api.showToast("Unesite godinu");
            return false;
          }
          const data = api.getData();
          if (data.confirmations.some((c) => c.year === y)) {
            api.showToast("Godina već postoji");
            return false;
          }
          data.confirmations.unshift({
            id: api.uid("conf"),
            year: y,
            bishop: fd.get("bishop")?.trim() || "",
            ceremonyDate: fd.get("ceremonyDate") || `${y}-05-01`,
            catechists: [],
            candidates: [],
          });
          api.saveData(data);
          root.dataset.year = String(y);
          api.showToast(`Godina ${y} dodana`);
          api.renderKrizmaPage();
        },
      });
    },

    openKrizmanik(year, candidate, onDone) {
      openForm({
        title: candidate ? "Uredi krizmanika" : "Novi krizmanik",
        size: "lg",
        body: `
          <div class="form-group form-wide"><label>Ime i prezime *</label><input name="name" value="${api.escapeHtml(candidate?.name || "")}" required /></div>
          <div class="form-group"><label>Škola</label><input name="school" value="${api.escapeHtml(candidate?.school || "")}" /></div>
          <div class="form-group"><label>Razred</label><input name="class" value="${api.escapeHtml(candidate?.class || "")}" /></div>
          <div class="form-group"><label>Grupa</label><input name="group" value="${api.escapeHtml(candidate?.group || "A")}" /></div>
          <div class="form-group"><label>Kum/ka</label><input name="sponsor" value="${api.escapeHtml(candidate?.sponsor || "")}" /></div>`,
        onSubmit: (form) => {
          const fd = new FormData(form);
          const name = fd.get("name")?.trim();
          if (!name) {
            api.showToast("Unesite ime");
            return false;
          }
          const data = api.getData();
          const c = data.confirmations.find((x) => x.year === year);
          if (!c) return false;
          const payload = {
            name,
            birthDate: candidate?.birthDate || "",
            school: fd.get("school")?.trim() || "",
            class: fd.get("class")?.trim() || "",
            group: fd.get("group")?.trim() || "A",
            baptized: candidate?.baptized || "",
            sponsor: fd.get("sponsor")?.trim() || "",
            status: candidate?.status || "upis",
            oib: candidate?.oib || "",
          };
          if (candidate) Object.assign(candidate, payload);
          else c.candidates.push({ id: api.uid("cr"), ...payload });
          api.saveData(data);
          api.showToast(candidate ? "Krizmanik ažuriran" : "Krizmanik dodan");
          onDone?.();
        },
      });
    },

    openKateheta(year, person, onDone) {
      openForm({
        title: person ? "Uredi suradnika" : "Novi suradnik",
        body: `
          <div class="form-group"><label>Ime *</label><input name="name" value="${api.escapeHtml(person?.name || "")}" required /></div>
          <div class="form-group"><label>Uloga</label><select name="role">
            <option ${person?.role === "kateheta" ? "selected" : ""}>kateheta</option>
            <option ${person?.role === "župnik" ? "selected" : ""}>župnik</option>
            <option ${person?.role === "vikar" ? "selected" : ""}>vikar</option>
            <option ${person?.role === "surdadnik" ? "selected" : ""}>surdadnik</option>
          </select></div>
          <div class="form-group"><label>Telefon</label><input name="phone" value="${api.escapeHtml(person?.phone || "")}" /></div>`,
        onSubmit: (form) => {
          const fd = new FormData(form);
          const name = fd.get("name")?.trim();
          if (!name) {
            api.showToast("Unesite ime");
            return false;
          }
          const data = api.getData();
          const c = data.confirmations.find((x) => x.year === year);
          if (!c) return false;
          const payload = {
            name,
            role: fd.get("role"),
            phone: fd.get("phone")?.trim() || "",
          };
          if (person) Object.assign(person, payload);
          else c.catechists.push({ id: api.uid("ct"), ...payload });
          api.saveData(data);
          api.showToast(person ? "Suradnik ažuriran" : "Suradnik dodan");
          onDone?.();
        },
      });
    },
  };

  global.PastoralCrudModals = {
    init(hooks) {
      api = hooks;
    },
    ...modals,
    confirm: (message, opts) => {
      const Mm = global.PastoralModal;
      if (!Mm) return Promise.resolve(confirm(message));
      return Mm.confirmPromise({ message, ...opts });
    },
  };
})(typeof window !== "undefined" ? window : global);
