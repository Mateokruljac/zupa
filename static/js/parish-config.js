/**
 * Postavke župe — Django: isključivo s servera (#parish-settings-data).
 */
(function (global) {
  const PARISH_ID = "bdm-slavonski-brod";

  const FALLBACK = {
    _parishId: PARISH_ID,
    name: "Župa",
    shortName: "Župa",
    city: "",
    diocese: "",
    pastor: "",
    phone: "",
    email: "",
    primaryColor: "#5c2e3a",
    accentColor: "#b8922a",
    colorScheme: "light",
  };

  function readJsonScript(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
  }

  function readServerSettings() {
    return readJsonScript("parish-settings-data");
  }

  function readPlatformColor() {
    const platform = readJsonScript("platform-color-data");
    return platform && typeof platform === "object" ? platform : null;
  }

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute("content");
    const inp = document.querySelector("[name=csrfmiddlewaretoken]");
    return inp ? inp.value : "";
  }

  function isDjangoShell() {
    return document.body?.dataset?.djangoShell === "1";
  }

  const THEME_KEYS = [
    "primaryColor",
    "accentColor",
    "bgColor",
    "bgPatternColor",
    "themePresetId",
    "customTheme",
    "colorScheme",
  ];

  function omitThemeKeys(data) {
    const rest = { ...data };
    THEME_KEYS.forEach((key) => {
      delete rest[key];
    });
    return rest;
  }

  function themeFrom(data) {
    const theme = {};
    THEME_KEYS.forEach((key) => {
      if (data && data[key] != null) theme[key] = data[key];
    });
    return theme;
  }

  function loadSettings() {
    const server = omitThemeKeys(readServerSettings() || {});
    const platform = themeFrom(readPlatformColor() || {});
    const merged = { ...omitThemeKeys(FALLBACK), ...server, ...platform };
    if (!merged.colorScheme) merged.colorScheme = "light";
    return merged;
  }

  function writeServerSettings(payload) {
    const parishEl = document.getElementById("parish-settings-data");
    if (parishEl) {
      try {
        parishEl.textContent = JSON.stringify(omitThemeKeys(payload));
      } catch {
        /* noop */
      }
    }
    const platformEl = document.getElementById("platform-color-data");
    if (platformEl) {
      try {
        platformEl.textContent = JSON.stringify(themeFrom(payload));
      } catch {
        /* noop */
      }
    }
  }

  function saveSettings(data) {
    const payload = { ...loadSettings(), ...data };
    writeServerSettings(payload);
    if (!isDjangoShell()) return;
    fetch("/theme/save/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({
        primaryColor: payload.primaryColor,
        accentColor: payload.accentColor,
        bgColor: payload.bgColor,
        bgPatternColor: payload.bgPatternColor,
        themePresetId: payload.themePresetId,
        customTheme: payload.customTheme,
        colorScheme: payload.colorScheme,
      }),
      credentials: "same-origin",
    }).catch(() => {});
  }

  function applyTheme() {
    const s = loadSettings();
    if (global.PastoralTheme) {
      global.PastoralTheme.applyFromSettings(s);
      return;
    }
    document.documentElement.style.setProperty("--tenant-primary", s.primaryColor || FALLBACK.primaryColor);
    document.documentElement.style.setProperty("--tenant-accent", s.accentColor || FALLBACK.accentColor);
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderLogoHtml(large) {
    const s = loadSettings();
    const cls = large ? "tenant-logo tenant-logo-lg" : "tenant-logo";
    if (s.logoUrl) {
      return `<img src="${escapeHtml(s.logoUrl)}" alt="" class="${cls} tenant-logo-img" />`;
    }
    return `<span class="${cls}" style="color:var(--tenant-primary)"><svg viewBox="0 0 48 48" class="tenant-logo-svg"><rect width="48" height="48" rx="10" fill="currentColor" opacity="0.12"/><path d="M24 10v28M16 20h16" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg></span>`;
  }

  global.PastoralParish = {
    PARISH_ID,
    applyTheme,
    loadSettings,
    saveSettings,
    renderLogoHtml,
  };

  if (readServerSettings() && global.PastoralTheme) {
    global.PastoralTheme.applyFromSettings(loadSettings());
  }
})(typeof window !== "undefined" ? window : global);
