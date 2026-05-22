/**
 * Jedna župa — branding (nije multitenant)
 */
(function (global) {
  const PARISH_ID = "bdm-slavonski-brod";

  const PARISH = {
    _parishId: PARISH_ID,
    name: "Župa Blažene Djevice Marije",
    shortName: "Bl. Djevice Marije",
    city: "Slavonski Brod",
    diocese: "Đakovačko-osječka nadbiskupija",
    pastor: "vlč. Krunoslav Karas",
    phone: "+385 35 000 000",
    email: "ured@zupa-bdm-sb.hr",
    theme: { primary: "#5c2e3a", accent: "#b8922a" },
  };

  const STORAGE_KEY = "pastoral_data";
  const SETTINGS_KEY = "pastoral_settings";
  const SESSION_KEY = "pastoral_session";

  function applyTheme() {
    const s = loadSettings();
    if (global.PastoralTheme) {
      global.PastoralTheme.applyFromSettings(s);
      return;
    }
    const primary = s.primaryColor || PARISH.theme.primary;
    const accent = s.accentColor || PARISH.theme.accent;
    document.documentElement.style.setProperty("--tenant-primary", primary);
    document.documentElement.style.setProperty("--tenant-accent", accent);
  }

  function loadSettings() {
    try {
      const saved = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
      const merged = { ...PARISH, ...saved };
      if (saved._parishId !== PARISH_ID) {
        merged.name = PARISH.name;
        merged.shortName = PARISH.shortName;
        merged.city = PARISH.city;
        merged.diocese = PARISH.diocese;
        merged.pastor = PARISH.pastor;
        merged._parishId = PARISH_ID;
        if (!saved.phone || saved.phone.includes("1 234")) merged.phone = PARISH.phone;
        if (!saved.email || saved.email.includes("zupa-marka")) merged.email = PARISH.email;
      }
      return merged;
    } catch (_) {
      return { ...PARISH };
    }
  }

  function saveSettings(data) {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify({ ...data, _parishId: PARISH_ID }));
  }

  function renderLogoHtml(large) {
    const s = loadSettings();
    const cls = large ? "tenant-logo tenant-logo-lg" : "tenant-logo";
    if (s.logoUrl) {
      return `<img src="${escapeHtml(s.logoUrl)}" alt="" class="${cls} tenant-logo-img" />`;
    }
    return `<span class="${cls}" style="color:var(--tenant-primary)"><svg viewBox="0 0 48 48" class="tenant-logo-svg"><rect width="48" height="48" rx="10" fill="currentColor" opacity="0.12"/><path d="M24 10v28M16 20h16" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg></span>`;
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  global.PastoralParish = {
    PARISH_ID,
    PARISH,
    STORAGE_KEY,
    SETTINGS_KEY,
    SESSION_KEY,
    applyTheme,
    loadSettings,
    saveSettings,
    renderLogoHtml,
  };
})(typeof window !== "undefined" ? window : global);
