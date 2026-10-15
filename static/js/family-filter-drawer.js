(function () {
  "use strict";

  const drawer = document.getElementById("family-filter-drawer");
  const openButton = document.querySelector("[data-family-filters-open]");
  if (!drawer || !openButton) return;

  const shell = document.querySelector(".app-shell");
  if (shell) shell.appendChild(drawer);

  const streetFilter = drawer.querySelector("[data-family-street-filter]");
  const searchInput = streetFilter?.querySelector("[data-filter-street-search]");
  const streetIdInput = streetFilter?.querySelector("[data-filter-street-id]");
  const suggestionList = streetFilter?.querySelector("[data-filter-street-list]");
  const optionsElement = document.getElementById("family-street-options");
  const streets = optionsElement ? JSON.parse(optionsElement.textContent) : [];

  const panel = drawer.querySelector(".family-filter-drawer__panel");

  function setOpen(isOpen) {
    drawer.classList.toggle("is-open", isOpen);
    document.body.classList.toggle("family-filters-open", isOpen);
    drawer.setAttribute("aria-hidden", isOpen ? "false" : "true");
    openButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
    if (isOpen) panel?.focus();
  }

  openButton.addEventListener("click", () => setOpen(true));
  drawer.querySelectorAll("[data-family-filters-close]").forEach((button) => {
    button.addEventListener("click", () => setOpen(false));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer.classList.contains("is-open")) setOpen(false);
  });

  if (!searchInput || !streetIdInput || !suggestionList) return;

  function streetLabel(street) {
    const streetName = street.name || "";
    return street.city ? streetName + " (" + street.city + ")" : streetName;
  }

  function matchingStreets(query) {
    const normalizedQuery = query.trim().toLocaleLowerCase("hr");
    if (!normalizedQuery) return streets.slice();
    return streets.filter((street) =>
      streetLabel(street).toLocaleLowerCase("hr").includes(normalizedQuery)
    );
  }

  function selectStreet(street) {
    streetIdInput.value = street ? street.id : "";
    searchInput.value = street ? street.name || "" : "";
    suggestionList.hidden = true;
  }

  function renderSuggestions() {
    suggestionList.replaceChildren();
    const clearItem = document.createElement("li");
    const clearButton = document.createElement("button");
    clearButton.type = "button";
    clearButton.textContent = "Sve ulice";
    clearButton.addEventListener("click", () => selectStreet(null));
    clearItem.append(clearButton);
    suggestionList.append(clearItem);

    matchingStreets(searchInput.value).forEach((street) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = streetLabel(street);
      button.addEventListener("click", () => selectStreet(street));
      item.append(button);
      suggestionList.append(item);
    });
    suggestionList.hidden = false;
  }

  searchInput.addEventListener("focus", renderSuggestions);
  searchInput.addEventListener("input", () => {
    streetIdInput.value = "";
    renderSuggestions();
  });
  searchInput.addEventListener("blur", () => {
    window.setTimeout(() => {
      if (suggestionList.contains(document.activeElement)) return;
      const typedName = searchInput.value.trim().toLocaleLowerCase("hr");
      if (!typedName) {
        selectStreet(null);
        return;
      }
      const exactMatch = streets.find(
        (street) => (street.name || "").trim().toLocaleLowerCase("hr") === typedName
      );
      if (exactMatch) selectStreet(exactMatch);
    }, 180);
  });
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !suggestionList.hidden) {
      suggestionList.hidden = true;
      event.stopPropagation();
    }
  });
  document.addEventListener("click", (event) => {
    if (!streetFilter.contains(event.target)) suggestionList.hidden = true;
  });
})();
