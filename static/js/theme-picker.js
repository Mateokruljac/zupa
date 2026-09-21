/**
 * Crkvene palete boja — gore desno, spremanje u postavke
 */
(function (global) {
  const PRESETS = [
    {
      id: "bdm",
      name: "Bordó i zlato",
      desc: "Klasična župska",
      primary: "#5c2e3a",
      accent: "#b8922a",
      bg: "#f6f3ed",
      bgPattern: "#ebe6dc",
    },
    {
      id: "marian",
      name: "Marijina plava",
      desc: "Bl. Djevice Marije",
      primary: "#1e4a6f",
      accent: "#c9a227",
      bg: "#f4f7fb",
      bgPattern: "#e6edf5",
    },
    {
      id: "liturgy",
      name: "Liturgijska zelena",
      desc: "Obično vrijeme",
      primary: "#2d5a45",
      accent: "#b8922a",
      bg: "#f3f6f2",
      bgPattern: "#e5ebe3",
    },
    {
      id: "advent",
      name: "Ljubičasta",
      desc: "Advent / korizma",
      primary: "#4a3d6b",
      accent: "#9a8fb8",
      bg: "#f5f3f8",
      bgPattern: "#ebe8f0",
    },
    {
      id: "basilica",
      name: "Bazilika",
      desc: "Kamen i zlato",
      primary: "#3d4543",
      accent: "#c4a35a",
      bg: "#f5f4f1",
      bgPattern: "#e8e6e1",
    },
    {
      id: "dawn",
      name: "Svitanje",
      desc: "Svijetla i topla",
      primary: "#6b4a3a",
      accent: "#d4a574",
      bg: "#faf7f2",
      bgPattern: "#f0ebe3",
    },
  ];

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  const DARK_NEUTRALS = {
    bg: "#1c1917",
    bgPattern: "#292524",
    surface: "#292524",
    surfaceElevated: "#33302c",
    text: "#fafaf9",
    textMuted: "#a8a29e",
    borderBase: "#44403c",
  };

  const LIGHT_NEUTRALS = {
    surface: "#ffffff",
    surfaceElevated: "#fffdf9",
    text: "#2c2824",
    textMuted: "#6d6760",
    borderBase: "#e3dcd2",
  };

  function resolveColorScheme(pref) {
    if (global.PastoralThemeInit?.resolve) return global.PastoralThemeInit.resolve(pref);
    if (pref === "system") {
      return global.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return pref === "dark" ? "dark" : "light";
  }

  function getResolvedScheme() {
    const root = document.documentElement;
    return root.dataset.colorScheme === "dark" ? "dark" : "light";
  }

  function applyColorScheme(pref) {
    const root = document.documentElement;
    const scheme = pref || root.dataset.colorSchemePref || "light";
    root.dataset.colorSchemePref = scheme;
    root.dataset.colorScheme = resolveColorScheme(scheme);
    global.PastoralThemeInit?.applyEarly?.(scheme);
  }

  function hexToRgb(hex) {
    let h = String(hex).replace("#", "").trim();
    if (h.length === 3) h = h.split("").map((c) => c + c).join("");
    if (!/^[0-9a-f]{6}$/i.test(h)) return { r: 92, g: 46, b: 58 };
    return {
      r: parseInt(h.slice(0, 2), 16),
      g: parseInt(h.slice(2, 4), 16),
      b: parseInt(h.slice(4, 6), 16),
    };
  }

  function rgbToHex({ r, g, b }) {
    const part = (value) => Math.round(Math.max(0, Math.min(255, value))).toString(16).padStart(2, "0");
    return `#${part(r)}${part(g)}${part(b)}`;
  }

  function relativeLuminance(color) {
    const { r, g, b } = typeof color === "string" ? hexToRgb(color) : color;
    const channel = (value) => {
      const normalized = value / 255;
      return normalized <= 0.04045
        ? normalized / 12.92
        : Math.pow((normalized + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  }

  function contrastRatio(foreground, background) {
    const a = relativeLuminance(foreground);
    const b = relativeLuminance(background);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  }

  function mixRgb(from, to, amount) {
    const a = typeof from === "string" ? hexToRgb(from) : from;
    const b = typeof to === "string" ? hexToRgb(to) : to;
    return {
      r: a.r + (b.r - a.r) * amount,
      g: a.g + (b.g - a.g) * amount,
      b: a.b + (b.b - a.b) * amount,
    };
  }

  function ensureContrast(color, background, minimum = 4.5) {
    if (contrastRatio(color, background) >= minimum) return rgbToHex(hexToRgb(color));
    const target = relativeLuminance(background) > 0.45 ? "#000000" : "#ffffff";
    let low = 0;
    let high = 1;
    for (let i = 0; i < 18; i += 1) {
      const amount = (low + high) / 2;
      const candidate = rgbToHex(mixRgb(color, target, amount));
      if (contrastRatio(candidate, background) >= minimum) high = amount;
      else low = amount;
    }
    return rgbToHex(mixRgb(color, target, high));
  }

  function bestTextOn(background) {
    const darkText = "#171412";
    const lightText = "#ffffff";
    return contrastRatio(darkText, background) >= contrastRatio(lightText, background)
      ? darkText
      : lightText;
  }

  function applyThemeVars(opts) {
    const root = document.documentElement;
    const primary = opts.primary || "#5c2e3a";
    const accent = opts.accent || "#b8922a";
    const bg = opts.bg || "#f6f3ed";
    const bgPattern = opts.bgPattern || "#ebe6dc";
    const { r, g, b } = hexToRgb(primary);
    const dark = getResolvedScheme() === "dark";
    const neutrals = dark ? DARK_NEUTRALS : LIGHT_NEUTRALS;
    const surfaceForContrast = dark ? DARK_NEUTRALS.surfaceElevated : (opts.surfaceElevated || LIGHT_NEUTRALS.surfaceElevated);
    const primaryText = ensureContrast(primary, surfaceForContrast);
    const accentText = ensureContrast(accent, surfaceForContrast);
    const onPrimary = bestTextOn(primary);
    const onAccent = bestTextOn(accent);
    const primaryFillShade = rgbToHex(mixRgb(
      primary,
      onPrimary === "#ffffff" ? "#000000" : "#ffffff",
      0.12
    ));
    const primaryStrong = ensureContrast(primary, "#ffffff");
    const softAlpha = dark ? 0.14 : 0.08;
    const glowAlpha = dark ? 0.28 : 0.18;
    const shadowAlpha = dark ? 0.35 : 0.08;
    const shadowLgAlpha = dark ? 0.45 : 0.12;

    root.style.setProperty("--tenant-primary-raw", primary);
    root.style.setProperty("--tenant-accent-raw", accent);
    root.style.setProperty("--tenant-primary", primaryText);
    root.style.setProperty("--tenant-accent", accentText);
    root.style.setProperty("--primary", primaryText);
    root.style.setProperty("--accent", accentText);
    root.style.setProperty("--primary-fill", primary);
    root.style.setProperty("--primary-fill-shade", primaryFillShade);
    root.style.setProperty("--primary-strong", primaryStrong);
    root.style.setProperty("--accent-fill", accent);
    root.style.setProperty("--on-primary", onPrimary);
    root.style.setProperty("--on-accent", onAccent);
    root.style.setProperty("--bg", dark ? DARK_NEUTRALS.bg : bg);
    root.style.setProperty("--bg-pattern", dark ? DARK_NEUTRALS.bgPattern : bgPattern);
    root.style.setProperty("--surface", neutrals.surface);
    root.style.setProperty("--surface-elevated", dark ? DARK_NEUTRALS.surfaceElevated : opts.surfaceElevated || LIGHT_NEUTRALS.surfaceElevated);
    root.style.setProperty("--text", neutrals.text);
    root.style.setProperty("--text-muted", neutrals.textMuted);
    root.style.setProperty("--border-base", neutrals.borderBase);
    root.style.setProperty("--primary-rgb", `${r}, ${g}, ${b}`);
    root.style.setProperty("--primary-soft", `rgba(${r}, ${g}, ${b}, ${softAlpha})`);
    root.style.setProperty("--primary-glow", `rgba(${r}, ${g}, ${b}, ${glowAlpha})`);
    root.style.setProperty("--accent-soft", `color-mix(in srgb, ${accent} ${dark ? 28 : 22}%, transparent)`);
    root.style.setProperty("--shadow", `0 8px 32px rgba(${dark ? "0, 0, 0" : `${r}, ${g}, ${b}`}, ${shadowAlpha})`);
    root.style.setProperty("--shadow-lg", `0 16px 48px rgba(${dark ? "0, 0, 0" : `${r}, ${g}, ${b}`}, ${shadowLgAlpha})`);
    root.style.setProperty("--border-tint", `color-mix(in srgb, ${primary} ${dark ? 18 : 12}%, var(--border-base))`);
    root.dataset.themePreset = opts.presetId || "custom";
    root.dataset.themeContrastAdjusted = String(primaryText.toLowerCase() !== primary.toLowerCase() || accentText.toLowerCase() !== accent.toLowerCase());
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", primary);
  }

  function applyFromSettings(settings) {
    applyColorScheme(settings.colorScheme || "light");
    applyThemeVars({
      presetId: settings.themePresetId || "custom",
      primary: settings.primaryColor || "#5c2e3a",
      accent: settings.accentColor || "#b8922a",
      bg: settings.bgColor || "#f6f3ed",
      bgPattern: settings.bgPatternColor || "#ebe6dc",
    });
  }

  function saveTheme(partial) {
    const P = global.PastoralParish;
    if (!P) return;
    const cur = P.loadSettings();
    const next = { ...cur, ...partial };
    if (partial.primaryColor != null && partial.customTheme === undefined) {
      next.customTheme = true;
    }
    P.saveSettings(next);
    applyFromSettings(next);
  }

  function renderModeToggleHtml(settings) {
    const pref = settings.colorScheme || document.documentElement.dataset.colorSchemePref || "light";
    const modes = [
      { id: "light", label: "Svijetlo", icon: "☀" },
      { id: "dark", label: "Tamno", icon: "☾" },
      { id: "system", label: "Sustav", icon: "◐" },
    ];
    return `
      <div class="theme-mode-section">
        <p class="theme-custom-title">Način prikaza</p>
        <div class="theme-mode-toggle" role="group" aria-label="Svijetli ili tamni način">
          ${modes
            .map(
              (m) => `
            <button type="button" class="theme-mode-btn ${pref === m.id ? "active" : ""}" data-color-scheme="${m.id}" title="${m.label}">
              <span class="theme-mode-icon" aria-hidden="true">${m.icon}</span>
              <span>${m.label}</span>
            </button>`
            )
            .join("")}
        </div>
      </div>`;
  }

  function renderPanelHtml(settings) {
    const activeId = settings.customTheme ? "custom" : settings.themePresetId || "bdm";
    return `
      <div class="theme-picker-panel" id="theme-picker-panel" role="dialog" aria-label="Paleta boja" hidden>
        <div class="theme-picker-panel-head">
          <strong>Paleta župe</strong>
          <button type="button" class="theme-picker-close" aria-label="Zatvori">×</button>
        </div>
        ${renderModeToggleHtml(settings)}
        <p class="card-sub">Odaberite ton boja — ostaje u skladu s crkvenim okruženjem.</p>
        <div class="theme-preset-grid">
          ${PRESETS.map(
            (p) => `
            <button type="button" class="theme-preset-btn ${activeId === p.id ? "active" : ""}" data-preset="${p.id}" title="${escapeHtml(p.name)}">
              <span class="theme-swatch-pair">
                <span class="theme-swatch" style="background:${p.primary}"></span>
                <span class="theme-swatch accent" style="background:${p.accent}"></span>
              </span>
              <span class="theme-preset-label">${escapeHtml(p.name)}</span>
              <small>${escapeHtml(p.desc)}</small>
            </button>`
          ).join("")}
        </div>
        <div class="theme-custom">
          <p class="theme-custom-title">Prilagodi boje</p>
          <div class="theme-custom-row">
            <label>Glavna <input type="color" id="theme-color-primary" value="${settings.primaryColor || "#5c2e3a"}" /></label>
            <label>Zlatni akcent <input type="color" id="theme-color-accent" value="${settings.accentColor || "#b8922a"}" /></label>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" id="theme-apply-custom">Primijeni prilagodbu</button>
          <p class="theme-contrast-note">Kontrast se automatski prilagođava svijetlom i tamnom načinu. Vaša izvorna boja ostaje spremljena.</p>
        </div>
      </div>`;
  }

  function renderQuickModeBtn() {
    const dark = getResolvedScheme() === "dark";
    return `
      <button type="button" class="btn btn-theme-mode" id="theme-mode-quick" title="${dark ? "Tamni način — klikni za svijetli" : "Svijetli način — klikni za tamni"}" aria-label="Prebaci svijetli/tamni način">
        <span class="theme-mode-quick-icon" aria-hidden="true">${dark ? "☀" : "☾"}</span>
      </button>`;
  }

  function renderTriggerHtml() {
    return `
      <div class="theme-picker-wrap">
        ${renderQuickModeBtn()}
        <button type="button" class="btn btn-theme-toggle" id="theme-picker-toggle" title="Paleta boja" aria-expanded="false">
          <span class="theme-toggle-icon" aria-hidden="true"></span>
          <span class="theme-toggle-label">Boje</span>
        </button>
      </div>`;
  }

  function updateQuickModeBtn(mount) {
    const btn = mount?.querySelector("#theme-mode-quick");
    if (!btn) return;
    const dark = getResolvedScheme() === "dark";
    btn.title = dark ? "Tamni način — klikni za svijetli" : "Svijetli način — klikni za tamni";
    const icon = btn.querySelector(".theme-mode-quick-icon");
    if (icon) icon.textContent = dark ? "☀" : "☾";
  }

  function setColorScheme(partial, mount) {
    saveTheme(partial);
    updateQuickModeBtn(mount);
    const pref = partial.colorScheme || document.documentElement.dataset.colorSchemePref;
    mount?.querySelectorAll("[data-color-scheme]").forEach((b) => {
      b.classList.toggle("active", b.dataset.colorScheme === pref);
    });
  }

  function bindPicker(mount) {
    const P = global.PastoralParish;
    if (!mount || mount.dataset.bound) return;
    mount.dataset.bound = "1";

    const toggle = mount.querySelector("#theme-picker-toggle");
    const panel = mount.querySelector("#theme-picker-panel");
    if (!toggle || !panel) return;

    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = !panel.hidden;
      panel.hidden = open;
      toggle.setAttribute("aria-expanded", String(!open));
      toggle.classList.toggle("is-open", !open);
      mount.classList.toggle("is-open", !open);
    });

    document.addEventListener("click", (e) => {
      if (!mount.contains(e.target)) {
        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        toggle.classList.remove("is-open");
        mount.classList.remove("is-open");
      }
    });

    panel.addEventListener("click", (e) => e.stopPropagation());

    panel.querySelector(".theme-picker-close")?.addEventListener("click", () => {
      panel.hidden = true;
      toggle.classList.remove("is-open");
      mount.classList.remove("is-open");
    });

    mount.querySelector("#theme-mode-quick")?.addEventListener("click", (e) => {
      e.stopPropagation();
      const next = getResolvedScheme() === "dark" ? "light" : "dark";
      setColorScheme({ colorScheme: next }, mount);
      showThemeToast(next === "dark" ? "Tamni način" : "Svijetli način");
    });

    panel.querySelectorAll("[data-color-scheme]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const scheme = btn.dataset.colorScheme;
        setColorScheme({ colorScheme: scheme }, mount);
        const labels = { light: "Svijetli način", dark: "Tamni način", system: "Način prema sustavu" };
        showThemeToast(labels[scheme] || "Način prikaza promijenjen");
      });
    });

    panel.querySelectorAll("[data-preset]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const preset = PRESETS.find((p) => p.id === btn.dataset.preset);
        if (!preset) return;
        saveTheme({
          themePresetId: preset.id,
          primaryColor: preset.primary,
          accentColor: preset.accent,
          bgColor: preset.bg,
          bgPatternColor: preset.bgPattern,
          customTheme: false,
        });
        panel.querySelectorAll(".theme-preset-btn").forEach((b) => b.classList.toggle("active", b === btn));
        showThemeToast("Tema: " + preset.name);
      });
    });

    document.getElementById("theme-apply-custom")?.addEventListener("click", () => {
      const primary = document.getElementById("theme-color-primary")?.value;
      const accent = document.getElementById("theme-color-accent")?.value;
      saveTheme({
        primaryColor: primary,
        accentColor: accent,
        customTheme: true,
        themePresetId: "custom",
      });
      panel.querySelectorAll(".theme-preset-btn").forEach((b) => b.classList.remove("active"));
      showThemeToast("Prilagođene boje primijenjene");
    });

    ["theme-color-primary", "theme-color-accent"].forEach((id) => {
      document.getElementById(id)?.addEventListener("input", (e) => {
        saveTheme({
          primaryColor: document.getElementById("theme-color-primary")?.value,
          accentColor: document.getElementById("theme-color-accent")?.value,
          customTheme: true,
          themePresetId: "custom",
        });
      });
    });
  }

  function showThemeToast(msg) {
    if (typeof global.showToast === "function") {
      global.showToast(msg);
      return;
    }
    document.querySelector(".toast")?.remove();
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2200);
  }

  function getAdminTopbarActions() {
    const topbar = document.querySelector(".app-shell .topbar");
    if (!topbar) return null;
    let actions = topbar.querySelector(".topbar-actions");
    if (!actions) {
      actions = document.createElement("div");
      actions.className = "topbar-actions";
      topbar.appendChild(actions);
    }
    return actions;
  }

  /** U topbaru odmah iza gumba Prezentacija (navbar), ili fixed samo na loginu */
  function placeInTopbar(mount) {
    const actions = getAdminTopbarActions();
    if (!actions) return false;
    mount.classList.remove("theme-picker-root--fixed");
    const prez = document.getElementById("btn-demo-present");
    if (prez && actions.contains(prez)) {
      if (mount.previousElementSibling !== prez) {
        prez.insertAdjacentElement("afterend", mount);
      }
    } else if (mount.parentElement !== actions) {
      actions.insertBefore(mount, actions.firstChild);
    }
    return true;
  }

  function repositionInTopbar() {
    const mount = document.getElementById("theme-picker-root");
    if (!mount || mount.classList.contains("theme-picker-root--fixed")) return;
    placeInTopbar(mount);
  }

  let systemSchemeListenerBound = false;

  function bindSystemSchemeListener() {
    if (systemSchemeListenerBound) return;
    systemSchemeListenerBound = true;
    global.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (document.documentElement.dataset.colorSchemePref !== "system") return;
      applyColorScheme("system");
      const P = global.PastoralParish;
      if (P) applyFromSettings(P.loadSettings());
      const mount = document.getElementById("theme-picker-root");
      updateQuickModeBtn(mount);
    });
  }

  /** @param {{ fixed?: boolean }} opts — fixed samo login / stranice bez app-shell */
  function initThemePicker(opts = {}) {
    const P = global.PastoralParish;
    if (!P) return;
    const settings = P.loadSettings();
    applyFromSettings(settings);
    bindSystemSchemeListener();

    const useFixed = !!opts.fixed;
    let mount = document.getElementById("theme-picker-root");
    if (!mount) {
      mount = document.createElement("div");
      mount.id = "theme-picker-root";
      mount.className = useFixed ? "theme-picker-root theme-picker-root--fixed" : "theme-picker-root";
    } else {
      mount.className = useFixed ? "theme-picker-root theme-picker-root--fixed" : "theme-picker-root";
    }

    mount.innerHTML = renderTriggerHtml() + renderPanelHtml(settings);

    if (useFixed) {
      document.body.appendChild(mount);
    } else if (!placeInTopbar(mount)) {
      document.body.appendChild(mount);
    }

    bindPicker(mount);
  }

  global.PastoralTheme = {
    PRESETS,
    applyThemeVars,
    contrastRatio,
    ensureContrast,
    bestTextOn,
    applyColorScheme,
    applyFromSettings,
    saveTheme,
    initThemePicker,
    repositionInTopbar,
    placeInTopbar,
  };
})(typeof window !== "undefined" ? window : global);
