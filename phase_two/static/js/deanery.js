/** Interakcije faze 2 za međužupnu suradnju. */
(function (global) {
  "use strict";

  const PRESETS = {
    marriage_certificate: {
      days: 3,
      subject: "Krsni list i potvrda slobodnog stanja za ženidbu",
      description: "Molimo provjeru matičnog upisa i izdavanje novijeg izvatka s potrebnim bilješkama za ženidbeni postupak.",
    },
    baptism_certificate: {
      days: 3,
      subject: "Potvrda krštenja",
      description: "Molimo izdavanje novijeg izvatka iz matice krštenih s pripadajućim bilješkama.",
    },
    marriage_delegation: {
      days: 4,
      subject: "Delegacija za slavlje ženidbe",
      description: "Molimo provjeru nadležnosti i izdavanje potrebne delegacije za asistiranje ženidbi.",
    },
    priest_substitution: {
      days: 1,
      subject: "Zamjena svećenika za misno slavlje",
      description: "Molimo odgovor o mogućnosti zamjene. Termin, lokacija i pastoralne okolnosti navedeni su u predmetu.",
    },
    mass_intention_transfer: {
      days: 7,
      subject: "Preuzimanje misnih nakana",
      description: "Molimo potvrdu mogućnosti preuzimanja nakana i evidentiranja pripadajućih stipendija.",
    },
    sacrament_record_check: {
      days: 5,
      subject: "Provjera sakramentalnog zapisa",
      description: "Molimo provjeru izvornog upisa i dostavu odgovora bez dijeljenja podataka koji nisu potrebni za ovaj predmet.",
    },
    pastoral_handover: {
      days: 5,
      subject: "Pastoralna primopredaja",
      description: "Molimo sigurnu koordinaciju pastoralne primopredaje i potvrdu odgovorne osobe koja preuzima predmet.",
    },
  };

  function isoAfterDays(days) {
    const value = new Date();
    value.setDate(value.getDate() + days);
    const local = new Date(value.getTime() - value.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
  }

  function init() {
    const dialog = document.getElementById("new-deanery-request");
    if (!dialog) return;
    const typeSelect = dialog.querySelector('[name="request_type"]');
    const subject = dialog.querySelector('[name="subject"]');
    const description = dialog.querySelector('[name="description"]');
    const dueDate = dialog.querySelector('[name="due_date"]');

    function applyPreset(type, force) {
      const preset = PRESETS[type];
      if (!preset) return;
      if (force || !subject.value.trim()) subject.value = preset.subject;
      if (force || !description.value.trim()) description.value = preset.description;
      if (force || !dueDate.value) dueDate.value = isoAfterDays(preset.days);
    }

    function open(type, forcePreset) {
      if (type && typeSelect) typeSelect.value = type;
      applyPreset(typeSelect?.value || type, forcePreset);
      dialog.showModal();
      setTimeout(() => dialog.querySelector("select, input, textarea")?.focus(), 40);
    }

    document.getElementById("open-deanery-request")?.addEventListener("click", () => open(typeSelect?.value, false));
    document.querySelectorAll("[data-request-type]").forEach((button) => {
      button.addEventListener("click", () => open(button.dataset.requestType, true));
    });
    dialog.querySelectorAll("[data-dialog-close]").forEach((button) => {
      button.addEventListener("click", () => dialog.close());
    });
    typeSelect?.addEventListener("change", () => applyPreset(typeSelect.value, true));
    dialog.addEventListener("click", (event) => {
      const rect = dialog.getBoundingClientRect();
      const outside = event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
      if (outside) dialog.close();
    });

    global.DeaneryUi = { openRequest: (type) => open(type, true) };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})(typeof window !== "undefined" ? window : this);
