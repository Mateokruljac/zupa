/**
 * Modal za sve CRUD operacije
 */
(function (global) {
  let activeOverlay = null;

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function close() {
    if (!activeOverlay) return;
    activeOverlay._cleanup?.();
    activeOverlay.remove();
    activeOverlay = null;
    document.body.style.overflow = "";
  }

  function bindCloseOnlyX(overlay, onClose) {
    overlay.querySelector(".pastoral-modal-close")?.addEventListener("click", () => {
      close();
      onClose?.();
    });
    overlay.querySelector(".pastoral-modal")?.addEventListener("click", (e) => e.stopPropagation());
  }

  function defaultFooter(formId, submitLabel, danger) {
    const cls = danger ? "btn-danger" : "btn-primary";
    return `
      <button type="button" class="btn btn-ghost" data-modal-cancel>Odustani</button>
      <button type="submit" class="btn ${cls}" form="${formId}">${escapeHtml(submitLabel || "Spremi")}</button>`;
  }

  /**
   * @param {object} opts
   * @param {string} opts.title
   * @param {string} opts.body - HTML unutar forme
   * @param {string} [opts.footer]
   * @param {string} [opts.size] sm | md | lg
   * @param {function} [opts.onSubmit] (form) => false to stay open
   * @param {function} [opts.onOpen] (overlay)
   * @param {boolean} [opts.danger]
   */
  function openForm(opts) {
    const formId = opts.formId || "pastoral-modal-form";
    close();
    const overlay = document.createElement("div");
    overlay.className = "pastoral-modal-overlay";
    const size = opts.size || "md";
    overlay.innerHTML = `
      <div class="pastoral-modal pastoral-modal--${size}" role="dialog" aria-modal="true" aria-labelledby="pastoral-modal-title">
        <header class="pastoral-modal-head">
          <h2 id="pastoral-modal-title" class="pastoral-modal-title">${escapeHtml(opts.title)}</h2>
          <button type="button" class="pastoral-modal-close" aria-label="Zatvori">&times;</button>
        </header>
        <form id="${formId}" class="pastoral-modal-body form-grid">${opts.body}</form>
        <footer class="pastoral-modal-foot">${opts.footer || defaultFooter(formId, opts.submitLabel, opts.danger)}</footer>
      </div>`;

    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";
    activeOverlay = overlay;

    const form = overlay.querySelector(`#${formId}`);
    if (opts.closeOnEscape !== false) {
      const onKey = (e) => {
        if (e.key === "Escape") close();
      };
      document.addEventListener("keydown", onKey);
      overlay._cleanup = () => document.removeEventListener("keydown", onKey);
    }

    const dismiss = () => close();
    overlay.querySelector(".pastoral-modal-close")?.addEventListener("click", dismiss);
    overlay.querySelector("[data-modal-cancel]")?.addEventListener("click", dismiss);
    if (opts.closeOnBackdrop !== false) {
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) dismiss();
      });
    }
    overlay.querySelector(".pastoral-modal")?.addEventListener("click", (e) => e.stopPropagation());

    form?.addEventListener("submit", (e) => {
      e.preventDefault();
      if (opts.onSubmit?.(form) === false) return;
      close();
    });

    opts.onOpen?.(overlay, form);
    const first = form?.querySelector("input,select,textarea,button");
    if (first) setTimeout(() => first.focus(), 50);
    return { overlay, form, close };
  }

  /**
   * @param {object} opts
   * @param {string} opts.title
   * @param {string} opts.message
   * @param {boolean} [opts.danger]
   * @param {string} [opts.confirmLabel]
   * @param {function} opts.onConfirm
   * @param {function} [opts.onCancel]
   */
  function confirm(opts) {
    close();
    const overlay = document.createElement("div");
    overlay.className = "pastoral-modal-overlay";
    overlay.innerHTML = `
      <div class="pastoral-modal pastoral-modal--sm" role="alertdialog" aria-modal="true">
        <header class="pastoral-modal-head">
          <h2 class="pastoral-modal-title">${escapeHtml(opts.title || "Potvrda")}</h2>
          <button type="button" class="pastoral-modal-close" aria-label="Zatvori">&times;</button>
        </header>
        <div class="pastoral-modal-body pastoral-modal-body--text">
          <p>${escapeHtml(opts.message)}</p>
        </div>
        <footer class="pastoral-modal-foot">
          <button type="button" class="btn btn-ghost" data-modal-cancel>Odustani</button>
          <button type="button" class="btn ${opts.danger ? "btn-danger" : "btn-primary"}" data-modal-confirm>${escapeHtml(opts.confirmLabel || (opts.danger ? "Obriši" : "Potvrdi"))}</button>
        </footer>
      </div>`;
    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";
    activeOverlay = overlay;

    const done = (fn) => {
      close();
      fn?.();
    };
    overlay.querySelector("[data-modal-confirm]")?.addEventListener("click", () => done(opts.onConfirm));
    overlay.querySelector("[data-modal-cancel]")?.addEventListener("click", () => done(opts.onCancel));
    overlay.querySelector(".pastoral-modal-close")?.addEventListener("click", () => done(opts.onCancel));
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) done(opts.onCancel);
    });
  }

  function confirmPromise(opts) {
    return new Promise((resolve) => {
      confirm({
        ...opts,
        onConfirm: () => resolve(true),
        onCancel: () => resolve(false),
      });
    });
  }

  /**
   * Prikaz detalja — zatvara se isključivo na × (bez klika izvan i Escape)
   * @param {object} opts
   * @param {string} opts.title
   * @param {string} opts.body - HTML
   * @param {string} [opts.size] sm | md | lg | xl
   * @param {function} [opts.onClose]
   * @param {function} [opts.onOpen] (overlay)
   */
  function openDetail(opts) {
    close();
    const overlay = document.createElement("div");
    overlay.className = "pastoral-modal-overlay pastoral-modal-overlay--detail";
    const size = opts.size || "lg";
    overlay.innerHTML = `
      <div class="pastoral-modal pastoral-modal--${size} pastoral-modal--detail" role="dialog" aria-modal="true" aria-labelledby="pastoral-modal-title">
        <header class="pastoral-modal-head">
          <h2 id="pastoral-modal-title" class="pastoral-modal-title">${escapeHtml(opts.title)}</h2>
          <button type="button" class="pastoral-modal-close" aria-label="Zatvori">&times;</button>
        </header>
        <div class="pastoral-modal-body pastoral-modal-body--detail">${opts.body}</div>
      </div>`;
    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";
    activeOverlay = overlay;
    bindCloseOnlyX(overlay, opts.onClose);
    opts.onOpen?.(overlay);
    return { overlay, close };
  }

  /** Samo prikaz (npr. upute prije plaćanja) */
  function alert(opts) {
    close();
    const overlay = document.createElement("div");
    overlay.className = "pastoral-modal-overlay";
    overlay.innerHTML = `
      <div class="pastoral-modal pastoral-modal--sm" role="dialog" aria-modal="true">
        <header class="pastoral-modal-head">
          <h2 class="pastoral-modal-title">${escapeHtml(opts.title || "Obavijest")}</h2>
          <button type="button" class="pastoral-modal-close">&times;</button>
        </header>
        <div class="pastoral-modal-body pastoral-modal-body--text">${opts.body}</div>
        <footer class="pastoral-modal-foot">
          <button type="button" class="btn btn-primary" data-modal-ok>U redu</button>
        </footer>
      </div>`;
    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";
    activeOverlay = overlay;
    const ok = () => {
      close();
      opts.onClose?.();
    };
    overlay.querySelector("[data-modal-ok]")?.addEventListener("click", ok);
    overlay.querySelector(".pastoral-modal-close")?.addEventListener("click", ok);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) ok();
    });
  }

  global.PastoralModal = {
    openForm,
    openDetail,
    confirm,
    confirmPromise,
    alert,
    close,
    escapeHtml,
  };
})(typeof window !== "undefined" ? window : global);
