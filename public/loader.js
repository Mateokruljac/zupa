/**
 * Učitavanje skripti za javni portal (file:// + http)
 */
(function () {
  const root = document.getElementById("public-root");

  function showError(msg, detail) {
    if (!root) return;
    root.innerHTML = `
      <section class="card public-error-card" style="max-width:520px;margin:2rem auto">
        <h2 style="margin-top:0">Portal se ne može učitati</h2>
        <p>${msg}</p>
        ${detail ? `<pre class="public-error-path">${detail}</pre>` : ""}
        <p class="card-sub"><strong>Ispravno:</strong> mapa <code>pastoral-zupa/public/index.html</code> (ne <code>pages/public</code>).</p>
        <p class="card-sub">U mapi projekta pokrenite:</p>
        <pre style="background:var(--bg);padding:12px;border-radius:8px">cd pastoral-zupa\nnpx serve -l 3340</pre>
        <p>Zatim: <a href="http://localhost:3340/public/index.html">http://localhost:3340/public/index.html</a></p>
      </section>`;
  }

  function projectRoot() {
    const href = decodeURI(location.href).replace(/\\/g, "/");
    const pub = href.indexOf("/public/");
    if (pub >= 0) return href.slice(0, pub + 1);
    return null;
  }

  function asset(rel) {
    const r = projectRoot();
    return r ? r + String(rel).replace(/^\//, "") : `../${rel}`;
  }

  const SCRIPTS = [
    "js/path-base.js",
    "js/parish-config.js",
    "js/theme-picker.js",
    "js/data-seed.js",
    "js/gdpr-engine.js",
    "js/modal-kit.js",
    "js/public-forms.js",
    "js/public-app.js",
  ];

  const rootPath = projectRoot();
  if (location.protocol === "file:" && !rootPath) {
    showError(
      "Otvorili ste krivu putanju ili preglednik blokira lokalne datoteke.",
      location.href
    );
    return;
  }

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = asset("css/styles.css");
  document.head.appendChild(link);

  let i = 0;
  function loadNext() {
    if (i >= SCRIPTS.length) return;
    const s = document.createElement("script");
    s.src = asset(SCRIPTS[i++]);
    s.onerror = () =>
      showError(
        "Nije učitana skripta: " + SCRIPTS[i - 1],
        "Koristite lokalni server (npx serve), ne direktno otvaranje datoteke."
      );
    s.onload = loadNext;
    document.head.appendChild(s);
  }
  loadNext();
})();
