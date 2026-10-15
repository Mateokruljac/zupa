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

  document.querySelectorAll("[data-record-dialog-open]").forEach(openRecordDialog);

  document.addEventListener("click", (event) => {
    const closeButton = event.target.closest("[data-record-dialog-close]");
    if (closeButton) {
      closeRecordDialog(closeButton.closest("dialog"));
      return;
    }
    const revealTrigger = event.target.closest("[data-reveal]");
    if (revealTrigger) {
      const form = document.getElementById(revealTrigger.dataset.reveal);
      if (!form) return;
      form.hidden = false;
      fillRevealedForm(form, revealTrigger);
      const focusable = form.querySelector("input:not([type='hidden']), select, textarea");
      if (focusable) focusable.focus();
      return;
    }
    const hideTrigger = event.target.closest("[data-reveal-hide]");
    if (hideTrigger) {
      const form = document.getElementById(hideTrigger.dataset.revealHide);
      if (!form) return;
      form.hidden = true;
      if (typeof form.reset === "function") form.reset();
      const memberId = form.querySelector('[name="member_id"]');
      if (memberId) memberId.value = "";
    }
  });

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
      if (field.tagName === "SELECT" && value && ![...field.options].some((option) => option.value === value)) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        field.append(option);
      }
      field.value = value || "";
    });
  }

  function syncFamilyWizardUrl(tabId) {
    const url = new URL(window.location.href);
    url.searchParams.set("tab", tabId);
    url.searchParams.delete("edit");
    window.history.replaceState(null, "", url.pathname + url.search);
    return url.pathname + url.search;
  }

  function showFamilyTab(root, tabId) {
    if (!root) return;
    const panes = [...root.querySelectorAll("[data-family-pane]")];
    const tabs = [...root.querySelectorAll(".family-wizard-tab[data-family-tab]")];
    const order = panes.map((pane) => pane.dataset.familyPane);
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
    const previousButton = root.querySelector("[data-family-wizard='prev']");
    const nextButton = root.querySelector("[data-family-wizard='next']");
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

  document.addEventListener("click", (event) => {
    const tab = event.target.closest(".family-wizard-tab[data-family-tab]");
    if (tab) {
      showFamilyTab(tab.closest("dialog[data-family-wizard]"), tab.dataset.familyTab);
      return;
    }
    const gotoTrigger = event.target.closest("[data-family-goto]");
    if (gotoTrigger) {
      showFamilyTab(gotoTrigger.closest("dialog[data-family-wizard]"), gotoTrigger.dataset.familyGoto);
      return;
    }
    const stepButton = event.target.closest("[data-family-wizard='prev'], [data-family-wizard='next']");
    if (!stepButton) return;
    const root = stepButton.closest("dialog[data-family-wizard]");
    if (!root) return;
    const panes = [...root.querySelectorAll("[data-family-pane]")];
    const currentIndex = panes.findIndex((pane) => !pane.hidden);
    if (currentIndex < 0) return;
    const nextIndex = stepButton.dataset.familyWizard === "prev" ? currentIndex - 1 : currentIndex + 1;
    const nextPane = panes[nextIndex];
    if (nextPane) showFamilyTab(root, nextPane.dataset.familyPane);
  });
})();
