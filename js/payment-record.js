/**
 * Evidencija uplate stipendija — gotovina ili žiro (bez kartice)
 */
(function (global) {
  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function genRef() {
    return `PAY-${Date.now().toString(36).toUpperCase().slice(-8)}`;
  }

  /**
   * @param {object} opts
   * @param {number} opts.amount
   * @param {string} opts.title
   * @param {string} [opts.subtitle]
   * @param {function} opts.onSuccess ({ paymentId, paidAt, amount, method })
   * @param {function} [opts.onCancel]
   */
  function recordPayment(opts) {
    const amount = Number(opts.amount) || 0;
    const overlay = document.createElement("div");
    overlay.className = "payment-overlay";
    overlay.innerHTML = `
      <div class="payment-modal card" role="dialog" aria-labelledby="pay-title">
        <button type="button" class="payment-close" aria-label="Zatvori">&times;</button>
        <h2 id="pay-title" class="section-title">Evidencija uplate</h2>
        <p class="card-sub">${escapeHtml(opts.title || "Misna nakana")}</p>
        ${opts.subtitle ? `<p class="card-sub">${escapeHtml(opts.subtitle)}</p>` : ""}
        <p class="payment-amount">${amount.toFixed(2)} €</p>
        <form id="payment-record-form" class="form-grid">
          <div class="form-group form-wide">
            <label>Način uplate</label>
            <select name="method" required>
              <option value="gotovina">Gotovina</option>
              <option value="žiro">Žiro račun</option>
            </select>
          </div>
          <p class="card-sub payment-demo-note">Uplata se bilježi u evidenciji župe — nema online terećenja.</p>
          <div class="payment-actions">
            <button type="button" class="btn btn-ghost" data-pay-cancel>Odustani</button>
            <button type="submit" class="btn btn-primary">Potvrdi uplatu</button>
          </div>
        </form>
      </div>`;

    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";

    function close() {
      overlay.remove();
      document.body.style.overflow = "";
      opts.onCancel?.();
    }

    overlay.querySelector(".payment-close")?.addEventListener("click", close);
    overlay.querySelector("[data-pay-cancel]")?.addEventListener("click", close);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
    });

    overlay.querySelector("#payment-record-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      const method = overlay.querySelector('[name="method"]')?.value || "gotovina";
      const paymentId = genRef();
      const paidAt = new Date().toISOString();
      close();
      opts.onSuccess?.({ paymentId, paidAt, amount, method });
    });

    setTimeout(() => overlay.querySelector('[name="method"]')?.focus(), 100);
  }

  global.PastoralPayment = { recordPayment, genRef };
})(typeof window !== "undefined" ? window : global);
