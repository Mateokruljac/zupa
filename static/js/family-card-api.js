(function () {
  "use strict";

  const dialog = document.getElementById("family-detail-dialog");
  if (!dialog) return;

  const MONTHS = ["sij", "velj", "ožu", "tra", "svi", "lip", "srp", "kol", "ruj", "lis", "stu", "pro"];
  const ENDPOINTS = {
    update_family: (familyId) => ({ method: "PATCH", url: "/api/families/" + familyId + "/" }),
    save_family_member: (familyId) => ({ method: "PUT", url: "/api/families/" + familyId + "/members/" }),
    save_family_contribution: (familyId) => ({ method: "PUT", url: "/api/families/" + familyId + "/contributions/" }),
    update_family_notes: (familyId) => ({ method: "PATCH", url: "/api/families/" + familyId + "/notes/" }),
  };

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
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
      cell.colSpan = 5;
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
      const actionCell = document.createElement("td");
      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.className = "btn btn-ghost btn-sm";
      editButton.textContent = "Uredi";
      editButton.dataset.reveal = "family-member-form";
      editButton.dataset.revealSubmitLabel = "Spremi člana";
      editButton.dataset.fillGivenName = member.givenName || "";
      editButton.dataset.fillSurname = member.surname || "";
      editButton.dataset.fillRelation = member.relation || "";
      editButton.dataset.fillBirthDate = member.birthDate || "";
      editButton.dataset.fillMemberId = member.id || "";
      actionCell.append(editButton);
      row.append(givenCell, surnameCell, relationCell, birthCell, actionCell);
      tableBody.append(row);
    });
  }

  function paintContributions(contributions) {
    setText("[data-family-contribution-count]", String(contributions.length));
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
      const luknoCell = document.createElement("td");
      appendAmount(luknoCell, contribution.luknoAmount, contribution.luknoPaidAt);
      const donationCell = document.createElement("td");
      appendAmount(donationCell, contribution.churchDonation, contribution.donationDate);
      const statusCell = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = contribution.luknoPaid ? "badge badge-done" : "badge badge-urgent";
      badge.textContent = contribution.luknoPaid ? "plaćeno" : "nije plaćeno";
      statusCell.append(badge);
      const actionCell = document.createElement("td");
      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.className = "btn btn-ghost btn-sm";
      editButton.textContent = "Uredi";
      editButton.dataset.reveal = "family-contribution-form";
      editButton.dataset.revealSubmitLabel = "Spremi lukno / dar";
      editButton.dataset.fillYear = String(contribution.year);
      editButton.dataset.fillLuknoAmount = String(contribution.luknoAmount);
      editButton.dataset.fillLuknoPaid = contribution.luknoPaid ? "1" : "";
      editButton.dataset.fillLuknoPaidAt = contribution.luknoPaidAt || "";
      editButton.dataset.fillChurchDonation = String(contribution.churchDonation);
      editButton.dataset.fillDonationDate = contribution.donationDate || "";
      editButton.dataset.fillNotes = contribution.notes || "";
      actionCell.append(editButton);
      row.append(yearCell, luknoCell, donationCell, statusCell, actionCell);
      tableBody.append(row);
    });
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

  function paintCard(card, form) {
    paintSummary(card);
    paintMembers(card.members || []);
    paintContributions(card.contributions || []);
    paintNotes(card.pastoralNotes || "");
    if (form.id === "family-basics-form") {
      const values = {
        surname: card.surname,
        status: card.status,
        street_id: card.streetId,
        address: card.address,
        phone: card.phone,
        email: card.email,
      };
      Object.entries(values).forEach(([name, value]) => {
        const field = form.elements[name];
        if (field) field.value = value || "";
      });
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
    if (!form.classList.contains("family-reveal-form")) return;
    form.hidden = true;
    form.reset();
    const memberId = form.querySelector('[name="member_id"]');
    if (memberId) memberId.value = "";
  }

  dialog.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.hasAttribute("data-family-form")) return;
    const actionInput = form.querySelector("[name='action']");
    const familyInput = form.querySelector("[name='family_id']");
    const actionName = actionInput ? actionInput.value : "";
    const endpoint = ENDPOINTS[actionName];
    const familyId = familyInput ? familyInput.value : "";
    if (!endpoint || !familyId) return;
    event.preventDefault();
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
  });
})();
