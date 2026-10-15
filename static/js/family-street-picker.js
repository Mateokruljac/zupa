(function () {
  "use strict";

  const picker = document.querySelector("[data-street-picker]");
  if (!picker) return;

  const optionsElement = document.getElementById("family-street-options");
  const streets = optionsElement ? JSON.parse(optionsElement.textContent) : [];
  const searchInput = picker.querySelector("[data-street-search]");
  const streetIdInput = picker.querySelector("[data-street-id]");
  const suggestionList = picker.querySelector("[data-street-suggestions]");
  const addButton = picker.querySelector("[data-street-add]");
  const streetDialog = document.getElementById("family-street-dialog");
  const createForm = streetDialog?.querySelector("[data-street-create-form]");
  const nameInput = createForm?.querySelector("[name='name']");
  const cityInput = createForm?.querySelector("[name='city']");
  const notesInput = createForm?.querySelector("[name='notes']");
  const confirmButton = createForm?.querySelector("[type='submit']");
  const errorMessage = streetDialog?.querySelector("[data-street-create-error]");
  const familyForm = picker.closest("form");

  function streetLabel(street) {
    const streetName = street.name || "";
    return street.city ? streetName + " (" + street.city + ")" : streetName;
  }

  function setExpanded(isExpanded) {
    searchInput.setAttribute("aria-expanded", isExpanded ? "true" : "false");
    suggestionList.hidden = !isExpanded;
  }

  function selectStreet(street) {
    streetIdInput.value = street ? street.id : "";
    searchInput.value = street ? street.name || "" : "";
    setExpanded(false);
  }

  function matchingStreets(query) {
    const normalizedQuery = query.trim().toLocaleLowerCase("hr");
    if (!normalizedQuery) return streets.slice();
    return streets.filter((street) =>
      streetLabel(street).toLocaleLowerCase("hr").includes(normalizedQuery)
    );
  }

  function renderSuggestions() {
    suggestionList.replaceChildren();
    const query = searchInput.value;
    const matches = matchingStreets(query);

    if (!query.trim()) {
      const clearItem = document.createElement("li");
      const clearButton = document.createElement("button");
      clearButton.type = "button";
      clearButton.textContent = "Bez povezane ulice";
      clearButton.addEventListener("click", () => selectStreet(null));
      clearItem.append(clearButton);
      suggestionList.append(clearItem);
    }

    if (!matches.length && query.trim()) {
      const emptyItem = document.createElement("li");
      emptyItem.className = "family-street-suggestions__empty";
      emptyItem.textContent = "Nema te ulice. Dodajte je gumbom +.";
      suggestionList.append(emptyItem);
    }

    matches.forEach((street) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.setAttribute("role", "option");
      button.textContent = streetLabel(street);
      button.addEventListener("click", () => selectStreet(street));
      item.append(button);
      suggestionList.append(item);
    });
    setExpanded(true);
  }

  function csrfToken() {
    const tokenField = familyForm?.querySelector("[name=csrfmiddlewaretoken]");
    if (tokenField) return tokenField.value;
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  function showCreateError() {
    errorMessage.hidden = false;
  }

  function appendStreetOption(street) {
    document.querySelectorAll("select[name='street'], select[name='street_id']").forEach((select) => {
      const alreadyListed = [...select.options].some((option) => option.value === street.id);
      if (alreadyListed) return;
      const option = document.createElement("option");
      option.value = street.id;
      option.textContent = streetLabel(street);
      select.append(option);
    });
  }

  searchInput.addEventListener("focus", renderSuggestions);
  searchInput.addEventListener("input", () => {
    streetIdInput.value = "";
    renderSuggestions();
  });
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setExpanded(false);
      return;
    }
    if (event.key !== "Enter") return;
    event.preventDefault();
    const matches = matchingStreets(searchInput.value);
    if (matches.length === 1) selectStreet(matches[0]);
  });

  searchInput.addEventListener("blur", () => {
    window.setTimeout(() => {
      if (streetDialog?.open) return;
      const typedName = searchInput.value.trim().toLocaleLowerCase("hr");
      if (!typedName) {
        selectStreet(null);
        return;
      }
      const exactMatch = streets.find(
        (street) => (street.name || "").trim().toLocaleLowerCase("hr") === typedName
      );
      if (exactMatch) {
        selectStreet(exactMatch);
        return;
      }
      if (!streetIdInput.value) searchInput.value = "";
    }, 180);
  });

  function openStreetDialog() {
    if (!streetDialog || !createForm) return;
    setExpanded(false);
    createForm.reset();
    errorMessage.hidden = true;
    nameInput.value = searchInput.value.trim();
    if (typeof streetDialog.showModal === "function") streetDialog.showModal();
    else streetDialog.setAttribute("open", "");
    nameInput.focus();
  }

  function closeStreetDialog() {
    if (!streetDialog) return;
    if (typeof streetDialog.close === "function") streetDialog.close();
    else streetDialog.removeAttribute("open");
  }

  addButton.addEventListener("click", openStreetDialog);

  streetDialog?.addEventListener("close", () => {
    errorMessage.hidden = true;
    if (confirmButton) confirmButton.disabled = false;
  });

  createForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const streetName = nameInput.value.trim();
    errorMessage.hidden = true;
    if (!streetName) {
      nameInput.focus();
      return;
    }
    const existingStreet = streets.find(
      (street) => (street.name || "").trim().toLocaleLowerCase("hr") === streetName.toLocaleLowerCase("hr")
    );
    if (existingStreet) {
      selectStreet(existingStreet);
      closeStreetDialog();
      return;
    }

    confirmButton.disabled = true;
    const formData = new FormData();
    formData.set("csrfmiddlewaretoken", csrfToken());
    formData.set("action", "add_street");
    formData.set("name", streetName);
    formData.set("city", cityInput.value.trim());
    formData.set("notes", notesInput.value.trim());
    try {
      const response = await fetch(window.location.pathname + window.location.search, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrfToken() },
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok || !payload.street?.id) {
        showCreateError();
        return;
      }
      const street = {
        id: payload.street.id,
        name: payload.street.name || streetName,
        city: payload.street.city || "",
      };
      streets.push(street);
      appendStreetOption(street);
      selectStreet(street);
      closeStreetDialog();
    } catch (error) {
      showCreateError();
    } finally {
      if (streetDialog?.open) confirmButton.disabled = false;
    }
  });

  document.addEventListener("click", (event) => {
    if (!picker.contains(event.target)) setExpanded(false);
  });
})();
