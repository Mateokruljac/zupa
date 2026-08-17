(function () {
  "use strict";

  const dialogs = {
    office: document.getElementById("ops-office-dialog"),
    facility: document.getElementById("ops-facility-dialog"),
    communication: document.getElementById("ops-communication-dialog"),
  };

  function openDialog(name) {
    const dialog = dialogs[name];
    if (!dialog) return;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
    const first = dialog.querySelector("input:not([type='hidden']), select, textarea");
    window.setTimeout(() => first?.focus(), 50);
  }

  function closeDialog(dialog) {
    if (!dialog) return;
    if (typeof dialog.close === "function") dialog.close();
    else dialog.removeAttribute("open");
  }

  document.querySelectorAll("[data-ops-dialog]").forEach((trigger) => {
    trigger.addEventListener("click", () => openDialog(trigger.dataset.opsDialog));
  });

  document.querySelectorAll("[data-ops-close]").forEach((trigger) => {
    trigger.addEventListener("click", () => closeDialog(trigger.closest("dialog")));
  });

  Object.values(dialogs).forEach((dialog) => {
    if (!dialog) return;
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeDialog(dialog);
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    Object.values(dialogs).forEach((dialog) => {
      if (dialog?.open) closeDialog(dialog);
    });
  });
})();
