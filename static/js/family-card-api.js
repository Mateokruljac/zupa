(function () {
  "use strict";

  const dialog = document.getElementById("family-detail-dialog");
  if (!dialog) return;

  const MONTHS = ["sij", "velj", "ožu", "tra", "svi", "lip", "srp", "kol", "ruj", "lis", "stu", "pro"];
  const ENDPOINTS = {
    get_family: (familyId) => ({ method: "GET", url: "/api/families/" + familyId + "/" }),
    update_family: (familyId) => ({ method: "PATCH", url: "/api/families/" + familyId + "/" }),
    save_family_member: (familyId) => ({ method: "PUT", url: "/api/families/" + familyId + "/members/" }),
    save_family_contribution: (familyId) => ({ method: "PUT", url: "/api/families/" + familyId + "/contributions/" }),
    update_family_notes: (familyId) => ({ method: "PATCH", url: "/api/families/" + familyId + "/notes/" }),
    delete_family: (familyId) => ({ method: "DELETE", url: "/api/families/" + familyId + "/" }),
    delete_family_member: (familyId, memberId) => ({
      method: "DELETE",
      url: "/api/families/" + familyId + "/members/" + encodeURIComponent(memberId) + "/",
    }),
    delete_family_contribution: (familyId, contributionId) => ({
      method: "DELETE",
      url: "/api/families/" + familyId + "/contributions/" + encodeURIComponent(contributionId) + "/",
    }),
  };

  function currentFamilyId() {
    const field = dialog.querySelector("[name='family_id']");
    return field ? field.value : "";
  }

  function setFamilyIdFields(familyId) {
    document.querySelectorAll("[data-family-id-field], [name='family_id']").forEach((field) => {
      if (field.closest("#new-family-dialog")) return;
      field.value = familyId || "";
    });
  }

  function setFamilyHash(familyId) {
    const url = new URL(window.location.href);
    if (familyId) url.hash = "family=" + encodeURIComponent(familyId);
    else url.hash = "";
    window.history.replaceState(null, "", url.pathname + url.search + url.hash);
  }

  function openDialog() {
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  function familyIdFromHash() {
    const match = /^#family=(.+)$/.exec(window.location.hash || "");
    return match ? decodeURIComponent(match[1]) : "";
  }

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.getAttribute("content")) return meta.getAttribute("content");
    const inp = dialog.querySelector("[name=csrfmiddlewaretoken]");
    if (inp && inp.value) return inp.value;
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function swalConfirm(title, text, confirmButtonText) {
    if (!window.Swal) return Promise.resolve(window.confirm(text || title));
    return window.Swal.fire({
      target: dialog,
      title: title,
      text: text || "",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: confirmButtonText || "Obriši",
      cancelButtonText: "Odustani",
      reverseButtons: true,
      focusCancel: true,
      heightAuto: false,
    }).then((result) => Boolean(result.isConfirmed));
  }

  function swalAlert(title, text, icon) {
    if (!window.Swal) {
      window.alert(text || title);
      return Promise.resolve();
    }
    return window.Swal.fire({
      target: dialog,
      title: title,
      text: text || "",
      icon: icon || "info",
      confirmButtonText: "U redu",
      heightAuto: false,
    });
  }

  function formatDate(isoValue) {
    const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoValue || "");
    if (!match) return "";
    const monthName = MONTHS[Number(match[2]) - 1];
    if (!monthName) return "";
    return Number(match[3]) + ". " + monthName + " " + match[1] + ".";
  }

  function formatMoney(amount) {
    const number = Number(amount);
    if (!Number.isFinite(number)) return "—";
    return number.toFixed(2) + " €";
  }

  function showStatus(message, state) {
    const status = dialog.querySelector("[data-family-card-status]");
    if (!status) return;
    status.hidden = !message;
    status.dataset.state = state || "";
    status.textContent = message || "";
  }

  function clearErrors(form) {
    form.querySelectorAll(".errorlist").forEach((list) => list.remove());
  }

  function showErrors(form, fields) {
    clearErrors(form);
    Object.entries(fields || {}).forEach(([fieldName, messages]) => {
      if (fieldName === "__all__") return;
      const field = form.elements[fieldName];
      if (!field) return;
      const list = document.createElement("ul");
      list.className = "errorlist";
      messages.forEach((message) => {
        const item = document.createElement("li");
        item.textContent = message;
        list.append(item);
      });
      (field.closest("p") || field.parentElement).append(list);
    });
  }

  function setText(selector, text) {
    const element = dialog.querySelector(selector);
    if (element) element.textContent = text;
  }

  function paintSummary(card) {
    setText("[data-family-card-title]", "Obitelj " + (card.surname || ""));
    setText("[data-family-card-address]", card.address || "—");
    const street = dialog.querySelector("[data-family-card-street]");
    if (street) {
      street.hidden = !card.streetName;
      street.textContent = card.streetName || "";
    }
    const phone = dialog.querySelector("[data-family-card-phone]");
    if (phone) {
      phone.hidden = !card.phone;
      phone.textContent = card.phone || "";
    }
    const lukno = dialog.querySelector("[data-family-card-lukno]");
    if (lukno) {
      lukno.replaceChildren(document.createTextNode("Lukno " + card.currentYear + ": "));
      const badge = document.createElement("span");
      badge.className = "badge";
      if (card.luknoStatus === "paid") {
        badge.classList.add("badge-done");
        badge.textContent = "plaćeno";
      } else if (card.luknoStatus === "unpaid") {
        badge.classList.add("badge-urgent");
        badge.textContent = "nije plaćeno";
      } else {
        badge.textContent = "nema zapisa";
      }
      lukno.append(badge);
    }
    const visit = dialog.querySelector("[data-family-card-visit]");
    if (visit && card.lastVisitOn !== undefined) {
      visit.replaceChildren();
      visit.append(document.createTextNode("Zadnji posjet: "));
      if (card.lastVisitOn) {
        const time = document.createElement("time");
        time.dateTime = card.lastVisitOn;
        time.textContent = formatDate(card.lastVisitOn) || card.lastVisitOn;
        visit.append(time);
        if (Number(card.lastVisitDays) > 365) {
          const overdue = document.createElement("span");
          overdue.className = "badge badge-urgent";
          overdue.textContent = "više od godine";
          visit.append(overdue);
        }
      } else {
        const missing = document.createElement("span");
        missing.className = "badge badge-urgent";
        missing.textContent = "nema zapisa";
        visit.append(missing);
      }
      if (card.needsPastoralFollowup) {
        const due = document.createElement("span");
        due.className = "badge badge-urgent";
        due.textContent = "posjetiti";
        visit.append(due);
      }
    }
    const gaps = dialog.querySelector("[data-family-card-gaps]");
    if (gaps) {
      gaps.replaceChildren();
      if (card.dataGaps && card.dataGaps.length) {
        const aside = document.createElement("aside");
        aside.className = "operational-warning";
        const title = document.createElement("strong");
        title.textContent = "Karton treba dopuniti:";
        const detail = document.createElement("span");
        detail.textContent = card.dataGaps.join(", ");
        aside.append(title, detail);
        gaps.append(aside);
      }
    }
  }

  function appendAmount(cell, amount, isoDate) {
    cell.append(document.createTextNode(formatMoney(amount)));
    const formattedDate = formatDate(isoDate);
    if (!formattedDate) return;
    const dateElement = document.createElement("small");
    dateElement.textContent = formattedDate;
    cell.append(dateElement);
  }

  function paintMembers(members) {
    const tableBody = dialog.querySelector("[data-family-members]");
    if (!tableBody) return;
    tableBody.replaceChildren();
    if (!members.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 6;
      cell.className = "empty-state";
      cell.textContent = "Još nema upisanih članova.";
      row.append(cell);
      tableBody.append(row);
      return;
    }
    members.forEach((member) => {
      const row = document.createElement("tr");
      const givenCell = document.createElement("td");
      const givenName = document.createElement("strong");
      givenName.textContent = member.givenName || member.name || "—";
      givenCell.append(givenName);
      const surnameCell = document.createElement("td");
      surnameCell.textContent = member.surname || "—";
      const relationCell = document.createElement("td");
      relationCell.textContent = member.relation || "—";
      const birthCell = document.createElement("td");
      birthCell.textContent = formatDate(member.birthDate) || member.birthYear || "—";
      const notesCell = document.createElement("td");
      const notesText = (member.notes || "").trim();
      if (notesText) {
        const note = document.createElement("span");
        note.className = "family-member-note";
        note.title = notesText;
        note.textContent = notesText.length > 40 ? notesText.slice(0, 37) + "…" : notesText;
        notesCell.append(note);
      } else {
        notesCell.textContent = "—";
      }
      const actionCell = document.createElement("td");
      actionCell.className = "family-row-actions";
      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.className = "btn btn-ghost btn-sm";
      editButton.textContent = "Uredi";
      editButton.dataset.recordDialog = "family-member-dialog";
      editButton.dataset.revealSubmitLabel = "Spremi člana";
      editButton.dataset.fillGivenName = member.givenName || "";
      editButton.dataset.fillSurname = member.surname || "";
      editButton.dataset.fillRelation = member.relation || "";
      editButton.dataset.fillBirthDate = member.birthDate || "";
      editButton.dataset.fillNotes = member.notes || "";
      editButton.dataset.fillMemberId = member.id || "";
      actionCell.append(editButton);
      if (member.id) {
        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "btn btn-ghost btn-sm";
        deleteButton.textContent = "Obriši";
        deleteButton.dataset.familyDeleteMember = member.id;
        deleteButton.dataset.familyDeleteLabel = [member.givenName || member.name || "", member.surname || ""]
          .filter(Boolean)
          .join(" ");
        actionCell.append(deleteButton);
      }
      row.append(givenCell, surnameCell, relationCell, birthCell, notesCell, actionCell);
      tableBody.append(row);
    });
  }

  function paintContributionTotals(totals) {
    const stats = dialog.querySelector("[data-family-contribution-stats]");
    if (!stats) return;
    if (window.familyFinanceStats) {
      window.familyFinanceStats.paint(stats, totals || {});
      return;
    }
    const grandTotal = totals && Number(totals.grandTotal);
    stats.hidden = !(grandTotal > 0);
    setText("[data-family-totals-grand]", formatMoney(grandTotal || 0));
  }

  function paintContributions(contributions, totals) {
    setText("[data-family-contribution-count]", String(contributions.length));
    paintContributionTotals(totals);
    const tableBody = dialog.querySelector("[data-family-contributions]");
    if (!tableBody) return;
    tableBody.replaceChildren();
    if (!contributions.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 5;
      cell.className = "empty-state";
      cell.textContent = "Nema financijskih zapisa.";
      row.append(cell);
      tableBody.append(row);
      return;
    }
    contributions.forEach((contribution) => {
      const row = document.createElement("tr");
      const yearCell = document.createElement("td");
      yearCell.textContent = String(contribution.year);
      const categoryCell = document.createElement("td");
      categoryCell.textContent = contribution.categoryLabel || "Lukno";
      const amountCell = document.createElement("td");
      amountCell.textContent = formatMoney(contribution.luknoAmount);
      const dateCell = document.createElement("td");
      dateCell.textContent = formatDate(contribution.luknoPaidAt) || "—";
      const actionCell = document.createElement("td");
      actionCell.className = "family-row-actions";
      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.className = "btn btn-ghost btn-sm";
      editButton.textContent = "Uredi";
      editButton.dataset.recordDialog = "family-contribution-dialog";
      editButton.dataset.revealSubmitLabel = "Spremi uplatu";
      editButton.dataset.fillContributionId = contribution.id || "";
      editButton.dataset.fillYear = String(contribution.year);
      editButton.dataset.fillCategory = contribution.category || "lukno";
      editButton.dataset.fillAmount = String(contribution.luknoAmount);
      editButton.dataset.fillPaidAt = contribution.luknoPaidAt || "";
      editButton.dataset.fillNotes = contribution.notes || "";
      actionCell.append(editButton);
      if (contribution.id) {
        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "btn btn-ghost btn-sm";
        deleteButton.textContent = "Obriši";
        deleteButton.dataset.familyDeleteContribution = contribution.id;
        deleteButton.dataset.familyDeleteLabel =
          String(contribution.year) + " · " + (contribution.categoryLabel || "Lukno");
        actionCell.append(deleteButton);
      }
      row.append(yearCell, categoryCell, amountCell, dateCell, actionCell);
      tableBody.append(row);
    });
  }

  function setStatusPills(root, status) {
    const toggle = root && root.querySelector("[data-family-status-toggle]");
    if (!toggle) return;
    const normalized = status === "neaktivna" ? "neaktivna" : "aktivna";
    const valueField = toggle.querySelector("[data-status-value]");
    if (valueField) valueField.value = normalized;
    toggle.querySelectorAll("[data-status-option]").forEach((pill) => {
      const selected = pill.dataset.statusOption === normalized;
      pill.classList.toggle("is-selected", selected);
      pill.classList.toggle("is-active", selected && normalized === "aktivna");
      pill.classList.toggle("is-inactive", selected && normalized === "neaktivna");
    });
  }

  function paintStatusToggle(status, surname) {
    const button = dialog.querySelector("[data-family-toggle-status]");
    if (!button) return;
    const normalized = status === "neaktivna" ? "neaktivna" : "aktivna";
    button.dataset.familyStatus = normalized;
    button.dataset.familyToggleLabel = surname ? "Obitelj " + surname : "ovu obitelj";
    button.textContent =
      normalized === "neaktivna" ? "Aktiviraj obitelj" : "Deaktiviraj obitelj";
    setStatusPills(dialog.querySelector("#family-basics-form"), normalized);
  }

  function paintNotes(notes) {
    const container = dialog.querySelector("[data-family-notes]");
    if (!container) return;
    container.replaceChildren();
    if (notes) {
      const aside = document.createElement("aside");
      aside.className = "pastoral-note";
      const paragraph = document.createElement("p");
      paragraph.textContent = notes;
      aside.append(paragraph);
      container.append(aside);
      return;
    }
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Nema upisane pastoralne bilješke.";
    container.append(empty);
  }

  function eventToneClass(eventType) {
    if (eventType === "left") return "case-event--message";
    if (eventType === "relation_changed") return "case-event--completed";
    return "case-event--joined";
  }

  function paintMembershipTimeline(events) {
    const list = dialog.querySelector("[data-family-membership-timeline]");
    if (!list) return;
    list.replaceChildren();
    if (!events || !events.length) {
      const item = document.createElement("li");
      item.className = "family-history-empty";
      const dot = document.createElement("span");
      dot.className = "case-event-dot";
      dot.setAttribute("aria-hidden", "true");
      const body = document.createElement("div");
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Još nema zabilježenih promjena članstva.";
      body.append(empty);
      item.append(dot, body);
      list.append(item);
      return;
    }
    events.forEach((event) => {
      const item = document.createElement("li");
      item.className = eventToneClass(event.type);
      const dot = document.createElement("span");
      dot.className = "case-event-dot";
      dot.setAttribute("aria-hidden", "true");
      const body = document.createElement("div");
      const headline = document.createElement("span");
      const title = document.createElement("strong");
      title.textContent = event.label || "";
      headline.append(title);
      if (event.at) {
        const time = document.createElement("time");
        time.dateTime = event.at;
        time.textContent = formatDate(event.at);
        headline.append(time);
      }
      const detail = document.createElement("p");
      const parts = [event.name || ""];
      if (event.detail) parts.push(event.detail);
      detail.textContent = parts.filter(Boolean).join(" · ");
      body.append(headline, detail);
      item.append(dot, body);
      list.append(item);
    });
  }

  function paintCard(card, form) {
    setFamilyIdFields(card.id || "");
    paintSummary(card);
    paintMembers(card.members || []);
    paintContributions(card.contributions || [], card.contributionTotals || {});
    paintMembershipTimeline(card.membershipTimeline || []);
    paintNotes(card.pastoralNotes || "");
    paintStatusToggle(card.status || "aktivna", card.surname || "");
    const deleteButton = dialog.querySelector("[data-family-delete-family]");
    if (deleteButton) {
      deleteButton.dataset.familyDeleteLabel = card.surname
        ? "Obitelj " + card.surname
        : "ovu obitelj";
    }
    if (!form) return;
    if (form.id === "family-basics-form") {
      const values = {
        surname: card.surname,
        address: card.address,
        phone: card.phone,
        email: card.email,
      };
      Object.entries(values).forEach(([name, value]) => {
        const field = form.elements[name];
        if (field) field.value = value || "";
      });
      setStatusPills(form, card.status || "aktivna");
      if (window.familyStreetPicker) {
        window.familyStreetPicker.setStreet(form, card.streetId || "", card.streetName || "");
      } else {
        const streetIdField = form.querySelector("[data-street-id]");
        const streetSearch = form.querySelector("[data-street-search]");
        if (streetIdField) streetIdField.value = card.streetId || "";
        if (streetSearch) streetSearch.value = card.streetName || "";
      }
    }
    if (form.id === "family-notes-form") {
      const notesField = form.elements.pastoral_notes;
      if (notesField) {
        notesField.value = card.pastoralNotes || "";
        notesField.defaultValue = card.pastoralNotes || "";
      }
    }
  }

  function payloadFromForm(form) {
    const payload = {};
    [...form.elements].forEach((field) => {
      if (!field.name || field.disabled) return;
      if (field.name === "csrfmiddlewaretoken" || field.name === "action" || field.name === "family_id") return;
      if (field.type === "checkbox") {
        payload[field.name] = field.checked;
        return;
      }
      if (field.type === "date") {
        payload[field.name] = field.value || null;
        return;
      }
      if (field.type === "number") {
        payload[field.name] = field.value === "" ? null : Number(field.value);
        return;
      }
      payload[field.name] = field.value;
    });
    return payload;
  }

  function closeSavedForm(form) {
    clearErrors(form);
    const nestedDialog = form.closest(
      "#family-contribution-dialog, #family-member-dialog"
    );
    if (nestedDialog) {
      form.reset();
      const contributionId = form.querySelector('[name="contribution_id"]');
      if (contributionId) contributionId.value = "";
      const memberId = form.querySelector('[name="member_id"]');
      if (memberId) memberId.value = "";
      if (typeof nestedDialog.close === "function") nestedDialog.close();
      else nestedDialog.removeAttribute("open");
      return;
    }
    if (!form.classList.contains("family-reveal-form")) return;
    form.hidden = true;
    form.reset();
    const memberId = form.querySelector('[name="member_id"]');
    if (memberId) memberId.value = "";
  }

  async function submitFamilyForm(form) {
    const actionInput = form.querySelector("[name='action']");
    const familyInput = form.querySelector("[name='family_id']");
    const actionName = actionInput ? actionInput.value : "";
    const endpoint = ENDPOINTS[actionName];
    const familyId = familyInput ? familyInput.value : "";
    if (!endpoint || !familyId) return;
    const submitButtons = [...form.querySelectorAll("[type='submit']")];
    submitButtons.forEach((button) => {
      button.disabled = true;
    });
    clearErrors(form);
    showStatus("", "");
    try {
      const route = endpoint(encodeURIComponent(familyId));
      const response = await fetch(route.url, {
        method: route.method,
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify(payloadFromForm(form)),
      });
      if (response.status === 401 || response.status === 403) {
        window.location.reload();
        return;
      }
      const body = await response.json().catch(() => ({}));
      if (response.status === 422 || body.error === "invalid") {
        showErrors(form, body.fields);
        const formMessages = (body.fields && body.fields.__all__) || [];
        showStatus(formMessages.join(" ") || "Provjerite unos.", "error");
        return;
      }
      if (!response.ok || body.ok === false || !body.card) {
        showStatus("Spremanje nije uspjelo. Pokušajte ponovno.", "error");
        return;
      }
      paintCard(body.card, form);
      closeSavedForm(form);
      showStatus(body.message || "Spremljeno.", "ok");
    } catch (error) {
      showStatus("Spremanje nije uspjelo. Pokušajte ponovno.", "error");
    } finally {
      submitButtons.forEach((button) => {
        button.disabled = false;
      });
    }
  }

  function onFamilyFormSubmit(event) {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.hasAttribute("data-family-form")) return;
    const actionInput = form.querySelector("[name='action']");
    const actionName = actionInput ? actionInput.value : "";
    if (!ENDPOINTS[actionName]) return;
    event.preventDefault();
    submitFamilyForm(form);
  }

  async function requestDelete(route, { expectCard }) {
    try {
      const response = await fetch(route.url, {
        method: route.method,
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
      });
      if (response.status === 401 || response.status === 403) {
        window.location.reload();
        return null;
      }
      const body = await response.json().catch(() => ({}));
      if (!response.ok || body.ok === false) {
        await swalAlert(
          "Brisanje nije uspjelo",
          body.message || body.error || body.detail || "Pokušajte ponovno.",
          "error",
        );
        return null;
      }
      if (expectCard && !body.card) {
        await swalAlert("Brisanje nije uspjelo", "Pokušajte ponovno.", "error");
        return null;
      }
      return body;
    } catch (error) {
      await swalAlert("Brisanje nije uspjelo", "Pokušajte ponovno.", "error");
      return null;
    }
  }

  dialog.addEventListener("click", async (event) => {
    const memberDelete = event.target.closest("[data-family-delete-member]");
    if (memberDelete) {
      const memberId = memberDelete.dataset.familyDeleteMember;
      const label = (memberDelete.dataset.familyDeleteLabel || "ovog člana").trim();
      if (!memberId) return;
      const confirmed = await swalConfirm(
        "Ukloniti člana?",
        "Ukloniti " + label + " iz obitelji?",
      );
      if (!confirmed) return;
      const familyId = currentFamilyId();
      if (!familyId) return;
      const body = await requestDelete(
        ENDPOINTS.delete_family_member(encodeURIComponent(familyId), memberId),
        { expectCard: true },
      );
      if (!body) return;
      paintCard(body.card, dialog.querySelector("#family-basics-form") || dialog.querySelector("[data-family-form]"));
      await swalAlert("Obrisano", body.message || "Član obitelji je uklonjen.", "success");
      return;
    }

    const contributionDelete = event.target.closest("[data-family-delete-contribution]");
    if (contributionDelete) {
      const contributionId = contributionDelete.dataset.familyDeleteContribution;
      const label = (contributionDelete.dataset.familyDeleteLabel || "ovu uplatu").trim();
      if (!contributionId) return;
      const confirmed = await swalConfirm(
        "Obrisati uplatu?",
        "Obrisati " + label + "?",
      );
      if (!confirmed) return;
      const familyId = currentFamilyId();
      if (!familyId) return;
      const body = await requestDelete(
        ENDPOINTS.delete_family_contribution(encodeURIComponent(familyId), contributionId),
        { expectCard: true },
      );
      if (!body) return;
      paintCard(body.card, dialog.querySelector("#family-basics-form") || dialog.querySelector("[data-family-form]"));
      await swalAlert("Obrisano", body.message || "Uplata je obrisana.", "success");
      return;
    }

    const familyDelete = event.target.closest("[data-family-delete-family]");
    if (familyDelete) {
      const label = (familyDelete.dataset.familyDeleteLabel || "ovu obitelj").trim();
      const confirmed = await swalConfirm(
        "Obrisati krivi unos?",
        "Obrisati " + label + "? Koristite samo za potpuno krivi ili dvostruki karton. Ako su se odselili ili više nisu u skrbi, umjesto toga deaktivirajte obitelj.",
      );
      if (!confirmed) return;
      const familyId = currentFamilyId();
      if (!familyId) return;
      const body = await requestDelete(
        ENDPOINTS.delete_family(encodeURIComponent(familyId)),
        { expectCard: false },
      );
      if (!body) return;
      await swalAlert("Obrisano", body.message || "Obitelj je obrisana.", "success");
      window.location.href = window.location.pathname;
      return;
    }

    const statusToggle = event.target.closest("[data-family-toggle-status]");
    if (statusToggle) {
      const familyId = currentFamilyId();
      const basicsForm = dialog.querySelector("#family-basics-form");
      if (!familyId || !basicsForm) return;
      const currentStatus =
        statusToggle.dataset.familyStatus === "neaktivna" ? "neaktivna" : "aktivna";
      const nextStatus = currentStatus === "neaktivna" ? "aktivna" : "neaktivna";
      const label = (statusToggle.dataset.familyToggleLabel || "ovu obitelj").trim();
      const confirmed = await swalConfirm(
        nextStatus === "neaktivna" ? "Deaktivirati obitelj?" : "Aktivirati obitelj?",
        nextStatus === "neaktivna"
          ? "Deaktivirati " + label + "? Karton ostaje u evidenciji (npr. odselili se). To je uobičajeni korak umjesto brisanja."
          : "Ponovno aktivirati " + label + "?",
        nextStatus === "neaktivna" ? "Deaktiviraj" : "Aktiviraj",
      );
      if (!confirmed) return;
      const payload = payloadFromForm(basicsForm);
      payload.status = nextStatus;
      try {
        const response = await fetch("/api/families/" + encodeURIComponent(familyId) + "/", {
          method: "PATCH",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify(payload),
        });
        if (response.status === 401 || response.status === 403) {
          window.location.reload();
          return;
        }
        const body = await response.json().catch(() => ({}));
        if (!response.ok || body.ok === false || !body.card) {
          await swalAlert(
            "Spremanje nije uspjelo",
            body.message || body.error || "Pokušajte ponovno.",
            "error",
          );
          return;
        }
        paintCard(body.card, basicsForm);
        await swalAlert(
          nextStatus === "neaktivna" ? "Deaktivirano" : "Aktivirano",
          nextStatus === "neaktivna"
            ? "Obitelj je označena kao neaktivna."
            : "Obitelj je ponovno aktivna.",
          "success",
        );
      } catch (error) {
        await swalAlert("Spremanje nije uspjelo", "Pokušajte ponovno.", "error");
      }
    }
  });

  async function openFamilyCard(familyId) {
    if (!familyId) return;
    showStatus("", "");
    try {
      const route = ENDPOINTS.get_family(encodeURIComponent(familyId));
      const response = await fetch(route.url, {
        method: route.method,
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrfToken() },
      });
      if (response.status === 401 || response.status === 403) {
        window.location.reload();
        return;
      }
      const body = await response.json().catch(() => ({}));
      if (!response.ok || body.ok === false || !body.card) {
        await swalAlert(
          "Karton nije učitan",
          body.message || body.error || "Pokušajte ponovno.",
          "error",
        );
        return;
      }
      const basicsForm = dialog.querySelector("#family-basics-form");
      paintCard(body.card, basicsForm);
      if (window.showFamilyWizardTab) {
        window.showFamilyWizardTab(dialog, "osnovno");
      }
      setFamilyHash(body.card.id || familyId);
      openDialog();
    } catch (error) {
      await swalAlert("Karton nije učitan", "Pokušajte ponovno.", "error");
    }
  }

  document.addEventListener("click", (event) => {
    const openTrigger = event.target.closest("[data-family-open]");
    if (!openTrigger) return;
    event.preventDefault();
    openFamilyCard(openTrigger.dataset.familyOpen || "");
  });

  dialog.addEventListener("close", () => {
    setFamilyHash("");
  });

  const hashFamilyId = familyIdFromHash();
  if (hashFamilyId) openFamilyCard(hashFamilyId);

  dialog.addEventListener("submit", onFamilyFormSubmit);
  ["family-contribution-dialog", "family-member-dialog"].forEach((dialogId) => {
    const nestedDialog = document.getElementById(dialogId);
    if (nestedDialog) nestedDialog.addEventListener("submit", onFamilyFormSubmit);
  });

  window.openFamilyCard = openFamilyCard;
})();

(function () {
  "use strict";

  document.addEventListener("click", (event) => {
    const option = event.target.closest("[data-status-option]");
    if (!option) return;
    const toggle = option.closest("[data-family-status-toggle]");
    if (!toggle) return;
    event.preventDefault();
    const status = option.dataset.statusOption === "neaktivna" ? "neaktivna" : "aktivna";
    const valueField = toggle.querySelector("[data-status-value]");
    if (valueField) valueField.value = status;
    toggle.querySelectorAll("[data-status-option]").forEach((pill) => {
      const selected = pill.dataset.statusOption === status;
      pill.classList.toggle("is-selected", selected);
      pill.classList.toggle("is-active", selected && status === "aktivna");
      pill.classList.toggle("is-inactive", selected && status === "neaktivna");
    });
  });
})();
