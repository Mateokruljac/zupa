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

  function setCache(data) {
    cache = data;
  }

  async function load() {
    if (cache) return getCache();
    if (!loading) loading = fetchData();
    await loading;
    loading = null;
    return getCache();
  }

  async function reload() {
    loading = fetchData();
    await loading;
    loading = null;
    return getCache();
  }

  function readOfficeStats() {
    const el = document.getElementById("office-stats-data");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
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
    reload,
    fetchData,
    getCache,
    setCache,
    csrfToken,
    ensureLoaded,
    readOfficeStats,
  };

  global.PastoralData = {
    load() {
      const c = getCache();
      if (c) return JSON.parse(JSON.stringify(c));
      return {};
    },
    save() {
      console.warn("[PastoralData] save() onemogućen — koristite Django POST ili PastoralApi.action()");
    },
    ensureSeed() {
      ensureLoaded().catch(() => {});
    },
    loadAsync: () => load(),
    defaultData() {
      return global.PastoralData.load();
    },
  };

  global.PastoralDataApi = {
    fetchFromServer: () => reload(),
    action: (name, payload) => action(name, payload),
  };
})(typeof window !== "undefined" ? window : global);
