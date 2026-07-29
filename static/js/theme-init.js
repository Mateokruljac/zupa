/**
 * Rani init svijetlog/tamnog načina — sprječava bljesak pri učitavanju.
 */
(function (global) {
  const STORAGE_KEY = "pastoral-color-scheme";

  function readPref() {
    const el = document.getElementById("parish-settings-data");
    if (el) {
      try {
        const s = JSON.parse(el.textContent);
        if (s.colorScheme) return s.colorScheme;
      } catch {
        /* noop */
      }
    }
    try {
      return localStorage.getItem(STORAGE_KEY) || "light";
    } catch {
      return "light";
    }
  }

  function resolve(pref) {
    if (pref === "system") {
      return global.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return pref === "dark" ? "dark" : "light";
  }

  function applyEarly(pref) {
    const root = document.documentElement;
    root.dataset.colorSchemePref = pref;
    root.dataset.colorScheme = resolve(pref);
  }

  applyEarly(readPref());

  global.PastoralThemeInit = { STORAGE_KEY, readPref, resolve, applyEarly };
})(typeof window !== "undefined" ? window : global);
