/**
 * Ispis HTML-a u novom prozoru (župni listić, dokumenti).
 */
(function (global) {
  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function safeColor(value, fallback) {
    return /^#[0-9a-f]{6}$/i.test(String(value || "")) ? value : fallback;
  }

  function printHtml(html, title) {
    const w = window.open("", "_blank");
    if (!w) {
      alert("Omogućite skočne prozore za ispis.");
      return;
    }
    const settings = global.PastoralParish?.loadSettings?.() || {};
    const parish = esc(settings.name || "Župa");
    const place = esc([settings.city, settings.diocese].filter(Boolean).join(" · "));
    const pastor = esc(settings.pastor || "");
    const primary = safeColor(settings.primaryColor, "#5c2e3a");
    const accent = safeColor(settings.accentColor, "#b8922a");
    const issued = new Date().toLocaleDateString("hr-HR");
    w.document.write(
      `<!DOCTYPE html><html lang="hr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>${esc(title || "Ispis")}</title>
      <link rel="stylesheet" href="/static/css/print-document.css"><style>:root{--print-primary:${primary};--print-accent:${accent}}</style></head><body>
      <div class="print-toolbar no-print"><div class="print-toolbar__copy"><strong>${esc(title || "Ispis")}</strong><span>Pregled A4 dokumenta prije ispisa ili spremanja u PDF</span></div><div class="print-toolbar__actions"><button type="button" onclick="window.print()">Ispis / PDF</button><button type="button" onclick="window.close()">Zatvori</button></div></div>
      <article class="print-sheet"><header class="document-letterhead"><span class="document-mark" aria-hidden="true"></span><div class="document-parish"><strong>${parish}</strong><span>${place}</span></div><div class="document-meta"><strong>Župni dokument</strong><span>${esc(issued)}</span></div></header><main class="document-content">${html}</main><footer class="document-footer"><span>${pastor ? `<strong>${pastor}</strong> · ` : ""}${parish}</span><span>${esc(issued)}</span></footer></article>
      <script>setTimeout(function(){window.print();},350);<\/script></body></html>`
    );
    w.document.close();
  }

  global.PastoralPrint = { printHtml, esc };
})(typeof window !== "undefined" ? window : global);
