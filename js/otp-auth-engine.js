/**
 * Prijava s OTP kodom — Netlify Function ili EmailJS
 */
(function (global) {
  const PENDING_KEY = "pastoral_otp_pending";

  function cfg() {
    return global.PastoralOtpMailConfig || {};
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function parishSettings() {
    return global.PastoralParish?.loadSettings?.() || {};
  }

  function emailjsReady() {
    const c = cfg().emailjs || {};
    return !!(c.publicKey && c.serviceId && c.templateId);
  }

  function resolveProvider() {
    const c = cfg();
    if (c.provider === "demo" || c.demoAlwaysShowOnPortal) return "demo";
    if (c.provider === "emailjs") return "emailjs";
    if (c.provider === "netlify") return "netlify";
    if (typeof location === "undefined") return "demo";
    const host = location.hostname;
    const port = location.port;
    if (host.includes("netlify.app") || host.endsWith(".netlify.live")) return "netlify";
    if (c.useNetlifyDevLocally && (port === "8888" || port === "8889")) return "netlify";
    if (emailjsReady()) return "emailjs";
    return "demo";
  }

  function resolveNetlifyEndpoint() {
    const c = cfg();
    if (c.netlifyFunctionUrl) return c.netlifyFunctionUrl;
    if (typeof location === "undefined") return null;
    const base = location.origin;
    return `${base}/.netlify/functions/send-otp`;
  }

  async function sendViaNetlify(opts) {
    const endpoint = resolveNetlifyEndpoint();
    if (!endpoint) return { ok: false, reason: "no_endpoint", demoCode: opts.otp };

    const s = parishSettings();
    const recipient = cfg().otpRecipient || "mateokruljac123@gmail.com";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          otp: opts.otp,
          userEmail: opts.userEmail,
          userRole: opts.roleLabel,
          parishName: s.shortName || s.name || "Pastoral",
          ttlMinutes: opts.ttlMinutes || 10,
          primaryColor: s.primaryColor || "#5c2e3a",
          accentColor: s.accentColor || "#b8922a",
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        return {
          ok: false,
          reason: data.error || "netlify_failed",
          detail: data,
          recipient,
          demoCode: data.devOtp || opts.otp,
        };
      }
      return {
        ok: true,
        recipient: data.recipient || recipient,
        simulated: !!data.simulated,
        demoCode: data.simulated && data.devOtp ? data.devOtp : null,
        message: data.message,
      };
    } catch (err) {
      return { ok: false, reason: "network", detail: err.message, recipient, demoCode: opts.otp };
    }
  }

  async function sendViaEmailjs(opts) {
    const c = cfg();
    const recipient = c.otpRecipient || "mateokruljac123@gmail.com";
    const html = buildOtpEmailHtml(opts);
    const text = buildPlainText(opts);
    const ej = c.emailjs;
    const params = {
      to_email: recipient,
      otp_code: opts.otp,
      user_email: opts.userEmail,
      user_role: opts.roleLabel,
      parish_name: parishSettings().shortName || parishSettings().name || "Pastoral",
      expires_minutes: String(opts.ttlMinutes || 10),
      message_html: html,
      message_text: text,
      subject: `Pastoral — kod za prijavu: ${opts.otp}`,
    };

    const res = await fetch("https://api.emailjs.com/api/v1.0/email/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        service_id: ej.serviceId,
        template_id: ej.templateId,
        user_id: ej.publicKey,
        template_params: params,
      }),
    });
    if (!res.ok) {
      const errText = await res.text();
      return { ok: false, reason: "send_failed", detail: errText, recipient, demoCode: opts.otp };
    }
    return { ok: true, recipient };
  }

  function generateCode(len) {
    const n = len || cfg().otpLength || 6;
    let code = "";
    for (let i = 0; i < n; i++) code += Math.floor(Math.random() * 10);
    return code;
  }

  function savePending(payload) {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify(payload));
  }

  function loadPending() {
    try {
      const raw = sessionStorage.getItem(PENDING_KEY);
      if (!raw) return null;
      const p = JSON.parse(raw);
      if (p.expiresAt && Date.now() > p.expiresAt) {
        clearPending();
        return null;
      }
      return p;
    } catch {
      return null;
    }
  }

  function clearPending() {
    sessionStorage.removeItem(PENDING_KEY);
  }

  function buildOtpEmailHtml(opts) {
    const s = parishSettings();
    const primary = s.primaryColor || "#5c2e3a";
    const accent = s.accentColor || "#b8922a";
    const parish = s.shortName || s.name || "Pastoral";
    const otp = esc(opts.otp);
    const userEmail = esc(opts.userEmail);
    const role = esc(opts.roleLabel);
    const minutes = opts.ttlMinutes || 10;

    return `<!DOCTYPE html>
<html lang="hr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#f4f0ec;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f0ec;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:520px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e8e0d8;box-shadow:0 8px 28px rgba(92,46,58,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg, ${primary} 0%, ${accent} 120%);padding:28px 32px;text-align:center;">
            <p style="margin:0 0 6px;font-size:11px;letter-spacing:0.14em;text-transform:uppercase;color:rgba(255,255,255,0.85);">Župni ured</p>
            <h1 style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:26px;font-weight:600;color:#ffffff;">${esc(parish)}</h1>
            <p style="margin:10px 0 0;font-size:14px;color:rgba(255,255,255,0.9);">Sigurnosna prijava — jednokratni kod</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 28px 24px;">
            <p style="margin:0 0 16px;font-size:15px;line-height:1.55;color:#3d3835;">Netko se pokušava prijaviti u <strong>Pastoral</strong> administraciju. Unesite kod ispod na stranici za prijavu.</p>
            <table role="presentation" width="100%" style="margin:20px 0;background:#faf8f6;border-radius:10px;border-left:4px solid ${accent};">
              <tr><td style="padding:20px 24px;text-align:center;">
                <p style="margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;color:#7a726c;">Vaš kod (OTP)</p>
                <p style="margin:0;font-family:ui-monospace,'Consolas',monospace;font-size:36px;font-weight:700;letter-spacing:0.22em;color:${primary};">${otp}</p>
              </td></tr>
            </table>
            <table role="presentation" width="100%" style="font-size:14px;color:#5c5652;">
              <tr><td style="padding:8px 0;border-bottom:1px solid #eee8e2;"><strong>E-mail prijave:</strong></td><td style="padding:8px 0;border-bottom:1px solid #eee8e2;text-align:right;">${userEmail}</td></tr>
              <tr><td style="padding:8px 0;border-bottom:1px solid #eee8e2;"><strong>Uloga:</strong></td><td style="padding:8px 0;border-bottom:1px solid #eee8e2;text-align:right;">${role}</td></tr>
              <tr><td style="padding:8px 0;"><strong>Vrijedi:</strong></td><td style="padding:8px 0;text-align:right;">${minutes} minuta</td></tr>
            </table>
            <p style="margin:24px 0 0;font-size:13px;line-height:1.5;color:#8a827c;">Ako niste zatražili prijavu, zanemarite ovu poruku i obavijestite župni ured.</p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 24px;background:#faf8f6;border-top:1px solid #eee8e2;text-align:center;">
            <p style="margin:0;font-size:12px;color:#9a928c;">Pastoral · župna administracija</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
  }

  function buildPlainText(opts) {
    return [
      `Pastoral — kod za prijavu: ${opts.otp}`,
      ``,
      `E-mail: ${opts.userEmail}`,
      `Uloga: ${opts.roleLabel}`,
      `Vrijedi ${opts.ttlMinutes || 10} minuta.`,
    ].join("\n");
  }

  async function sendOtpEmail(opts) {
    const recipient = cfg().otpRecipient || "mateokruljac123@gmail.com";
    const provider = resolveProvider();

    if (provider === "netlify") {
      const result = await sendViaNetlify(opts);
      if (result.ok) return result;
      if (cfg().demoShowCodeWhenNoEmailjs) {
        return { ok: true, recipient, simulated: true, demoCode: result.demoCode || opts.otp, message: "Netlify nedostupan — demo kod" };
      }
      return result;
    }

    if (provider === "emailjs") {
      try {
        return await sendViaEmailjs(opts);
      } catch (err) {
        return { ok: false, reason: "network", detail: err.message, recipient, demoCode: opts.otp };
      }
    }

    return { ok: false, reason: "no_provider", recipient, demoCode: opts.otp };
  }

  function getTemplateForEmailJsDashboard() {
    return buildOtpEmailHtml({
      otp: "123456",
      userEmail: "ured@zupa-bdm-sb.hr",
      roleLabel: "Župnik",
      ttlMinutes: 10,
    });
  }

  function mountLoginUi(root, api) {
    if (!root) return;
    const recipient = cfg().otpRecipient || "mateokruljac123@gmail.com";
    const pending = loadPending();

    root.innerHTML = `
      <div id="login-step-credentials" class="login-step ${pending ? "hidden" : ""}">
        <p class="login-otp-hint card-sub">Demo prijava: nakon klika prikazat će se <strong>jednokratni kod na ovoj stranici</strong> (produkcija: e-mail na ${esc(recipient)}).</p>
      </div>
      <div id="login-step-otp" class="login-step login-otp-panel ${pending ? "" : "hidden"}">
        <div class="login-otp-portal card" role="status" aria-live="polite">
          <p class="login-otp-portal-label">Vaš kod za prijavu (demo)</p>
          <p class="login-otp-portal-code" id="login-otp-portal-code">——</p>
          <p class="login-otp-portal-sub card-sub">Unesite isti kod u polje ispod. Vrijedi ${cfg().otpTtlMinutes || 10} min.</p>
          <button type="button" class="btn btn-ghost btn-sm" id="login-otp-copy">Kopiraj kod</button>
        </div>
        <div class="form-group">
          <label for="login-otp-input">Upišite kod</label>
          <input type="text" id="login-otp-input" class="login-otp-input" inputmode="numeric" autocomplete="one-time-code" maxlength="8" placeholder="000000" />
        </div>
        <div id="login-otp-demo-box" class="login-otp-demo hidden" role="status"></div>
        <p id="login-otp-error" class="login-otp-error hidden"></p>
        <button type="button" class="btn btn-primary fx-btn-shine" style="width:100%" id="login-otp-verify">Potvrdi kod i uđi</button>
        <div class="login-otp-actions">
          <button type="button" class="btn btn-ghost btn-sm" id="login-otp-resend" disabled>Pošalji ponovo</button>
          <button type="button" class="btn btn-ghost btn-sm" id="login-otp-back">Promijeni e-mail</button>
        </div>
      </div>`;

    if (pending) showOtpStep(api, pending.code);
  }

  function showCredentialsStep() {
    document.getElementById("login-step-credentials")?.classList.remove("hidden");
    document.getElementById("login-step-otp")?.classList.add("hidden");
    const submit = document.getElementById("login-submit-btn");
    if (submit) {
      submit.textContent = "Prikaži kod za prijavu";
      submit.disabled = false;
    }
  }

  function showOtpStep(api, code) {
    document.getElementById("login-step-credentials")?.classList.add("hidden");
    document.getElementById("login-step-otp")?.classList.remove("hidden");
    const submit = document.getElementById("login-submit-btn");
    if (submit) submit.classList.add("hidden");

    const displayCode = code || loadPending()?.code || "";
    const portalCode = document.getElementById("login-otp-portal-code");
    if (portalCode) portalCode.textContent = displayCode;

    const copyBtn = document.getElementById("login-otp-copy");
    if (copyBtn) {
      copyBtn.onclick = async () => {
        try {
          await navigator.clipboard.writeText(displayCode);
          api.showToast("Kod kopiran");
        } catch {
          api.showToast("Kopiraj ručno");
        }
      };
    }

    const demoBox = document.getElementById("login-otp-demo-box");
    if (demoBox) {
      demoBox.classList.add("hidden");
      demoBox.innerHTML = "";
    }

    document.getElementById("login-otp-input")?.focus();
    startResendCooldown(api);
  }

  function startResendCooldown(api) {
    const btn = document.getElementById("login-otp-resend");
    if (!btn) return;
    const sec = cfg().resendCooldownSeconds || 60;
    const pending = loadPending();
    const sentAt = pending?.sentAt || 0;
    let left = Math.max(0, sec - Math.floor((Date.now() - sentAt) / 1000));

    function tick() {
      if (left > 0) {
        btn.disabled = true;
        btn.textContent = `Ponovo za ${left}s`;
        left--;
        setTimeout(tick, 1000);
      } else {
        btn.disabled = false;
        btn.textContent = "Pošalji ponovo";
      }
    }
    tick();
  }

  function setOtpError(msg) {
    const el = document.getElementById("login-otp-error");
    if (!el) return;
    if (msg) {
      el.textContent = msg;
      el.classList.remove("hidden");
    } else {
      el.classList.add("hidden");
      el.textContent = "";
    }
  }

  async function requestOtp(api) {
    const email = document.getElementById("login-email")?.value?.trim();
    const legacyRole = document.getElementById("login-role")?.value;
    if (!email) {
      api.showToast("Unesite e-mail");
      return;
    }
    if (api.validateGdpr && !api.validateGdpr()) return;

    const ROLE_LABELS = global.PastoralPermissions?.LEGACY_ROLE_LABELS || {
      zupnik: "Župnik",
      vikar: "Vikar",
      upravitelj: "Upravitelj",
      kateheta: "Kateheta",
    };
    const roleLabel = ROLE_LABELS[legacyRole] || legacyRole;
    const code = generateCode();
    const ttlMin = cfg().otpTtlMinutes || 10;
    const now = Date.now();

    const submit = document.getElementById("login-submit-btn");
    if (submit) {
      submit.disabled = true;
      submit.textContent = "Generiram kod…";
    }

    if (submit) {
      submit.disabled = false;
      submit.textContent = "Prikaži kod za prijavu";
    }

    savePending({
      code,
      email,
      legacyRole,
      expiresAt: now + ttlMin * 60 * 1000,
      sentAt: now,
      attempts: 0,
    });

    api.showToast("Kod je prikazan na portalu — unesite ga ispod");

    if (cfg().provider !== "demo") {
      sendOtpEmail({ otp: code, userEmail: email, roleLabel, ttlMinutes: ttlMin }).catch(() => {});
    }

    showOtpStep(api, code);
  }

  function verifyOtp(api) {
    const pending = loadPending();
    if (!pending) {
      setOtpError("Kod je istekao. Zatražite novi.");
      showCredentialsStep();
      return;
    }

    const input = (document.getElementById("login-otp-input")?.value || "").replace(/\D/g, "");
    const expected = String(pending.code || "");

    if (input.length < (cfg().otpLength || 6)) {
      setOtpError("Unesite cijeli kod.");
      return;
    }

    if (input !== expected) {
      pending.attempts = (pending.attempts || 0) + 1;
      savePending(pending);
      const maxA = cfg().maxAttempts || 5;
      if (pending.attempts >= maxA) {
        clearPending();
        setOtpError("Previše pogrešnih pokušaja. Zatražite novi kod.");
        showCredentialsStep();
        return;
      }
      setOtpError(`Netočan kod. Preostalo pokušaja: ${maxA - pending.attempts}`);
      return;
    }

    setOtpError("");
    clearPending();
    api.completeLogin({ email: pending.email, legacyRole: pending.legacyRole });
  }

  function initLoginFlow(api) {
    const mount = document.getElementById("login-otp-mount");
    if (mount) mountLoginUi(mount, api);

    const form = document.getElementById("login-form");
    if (!form) return;

    const submit = form.querySelector('button[type="submit"]');
    if (submit) {
      submit.id = "login-submit-btn";
      submit.textContent = loadPending() ? "" : "Prikaži kod za prijavu";
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (loadPending()) {
        verifyOtp(api);
      } else {
        requestOtp(api);
      }
    });

    document.getElementById("login-otp-verify")?.addEventListener("click", () => verifyOtp(api));
    document.getElementById("login-otp-back")?.addEventListener("click", () => {
      clearPending();
      setOtpError("");
      showCredentialsStep();
      if (submit) {
        submit.classList.remove("hidden");
        submit.textContent = "Prikaži kod za prijavu";
      }
    });
    document.getElementById("login-otp-resend")?.addEventListener("click", () => {
      clearPending();
      requestOtp(api);
    });

    document.getElementById("login-otp-input")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        verifyOtp(api);
      }
    });

    if (loadPending()) {
      const p = loadPending();
      showOtpStep(api, p?.code);
      if (submit) submit.classList.add("hidden");
    }
  }

  global.PastoralOtpAuth = {
    initLoginFlow,
    buildOtpEmailHtml,
    getTemplateForEmailJsDashboard,
    sendOtpEmail,
    emailjsReady,
    resolveProvider,
    resolveNetlifyEndpoint,
    clearPending,
    loadPending,
  };
})(typeof window !== "undefined" ? window : global);
