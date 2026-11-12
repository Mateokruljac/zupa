(function () {
  "use strict";

  const dirtyForms = new Set();

  function activateTab(tabset, button, focus = false) {
    const buttons = Array.from(tabset.querySelectorAll('[role="tab"]'));
    const panels = Array.from(tabset.querySelectorAll('[data-tab-panel]'));
    const targetId = button.dataset.tabTarget;

    buttons.forEach((candidate) => {
      const active = candidate === button;
      candidate.setAttribute("aria-selected", String(active));
      candidate.tabIndex = active ? 0 : -1;
    });
    panels.forEach((panel) => {
      panel.hidden = panel.id !== targetId;
    });
    if (focus) button.focus();
  }

  function moveTab(tabset, offset) {
    const buttons = Array.from(tabset.querySelectorAll('[role="tab"]'));
    const currentIndex = buttons.findIndex(
      (button) => button.getAttribute("aria-selected") === "true"
    );
    const nextIndex = (currentIndex + offset + buttons.length) % buttons.length;
    activateTab(tabset, buttons[nextIndex], true);
  }

  function markValidationErrors(tabset) {
    let firstInvalidButton = null;
    tabset.querySelectorAll('[data-tab-panel]').forEach((panel) => {
      const button = tabset.querySelector(`[data-tab-target="${panel.id}"]`);
      const hasErrors = Boolean(panel.querySelector(".errorlist"));
      button?.classList.toggle("has-errors", hasErrors);
      const badge = button?.querySelector(".baptism-registry-tabs__error");
      if (badge) badge.hidden = !hasErrors;
      if (hasErrors && !firstInvalidButton) firstInvalidButton = button;
    });
    if (firstInvalidButton) activateTab(tabset, firstInvalidButton);
  }

  function initializeTabset(tabset) {
    const buttons = Array.from(tabset.querySelectorAll('[role="tab"]'));
    if (!buttons.length) return;

    buttons.forEach((button) => {
      button.addEventListener("click", () => activateTab(tabset, button));
      button.addEventListener("keydown", (event) => {
        if (event.key === "ArrowRight") moveTab(tabset, 1);
        else if (event.key === "ArrowLeft") moveTab(tabset, -1);
        else if (event.key === "Home") activateTab(tabset, buttons[0], true);
        else if (event.key === "End") activateTab(tabset, buttons.at(-1), true);
        else return;
        event.preventDefault();
      });
    });

    tabset.querySelectorAll("[data-tab-next]").forEach((button) => {
      button.addEventListener("click", () => moveTab(tabset, 1));
    });
    tabset.querySelectorAll("[data-tab-previous]").forEach((button) => {
      button.addEventListener("click", () => moveTab(tabset, -1));
    });

    const form = tabset.closest("form");
    if (form) {
      const markDirty = () => dirtyForms.add(form);
      form.addEventListener("input", markDirty);
      form.addEventListener("change", markDirty);
      form.addEventListener("submit", () => dirtyForms.delete(form));
      form.addEventListener(
        "invalid",
        (event) => {
          const panel = event.target.closest("[data-tab-panel]");
          if (!panel || !tabset.contains(panel)) return;
          const button = tabset.querySelector(`[data-tab-target="${panel.id}"]`);
          if (button) {
            button.classList.add("has-errors");
            const badge = button.querySelector(".baptism-registry-tabs__error");
            if (badge) badge.hidden = false;
            activateTab(tabset, button);
          }
        },
        true
      );
    }

    markValidationErrors(tabset);
  }

  document.querySelectorAll("[data-registry-tabs]").forEach(initializeTabset);

  window.addEventListener("beforeunload", (event) => {
    if (!dirtyForms.size) return;
    event.preventDefault();
    event.returnValue = "";
  });
})();
