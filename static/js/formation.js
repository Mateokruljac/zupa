(function () {
  document.querySelectorAll("[data-formation-year-form]").forEach((yearForm) => {
    yearForm.addEventListener("submit", () => {
      const yearInput = yearForm.querySelector("[name='year']");
      if (!yearInput?.value) return;

      const destination = new URL(window.location.href);
      destination.search = "";
      destination.searchParams.set("year", yearInput.value);
      yearForm.action = destination.toString();
    });
  });
})();
