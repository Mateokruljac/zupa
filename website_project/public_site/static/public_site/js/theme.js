(function () {
  'use strict';

  const storageKey = 'public-site-color-scheme';
  const allowed = ['system', 'light', 'dark'];
  const media = window.matchMedia('(prefers-color-scheme: dark)');

  function storedChoice() {
    try {
      const value = window.localStorage.getItem(storageKey);
      return allowed.includes(value) ? value : 'system';
    } catch (_error) {
      return 'system';
    }
  }

  function effectiveTheme(choice) {
    return choice === 'system' ? (media.matches ? 'dark' : 'light') : choice;
  }

  function contrastColor(value) {
    const match = String(value).trim().match(/^#([0-9a-f]{6})$/i);
    if (!match) return '#ffffff';
    const rgb = [0, 2, 4].map(function (offset) {
      return parseInt(match[1].slice(offset, offset + 2), 16) / 255;
    });
    const channels = rgb.map(function (channel) {
      return channel <= 0.04045 ? channel / 12.92 : Math.pow((channel + 0.055) / 1.055, 2.4);
    });
    const luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    const whiteContrast = 1.05 / (luminance + 0.05);
    const darkContrast = (luminance + 0.05) / 0.05;
    return whiteContrast >= darkContrast ? '#ffffff' : '#171417';
  }

  function applyParishContrasts() {
    const styles = window.getComputedStyle(document.documentElement);
    const primary = styles.getPropertyValue('--parish-primary');
    const accent = styles.getPropertyValue('--parish-accent');
    document.documentElement.style.setProperty('--parish-primary-contrast', contrastColor(primary));
    document.documentElement.style.setProperty('--parish-accent-contrast', contrastColor(accent));
  }

  function updateButton(choice) {
    const button = document.querySelector('[data-theme-toggle]');
    if (!button) return;
    const labels = {system: 'Sustav', light: 'Svijetlo', dark: 'Tamno'};
    const icons = {system: '◐', light: '☀', dark: '☾'};
    const label = labels[choice];
    button.querySelector('[data-theme-icon]').textContent = icons[choice];
    button.querySelector('[data-theme-label]').textContent = label;
    button.setAttribute('aria-label', `Tema: ${label}. Promijeni temu.`);
    button.setAttribute('title', `Tema: ${label}`);
  }

  function applyTheme(choice) {
    const normalized = allowed.includes(choice) ? choice : 'system';
    const effective = effectiveTheme(normalized);
    document.documentElement.dataset.colorScheme = normalized;
    document.documentElement.dataset.theme = effective;
    document.documentElement.style.colorScheme = effective;
    updateButton(normalized);
  }

  const initialChoice = storedChoice();
  applyTheme(initialChoice);

  document.addEventListener('DOMContentLoaded', function () {
    applyParishContrasts();
    updateButton(storedChoice());
    const button = document.querySelector('[data-theme-toggle]');
    if (!button) return;
    button.addEventListener('click', function () {
      const current = document.documentElement.dataset.colorScheme || 'system';
      const next = allowed[(allowed.indexOf(current) + 1) % allowed.length];
      try {
        window.localStorage.setItem(storageKey, next);
      } catch (_error) {
        // Privatni način rada može onemogućiti spremanje; tema i dalje radi za ovu stranicu.
      }
      applyTheme(next);
    });
  });

  media.addEventListener('change', function () {
    if ((document.documentElement.dataset.colorScheme || 'system') === 'system') {
      applyTheme('system');
    }
  });
})();
