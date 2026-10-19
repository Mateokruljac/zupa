(function () {
  "use strict";

  const dialog = document.getElementById("street-detail-dialog");

  function swalConfirm(title, text, confirmButtonText) {
    if (!window.Swal) return Promise.resolve(window.confirm(text || title));
    return window.Swal.fire({
      target: dialog || undefined,
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
    const form = event.target.closest("[data-street-delete-form]");
    if (!form) return;
    event.preventDefault();
    const label = (form.dataset.streetDeleteLabel || "ovu ulicu").trim();
    const confirmed = await swalConfirm(
      "Obrisati ulicu?",
      "Obrisati ulicu " + label + "? Ako na njoj ima obitelji, prvo ih premjestite ili odspojite.",
      "Obriši",
    );
    if (!confirmed) return;
    form.submit();
  });
})();
