/**
 * Rani način prikaza — samo iz #platform-color-data / #parish-settings-data.
 */
(function (global) {
  function readJsonScript(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
  }

  function readPref() {
    const platform = readJsonScript("platform-color-data");
    if (platform && platform.colorScheme) return platform.colorScheme;
    const parish = readJsonScript("parish-settings-data");
    if (parish && parish.colorScheme) return parish.colorScheme;
    return "light";
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

  const publicSite = document.documentElement.hasAttribute("data-public-site");
  applyEarly(publicSite ? "light" : readPref());

  global.PastoralThemeInit = { readPref, resolve, applyEarly };
})(typeof window !== "undefined" ? window : global);
