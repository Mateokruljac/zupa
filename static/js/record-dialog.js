(function () {
  "use strict";

  function openRecordDialog(dialog) {
    if (!dialog || dialog.open) return;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  function closeRecordDialog(dialog) {
    if (!dialog) return;
    if (typeof dialog.close === "function") dialog.close();
    else dialog.removeAttribute("open");
  }

  document.querySelectorAll("[data-record-dialog]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      openRecordDialog(document.getElementById(trigger.dataset.recordDialog));
    });
  });

  document.querySelectorAll("[data-record-dialog-root]").forEach((dialog) => {
    dialog.querySelectorAll("[data-record-dialog-close]").forEach((button) => {
      button.addEventListener("click", () => closeRecordDialog(dialog));
    });
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeRecordDialog(dialog);
    });
  });

  document.querySelectorAll("[data-record-dialog-open]").forEach(openRecordDialog);

  function fieldNameFromFillKey(key) {
    return key
      .slice(4)
      .replace(/^[A-Z]/, (character) => character.toLowerCase())
      .replace(/[A-Z]/g, (character) => "_" + character.toLowerCase());
  }

  function fillRevealedForm(form, trigger) {
    const submitButton = form.querySelector("[data-reveal-submit]");
    if (submitButton && trigger.dataset.revealSubmitLabel) {
      submitButton.textContent = trigger.dataset.revealSubmitLabel;
    }
    if (trigger.hasAttribute("data-reveal-reset")) {
      form.reset();
      const memberId = form.querySelector('[name="member_id"]');
      if (memberId) memberId.value = "";
      return;
    }
    Object.entries(trigger.dataset).forEach(([key, value]) => {
      if (!key.startsWith("fill") || key === "fill") return;
      const fieldName = fieldNameFromFillKey(key);
      const field =
        form.querySelector('[data-fill-target="' + fieldName + '"]') ||
        form.elements[fieldName];
      if (!field) return;
      if (field.type === "checkbox") {
        field.checked = value === "1" || value === "true";
        return;
      }
      field.value = value || "";
    });
  }

  document.querySelectorAll("[data-reveal]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const form = document.getElementById(trigger.dataset.reveal);
      if (!form) return;
      form.hidden = false;
      fillRevealedForm(form, trigger);
      const focusable = form.querySelector("input:not([type='hidden']), select, textarea");
      if (focusable) focusable.focus();
    });
  });

  document.querySelectorAll("[data-reveal-hide]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const form = document.getElementById(trigger.dataset.revealHide);
      if (!form) return;
      form.hidden = true;
      if (typeof form.reset === "function") form.reset();
      const memberId = form.querySelector('[name="member_id"]');
      if (memberId) memberId.value = "";
    });
  });

  function syncFamilyWizardUrl(tabId) {
    const url = new URL(window.location.href);
    url.searchParams.set("tab", tabId);
    url.searchParams.delete("edit");
    window.history.replaceState(null, "", url.pathname + url.search);
    return url.pathname + url.search;
  }

  document.querySelectorAll("[data-family-wizard]").forEach((root) => {
    const panes = [...root.querySelectorAll("[data-family-pane]")];
    const tabs = [...root.querySelectorAll(".family-wizard-tab[data-family-tab]")];
    const previousButton = root.querySelector("[data-family-wizard='prev']");
    const nextButton = root.querySelector("[data-family-wizard='next']");
    const order = panes.map((pane) => pane.dataset.familyPane);

    function currentIndex() {
      return panes.findIndex((pane) => !pane.hidden);
    }

    function showTab(tabId) {
      if (!order.includes(tabId)) return;
      panes.forEach((pane) => {
        pane.hidden = pane.dataset.familyPane !== tabId;
      });
      tabs.forEach((tab) => {
        const isActive = tab.dataset.familyTab === tabId;
        tab.classList.toggle("is-active", isActive);
        if (isActive) tab.setAttribute("aria-current", "page");
        else tab.removeAttribute("aria-current");
      });
      const index = order.indexOf(tabId);
      if (previousButton) previousButton.hidden = index <= 0;
      if (nextButton) nextButton.hidden = index >= order.length - 1;
      const action = syncFamilyWizardUrl(tabId);
      root.querySelectorAll("form[data-family-form]").forEach((form) => {
        form.setAttribute("action", action);
      });
      root.querySelectorAll(".family-reveal-form").forEach((form) => {
        const pane = form.closest("[data-family-pane]");
        if (pane && pane.dataset.familyPane === tabId) return;
        form.hidden = true;
      });
    }

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => showTab(tab.dataset.familyTab));
    });
    root.querySelectorAll("[data-family-goto]").forEach((trigger) => {
      trigger.addEventListener("click", () => showTab(trigger.dataset.familyGoto));
    });
    if (previousButton) {
      previousButton.addEventListener("click", () => {
        const index = currentIndex();
        if (index > 0) showTab(order[index - 1]);
      });
    }
    if (nextButton) {
      nextButton.addEventListener("click", () => {
        const index = currentIndex();
        if (index < order.length - 1) showTab(order[index + 1]);
      });
    }
  });
})();
