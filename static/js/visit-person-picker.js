(function () {
  "use strict";

  const optionsElement = document.getElementById("visit-person-options");
  const people = optionsElement ? JSON.parse(optionsElement.textContent) : [];

  function matchingPeople(query) {
    const normalizedQuery = query.trim().toLocaleLowerCase("hr");
    if (!normalizedQuery) return people.slice(0, 40);
    return people
      .filter((person) => {
        const haystack = [person.name, person.detail, person.address]
          .filter(Boolean)
          .join(" ")
          .toLocaleLowerCase("hr");
        return haystack.includes(normalizedQuery);
      })
      .slice(0, 40);
  }

  function initPicker(root) {
    const searchInput = root.querySelector("[data-visit-person-search]");
    const addressInput = root.querySelector("[data-visit-address]");
    const familyIdInput = root.querySelector("[data-visit-family-id]");
    const suggestionList = root.querySelector("[data-visit-person-suggestions]");
    if (!searchInput || !suggestionList) return;

    let selectedName = searchInput.value.trim();

    function setExpanded(isExpanded) {
      searchInput.setAttribute("aria-expanded", isExpanded ? "true" : "false");
      suggestionList.hidden = !isExpanded;
    }

    function selectPerson(person) {
      selectedName = person ? person.name || "" : "";
      searchInput.value = selectedName;
      if (addressInput) addressInput.value = person ? person.address || "" : "";
      if (familyIdInput) familyIdInput.value = person ? person.familyId || "" : "";
      setExpanded(false);
    }

    function clearFamilyLinkIfTyped() {
      if (searchInput.value.trim() === selectedName) return;
      selectedName = "";
      if (familyIdInput) familyIdInput.value = "";
    }

    function renderSuggestions() {
      suggestionList.replaceChildren();
      const matches = matchingPeople(searchInput.value);

      if (!matches.length) {
        const emptyItem = document.createElement("li");
        emptyItem.className = "visit-person-suggestions__empty";
        emptyItem.textContent = searchInput.value.trim()
          ? "Nema podudaranja — možete ostaviti upisano ime."
          : "Nema osoba u kartoteci.";
        suggestionList.append(emptyItem);
        setExpanded(true);
        return;
      }

      matches.forEach((person) => {
        const item = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.setAttribute("role", "option");
        button.innerHTML =
          "<strong></strong>" + (person.detail ? "<small></small>" : "");
        button.querySelector("strong").textContent = person.name || "";
        const detail = button.querySelector("small");
        if (detail) detail.textContent = person.detail;
        button.addEventListener("click", () => selectPerson(person));
        item.append(button);
        suggestionList.append(item);
      });
      setExpanded(true);
    }

    searchInput.addEventListener("focus", renderSuggestions);
    searchInput.addEventListener("input", () => {
      clearFamilyLinkIfTyped();
      renderSuggestions();
    });
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        setExpanded(false);
        return;
      }
      if (event.key !== "Enter" || suggestionList.hidden) return;
      const firstOption = suggestionList.querySelector("button[role='option']");
      if (!firstOption) return;
      event.preventDefault();
      firstOption.click();
    });

    document.addEventListener("click", (event) => {
      if (!root.contains(event.target)) setExpanded(false);
    });
  }

  document.querySelectorAll("[data-visit-person-picker]").forEach(initPicker);
})();
