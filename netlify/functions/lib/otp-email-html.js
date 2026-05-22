/**
 * HTML predložak OTP poruke (isti vizual kao u aplikaciji)
 */
function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildOtpEmailHtml(opts) {
  const primary = opts.primaryColor || "#5c2e3a";
  const accent = opts.accentColor || "#b8922a";
  const parish = esc(opts.parishName || "Pastoral");
  const otp = esc(opts.otp);
  const userEmail = esc(opts.userEmail);
  const role = esc(opts.userRole);
  const minutes = opts.ttlMinutes || 10;

  return `<!DOCTYPE html>
<html lang="hr">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f4f0ec;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f0ec;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:520px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e8e0d8;">
        <tr>
          <td style="background:linear-gradient(135deg, ${primary} 0%, ${accent} 120%);padding:28px 32px;text-align:center;">
            <p style="margin:0 0 6px;font-size:11px;letter-spacing:0.14em;text-transform:uppercase;color:rgba(255,255,255,0.85);">Župni ured</p>
            <h1 style="margin:0;font-family:Georgia,serif;font-size:26px;color:#fff;">${parish}</h1>
            <p style="margin:10px 0 0;font-size:14px;color:rgba(255,255,255,0.9);">Sigurnosna prijava — jednokratni kod</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 28px 24px;">
            <p style="margin:0 0 16px;font-size:15px;line-height:1.55;color:#3d3835;">Netko se pokušava prijaviti u <strong>Pastoral</strong>. Unesite kod na stranici za prijavu.</p>
            <table role="presentation" width="100%" style="margin:20px 0;background:#faf8f6;border-radius:10px;border-left:4px solid ${accent};">
              <tr><td style="padding:20px 24px;text-align:center;">
                <p style="margin:0 0 8px;font-size:12px;text-transform:uppercase;color:#7a726c;">Vaš kod (OTP)</p>
                <p style="margin:0;font-family:monospace;font-size:36px;font-weight:700;letter-spacing:0.22em;color:${primary};">${otp}</p>
              </td></tr>
            </table>
            <table role="presentation" width="100%" style="font-size:14px;color:#5c5652;">
              <tr><td style="padding:8px 0;border-bottom:1px solid #eee8e2;"><strong>E-mail prijave:</strong></td><td style="padding:8px 0;border-bottom:1px solid #eee8e2;text-align:right;">${userEmail}</td></tr>
              <tr><td style="padding:8px 0;border-bottom:1px solid #eee8e2;"><strong>Uloga:</strong></td><td style="padding:8px 0;border-bottom:1px solid #eee8e2;text-align:right;">${role}</td></tr>
              <tr><td style="padding:8px 0;"><strong>Vrijedi:</strong></td><td style="padding:8px 0;text-align:right;">${minutes} minuta</td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px;background:#faf8f6;text-align:center;font-size:12px;color:#9a928c;">Pastoral · župna administracija</td>
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
    `E-mail: ${opts.userEmail}`,
    `Uloga: ${opts.userRole}`,
    `Vrijedi ${opts.ttlMinutes || 10} minuta.`,
  ].join("\n");
}

module.exports = { buildOtpEmailHtml, buildPlainText };
