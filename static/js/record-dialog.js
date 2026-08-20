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
})();
