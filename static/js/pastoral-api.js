/**
 * Django API klijent — fetch podataka i CRUD akcije.
 */
(function (global) {
  let cache = null;
  let loading = null;

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute("content");
    const inp = document.querySelector("[name=csrfmiddlewaretoken]");
    return inp ? inp.value : "";
  }

  async function fetchData() {
    const res = await fetch("/api/parish-data/", { credentials: "same-origin" });
    if (!res.ok) throw new Error("parish_data_fetch_failed");
    cache = await res.json();
    return cache;
  }

  async function action(name, payload) {
    const res = await fetch("/api/action/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({ action: name, payload: payload || {} }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok || body.ok === false) {
      const err = new Error(body.error || "action_failed");
      err.details = body;
      throw err;
    }
    if (body.data) {
      if (body.dataPartial) {
        if (cache) cache = { ...cache, ...body.data };
      } else {
        cache = body.data;
      }
    }
    return body;
  }

  async function jsonRequest(url, { method, body } = {}) {
    const headers = { "X-CSRFToken": csrfToken() };
    const options = { method: method || "GET", credentials: "same-origin", headers };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const res = await fetch(url, options);
    const payload = await res.json().catch(() => ({}));
    if (!res.ok || payload.ok === false) {
      const err = new Error(payload.error || payload.detail || "request_failed");
      err.details = payload;
      throw err;
    }
    return payload;
  }

  function upsertCachedIntention(item) {
    if (!cache || !item) return;
    const list = Array.isArray(cache.intentions) ? cache.intentions : [];
    cache.intentions = list.filter((intention) => intention.id !== item.id).concat(item);
  }

  async function createIntention(fields) {
    const response = await jsonRequest("/api/intentions/", {
      method: "POST",
      body: fields,
    });
    upsertCachedIntention(response.item);
    return response.item;
  }

  async function updateIntention(intentionId, fields) {
    const response = await jsonRequest(`/api/intentions/${intentionId}/`, {
      method: "PATCH",
      body: fields,
    });
    upsertCachedIntention(response.item);
    return response.item;
  }

  async function deleteIntention(intentionId) {
    const response = await jsonRequest(`/api/intentions/${intentionId}/`, { method: "DELETE" });
    if (cache && Array.isArray(cache.intentions)) {
      cache.intentions = cache.intentions.filter((intention) => intention.id !== intentionId);
    }
    return response;
  }

  function getCache() {
    return cache ? JSON.parse(JSON.stringify(cache)) : null;
  }

  async function load() {
    if (cache) return getCache();
    if (!loading) loading = fetchData();
    await loading;
    loading = null;
    return getCache();
  }

  function needsParishData() {
    return document.body?.dataset?.needsParishData === "1";
  }

  async function ensureLoaded() {
    if (cache) return getCache();
    if (!needsParishData()) return {};
    return load();
  }

  global.PastoralApi = {
    action,
    createIntention,
    updateIntention,
    deleteIntention,
    load,
    getCache,
    ensureLoaded,
  };
})(typeof window !== "undefined" ? window : global);
