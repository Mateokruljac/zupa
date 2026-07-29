/**
 * Django OTP prijava — fetch na /api/otp/send/
 */
(function (global) {
  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute("content");
    const inp = document.querySelector("#login-form [name=csrfmiddlewaretoken]");
    return inp ? inp.value : "";
  }

  function showStep(step) {
    const credentials = document.getElementById("login-step-credentials");
    const otp = document.getElementById("login-step-otp");
    if (credentials) credentials.classList.toggle("hidden", step !== "credentials");
    if (otp) otp.classList.toggle("hidden", step !== "otp");
  }

  function setCredentialsError(msg) {
    const el = document.getElementById("login-credentials-error");
    if (!el) return;
    if (msg) {
      el.textContent = msg;
      el.classList.remove("hidden");
    } else {
      el.textContent = "";
      el.classList.add("hidden");
    }
  }

  function setStatus(msg) {
    const el = document.getElementById("login-otp-status");
    if (!el) return;
    if (msg) {
      el.textContent = msg;
      el.classList.remove("hidden");
    } else {
      el.textContent = "";
      el.classList.add("hidden");
    }
  }

  async function requestOtp(form) {
    const submit = form.querySelector('button[type="submit"]');
    const email = form.querySelector('[name="email"]')?.value?.trim();
    const role = form.querySelector('[name="role"]')?.value;
    const gdpr = form.querySelector('[name="gdpr_consent"]')?.checked;

    setCredentialsError("");

    if (!email) {
      setCredentialsError("Unesite e-mail.");
      return;
    }
    if (!gdpr) {
      setCredentialsError("Potrebna je suglasnost za obradu podataka (GDPR).");
      return;
    }

    if (submit) {
      submit.disabled = true;
      submit.textContent = "Šaljem kod…";
    }

    try {
      const res = await fetch("/api/otp/send/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        credentials: "same-origin",
        body: JSON.stringify({
          email,
          role,
          gdpr_consent: gdpr,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        const detail = data.detail ? `: ${data.detail}` : "";
        setCredentialsError(
          data.error === "invalid_input"
            ? "Provjerite unesene podatke."
            : `Nije moguće poslati e-mail${detail}. SMTP mora ići na port 1025 (Mailhog web sučelje je na 8025).`
        );
        return;
      }

      showStep("otp");
      setStatus(data.message || "Kod je poslan. Unesite ga ispod.");
      document.getElementById("login-otp-input")?.focus();
    } catch (err) {
      setCredentialsError(`Mrežna greška: ${err.message}`);
    } finally {
      if (submit) {
        submit.disabled = false;
        submit.textContent = "Pošalji kod za prijavu";
      }
    }
  }

  function init() {
    const form = document.getElementById("login-form");
    if (!form || form.dataset.otpJs !== "1") return;

    if (document.body.dataset.otpMode === "1") {
      showStep("otp");
      return;
    }

    showStep("credentials");

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      requestOtp(form);
    });

    document.getElementById("login-otp-back")?.addEventListener("click", () => {
      setStatus("");
      setCredentialsError("");
      showStep("credentials");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  global.PastoralOtpLogin = { requestOtp };
})(typeof window !== "undefined" ? window : global);
