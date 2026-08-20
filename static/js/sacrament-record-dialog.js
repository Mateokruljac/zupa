(function () {
  function openSacramentRecordDialog(dialogIdentifier) {
    const dialog = document.getElementById(dialogIdentifier);
    if (!dialog) return;

    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.setAttribute("open", "");
    }

    dialog.querySelector("input:not([type='hidden'])")?.focus();
  }

  function closeSacramentRecordDialog(dialog) {
    if (!dialog) return;
    if (typeof dialog.close === "function") {
      dialog.close();
    } else {
      dialog.removeAttribute("open");
    }
  }

  document.querySelectorAll("[data-sacrament-dialog]").forEach((trigger) => {
    const openDialog = () => openSacramentRecordDialog(trigger.dataset.sacramentDialog);

    trigger.addEventListener("click", openDialog);
    trigger.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openDialog();
    });
  });

  document.querySelectorAll(".sacrament-record-dialog").forEach((dialog) => {
    dialog.querySelectorAll("[data-sacrament-dialog-close]").forEach((button) => {
      button.addEventListener("click", () => closeSacramentRecordDialog(dialog));
    });

    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeSacramentRecordDialog(dialog);
    });
  });

  document.querySelectorAll("[data-confirm-delete]").forEach((deleteForm) => {
    deleteForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const recordLabel = deleteForm.dataset.recordLabel || "ovaj zapis";

      if (window.PastoralModal?.confirm) {
        window.PastoralModal.confirm({
          title: "Obrisati zapis?",
          message: `Trajno će se obrisati ${recordLabel}. Ovu radnju nije moguće poništiti.`,
          danger: true,
          confirmLabel: "Obriši",
          onConfirm: () => deleteForm.submit(),
        });
        return;
      }

      if (window.confirm(`Trajno obrisati ${recordLabel}?`)) {
        deleteForm.submit();
      }
    });
  });
})();
