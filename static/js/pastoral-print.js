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

  function printHtml(html, title) {
    const w = window.open("", "_blank");
    if (!w) {
      alert("Omogućite skočne prozore za ispis.");
      return;
    }
    w.document.write(
      `<!DOCTYPE html><html lang="hr"><head><meta charset="utf-8"><title>${esc(title || "Ispis")}</title>
      <style>body{font-family:Georgia,serif;padding:40px;max-width:800px;margin:0 auto;color:#222}
      @media print{.no-print{display:none} body{padding:12px}}</style></head><body>${html}
      <p class="no-print" style="margin-top:2em"><button type="button" onclick="window.print()">Ispis</button></p>
      <script>setTimeout(function(){window.print();},300);<\/script></body></html>`
    );
    w.document.close();
  }

  global.PastoralPrint = { printHtml, esc };
})(typeof window !== "undefined" ? window : global);
