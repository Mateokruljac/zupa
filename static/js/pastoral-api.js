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
    if (body.data) cache = body.data;
    return body;
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
    load,
    getCache,
    ensureLoaded,
  };
})(typeof window !== "undefined" ? window : global);
