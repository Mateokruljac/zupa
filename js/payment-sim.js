/**
 * Simulacija online plaćanja (demo) — nakane i stipendiji
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
   * @param {function} opts.onSuccess ({ paymentId, paidAt })
   * @param {function} [opts.onCancel]
   */
  function runSimulation(opts) {
    const amount = Number(opts.amount) || 0;
    const overlay = document.createElement("div");
    overlay.className = "payment-overlay";
    overlay.innerHTML = `
      <div class="payment-modal card" role="dialog" aria-labelledby="pay-title">
        <button type="button" class="payment-close" aria-label="Zatvori">&times;</button>
        <h2 id="pay-title" class="section-title">Plaćanje stipendija</h2>
        <p class="card-sub">${escapeHtml(opts.title || "Misna nakana")}</p>
        <p class="payment-amount">${amount.toFixed(2)} €</p>
        <form id="payment-sim-form" class="form-grid">
          <div class="form-group form-wide">
            <label>Broj kartice (demo)</label>
            <input type="text" id="pay-card" placeholder="4242 4242 4242 4242" maxlength="19" required />
          </div>
          <div class="form-group">
            <label>Vrijedi do</label>
            <input type="text" id="pay-exp" placeholder="12/28" required />
          </div>
          <div class="form-group">
            <label>CVV</label>
            <input type="text" id="pay-cvv" placeholder="123" maxlength="4" required />
          </div>
          <div class="form-group form-wide">
            <label>Ime na kartici</label>
            <input type="text" id="pay-name" placeholder="Ime Prezime" required />
          </div>
          <p class="card-sub payment-demo-note">Demo — nema stvarnog terećenja. Podaci se ne šalju na server.</p>
          <div class="payment-actions">
            <button type="button" class="btn btn-ghost" data-pay-cancel>Odustani</button>
            <button type="submit" class="btn btn-primary" id="pay-submit">Plati ${amount.toFixed(2)} €</button>
          </div>
        </form>
        <div id="payment-processing" class="payment-processing hidden">
          <p>Obrada plaćanja…</p>
          <div class="payment-spinner"></div>
        </div>
        <div id="payment-success" class="payment-success hidden">
          <p class="payment-success-icon">✓</p>
          <p><strong>Plaćanje uspješno</strong></p>
          <p class="card-sub" id="payment-ref-line"></p>
          <button type="button" class="btn btn-primary" id="pay-done-btn">Zatvori</button>
        </div>
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

    const form = overlay.querySelector("#payment-sim-form");
    const processing = overlay.querySelector("#payment-processing");
    const success = overlay.querySelector("#payment-success");

    form?.addEventListener("submit", (e) => {
      e.preventDefault();
      form.classList.add("hidden");
      processing.classList.remove("hidden");
      const paymentId = genRef();
      const paidAt = new Date().toISOString();
      setTimeout(() => {
        processing.classList.add("hidden");
        success.classList.remove("hidden");
        overlay.querySelector("#payment-ref-line").textContent = `Referenca: ${paymentId}`;
        overlay.querySelector("#pay-done-btn")?.addEventListener("click", () => {
          close();
          opts.onSuccess?.({ paymentId, paidAt, amount });
        }, { once: true });
      }, 1800);
    });

    setTimeout(() => overlay.querySelector("#pay-card")?.focus(), 100);
  }

  global.PastoralPayment = { runSimulation, genRef };
})(typeof window !== "undefined" ? window : global);
