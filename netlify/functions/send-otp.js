/**
 * Netlify Function — slanje OTP e-pošte
 *
 * Varijable okruženja (Netlify → Site configuration → Environment variables):
 *   OTP_RECIPIENT          = mateokruljac123@gmail.com
 *   OTP_SIMULATE           = true   (default ako nema RESEND_API_KEY)
 *   OTP_EXPOSE_DEV_OTP     = true   (u simulaciji: vrati kod u JSON za demo UI)
 *   RESEND_API_KEY         = re_... (opcionalno — pravo slanje)
 *   RESEND_FROM            = Pastoral <onboarding@resend.dev>
 */
const { buildOtpEmailHtml, buildPlainText } = require("./lib/otp-email-html");

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

function json(statusCode, body) {
  return {
    statusCode,
    headers: CORS,
    body: JSON.stringify(body),
  };
}

function shouldSimulate() {
  if (process.env.RESEND_API_KEY) return false;
  const v = process.env.OTP_SIMULATE;
  if (v === "false" || v === "0") return false;
  return true;
}

async function sendViaResend({ to, subject, html, text }) {
  const from = process.env.RESEND_FROM || "Pastoral <onboarding@resend.dev>";
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: [to],
      subject,
      html,
      text,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Resend ${res.status}: ${err}`);
  }
  return res.json();
}

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers: CORS, body: "" };
  }

  if (event.httpMethod !== "POST") {
    return json(405, { ok: false, error: "Method not allowed" });
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return json(400, { ok: false, error: "Invalid JSON" });
  }

  const otp = String(body.otp || "").replace(/\D/g, "");
  const userEmail = String(body.userEmail || "").trim();
  const userRole = String(body.userRole || body.user_role || "—").trim();
  const parishName = String(body.parishName || body.parish_name || "Pastoral").trim();
  const ttlMinutes = Number(body.ttlMinutes || body.ttl_minutes) || 10;

  if (!otp || otp.length < 4) {
    return json(400, { ok: false, error: "Missing OTP code" });
  }

  const recipient = process.env.OTP_RECIPIENT || "mateokruljac123@gmail.com";
  const mailOpts = {
    otp,
    userEmail: userEmail || "—",
    userRole,
    parishName,
    ttlMinutes,
    primaryColor: body.primaryColor || "#5c2e3a",
    accentColor: body.accentColor || "#b8922a",
  };

  const subject = `Pastoral — kod za prijavu: ${otp}`;
  const html = buildOtpEmailHtml(mailOpts);
  const text = buildPlainText(mailOpts);

  const simulate = shouldSimulate();
  const exposeDev = process.env.OTP_EXPOSE_DEV_OTP === "true" || process.env.OTP_EXPOSE_DEV_OTP === "1";

  if (simulate) {
    console.log("[Pastoral OTP SIMULATE]", {
      to: recipient,
      otp,
      userEmail,
      userRole,
      parishName,
      ttlMinutes,
      htmlPreview: text,
    });

    return json(200, {
      ok: true,
      simulated: true,
      recipient,
      message: "E-mail simuliran (Netlify Functions log). Postavite RESEND_API_KEY za pravo slanje.",
      ...(exposeDev ? { devOtp: otp } : {}),
    });
  }

  try {
    await sendViaResend({ to: recipient, subject, html, text });
    return json(200, {
      ok: true,
      simulated: false,
      recipient,
      message: "E-mail poslan.",
    });
  } catch (err) {
    console.error("[Pastoral OTP send error]", err);
    return json(500, {
      ok: false,
      error: err.message || "Send failed",
      recipient,
      ...(exposeDev ? { devOtp: otp } : {}),
    });
  }
};
