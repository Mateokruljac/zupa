(function () {
  "use strict";

  const optionsElement = document.getElementById("family-street-options");
  const streets = optionsElement ? JSON.parse(optionsElement.textContent) : [];
  const streetDialog = document.getElementById("family-street-dialog");
  const createForm = streetDialog?.querySelector("[data-street-create-form]");
  const nameInput = createForm?.querySelector("[name='name']");
  const cityInput = createForm?.querySelector("[name='city']");
  const notesInput = createForm?.querySelector("[name='notes']");
  const confirmButton = createForm?.querySelector("[type='submit']");
  const errorMessage = streetDialog?.querySelector("[data-street-create-error]");
  let activePicker = null;

  function streetLabel(street) {
    const streetName = street.name || "";
    return street.city ? streetName + " (" + street.city + ")" : streetName;
  }

  function csrfToken(form) {
    const tokenField = form?.querySelector("[name=csrfmiddlewaretoken]");
    if (tokenField) return tokenField.value;
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  function matchingStreets(query) {
    const normalizedQuery = query.trim().toLocaleLowerCase("hr");
    if (!normalizedQuery) return streets.slice();
    return streets.filter((street) =>
      streetLabel(street).toLocaleLowerCase("hr").includes(normalizedQuery)
    );
  }

  function syncSearchFromId(picker) {
    const streetIdInput = picker.querySelector("[data-street-id]");
    const searchInput = picker.querySelector("[data-street-search]");
    if (!streetIdInput || !searchInput) return;
    const street = streets.find((item) => item.id === streetIdInput.value);
    searchInput.value = street ? street.name || "" : "";
  }

  function initPicker(picker) {
    const searchInput = picker.querySelector("[data-street-search]");
    const streetIdInput = picker.querySelector("[data-street-id]");
    const suggestionList = picker.querySelector("[data-street-suggestions]");
    const addButton = picker.querySelector("[data-street-add]");
    if (!searchInput || !streetIdInput || !suggestionList) return;

    function setExpanded(isExpanded) {
      searchInput.setAttribute("aria-expanded", isExpanded ? "true" : "false");
      suggestionList.hidden = !isExpanded;
    }

    function selectStreet(street) {
      streetIdInput.value = street ? street.id : "";
      searchInput.value = street ? street.name || "" : "";
      setExpanded(false);
    }

    picker._selectStreet = selectStreet;
    picker._syncSearch = () => syncSearchFromId(picker);

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

    searchInput.addEventListener("focus", () => {
      activePicker = picker;
      renderSuggestions();
    });
    searchInput.addEventListener("input", () => {
      streetIdInput.value = "";
      activePicker = picker;
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

    addButton?.addEventListener("click", () => {
      if (!streetDialog || !createForm) return;
      activePicker = picker;
      setExpanded(false);
      createForm.reset();
      if (errorMessage) errorMessage.hidden = true;
      nameInput.value = searchInput.value.trim();
      if (typeof streetDialog.showModal === "function") streetDialog.showModal();
      else streetDialog.setAttribute("open", "");
      nameInput.focus();
    });

    syncSearchFromId(picker);
  }

  document.querySelectorAll("[data-street-picker]").forEach(initPicker);

  function closeStreetDialog() {
    if (!streetDialog) return;
    if (typeof streetDialog.close === "function") streetDialog.close();
    else streetDialog.removeAttribute("open");
  }

  streetDialog?.addEventListener("close", () => {
    if (errorMessage) errorMessage.hidden = true;
    if (confirmButton) confirmButton.disabled = false;
  });

  createForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const streetName = nameInput.value.trim();
    if (errorMessage) errorMessage.hidden = true;
    if (!streetName) {
      nameInput.focus();
      return;
    }
    const existingStreet = streets.find(
      (street) =>
        (street.name || "").trim().toLocaleLowerCase("hr") === streetName.toLocaleLowerCase("hr")
    );
    if (existingStreet) {
      activePicker?._selectStreet?.(existingStreet);
      closeStreetDialog();
      return;
    }

    if (confirmButton) confirmButton.disabled = true;
    const formData = new FormData();
    const token = csrfToken(activePicker?.closest("form") || createForm);
    formData.set("csrfmiddlewaretoken", token);
    formData.set("action", "add_street");
    formData.set("name", streetName);
    formData.set("city", cityInput.value.trim());
    formData.set("notes", notesInput.value.trim());
    try {
      const response = await fetch(window.location.pathname + window.location.search, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": token },
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok || !payload.street?.id) {
        if (errorMessage) errorMessage.hidden = false;
        return;
      }
      const street = {
        id: payload.street.id,
        name: payload.street.name || streetName,
        city: payload.street.city || "",
      };
      streets.push(street);
      activePicker?._selectStreet?.(street);
      closeStreetDialog();
    } catch (error) {
      if (errorMessage) errorMessage.hidden = false;
    } finally {
      if (streetDialog?.open && confirmButton) confirmButton.disabled = false;
    }
  });

  document.addEventListener("click", (event) => {
    document.querySelectorAll("[data-street-picker]").forEach((picker) => {
      if (picker.contains(event.target)) return;
      const suggestionList = picker.querySelector("[data-street-suggestions]");
      const searchInput = picker.querySelector("[data-street-search]");
      if (suggestionList) suggestionList.hidden = true;
      if (searchInput) searchInput.setAttribute("aria-expanded", "false");
    });
  });

  window.familyStreetPicker = {
    syncAll() {
      document.querySelectorAll("[data-street-picker]").forEach((picker) => {
        picker._syncSearch?.();
      });
    },
    setStreet(pickerOrForm, streetId, streetName) {
      const picker =
        pickerOrForm?.matches?.("[data-street-picker]")
          ? pickerOrForm
          : pickerOrForm?.querySelector?.("[data-street-picker]");
      if (!picker) return;
      const street =
        streets.find((item) => item.id === streetId) ||
        (streetId ? { id: streetId, name: streetName || "" } : null);
      if (street && !streets.some((item) => item.id === street.id)) {
        streets.push(street);
      }
      picker._selectStreet?.(street || null);
    },
  };
})();
