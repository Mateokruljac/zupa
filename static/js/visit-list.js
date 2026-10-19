(function () {
  "use strict";

  const dialog = document.getElementById("visit-record-dialog");

  function swalConfirm(title, text, confirmButtonText) {
    if (!window.Swal) return Promise.resolve(window.confirm(text || title));
    return window.Swal.fire({
      target: dialog && dialog.open ? dialog : undefined,
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

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest("[data-visit-delete-form]");
    if (!form) return;
    event.preventDefault();
    const label = (form.dataset.visitDeleteLabel || "ovaj posjet").trim();
    const confirmed = await swalConfirm(
      "Obrisati posjet?",
      "Obrisati posjet za " + label + "? Ova radnja se ne može poništiti.",
      "Obriši",
    );
    if (!confirmed) return;
    form.submit();
  });
})();
