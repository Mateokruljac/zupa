/**
 * Legacy loader — javni obrasci su na Django rutama (/public/…).
 */
(function () {
  if (location.pathname.startsWith("/public")) return;
  const root = document.getElementById("public-root");
  if (root) {
    root.innerHTML = `
      <section class="card" style="max-width:480px;margin:2rem auto;padding:24px;text-align:center">
        <h2>Javni obrasci</h2>
        <p class="card-sub">Koristite Django server:</p>
        <p><a href="/public/">/public/</a></p>
      </section>`;
  }
})();
