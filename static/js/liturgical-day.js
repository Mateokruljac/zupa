/**
 * Dopuna liturgijskog kartona ako server nije uspio učitati čitanja (HILP).
 */
(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const card = document.querySelector(".lit-day-card[data-lit-day]");
    if (!card || card.querySelector(".lit-readings-block")) return;

    const iso = card.dataset.litDay;
    if (!iso) return;

    fetch(`/api/liturgical/day/${iso}/`, { credentials: "same-origin" })
      .then((res) => (res.ok ? res.json() : null))
      .then((day) => {
        if (!day?.readings?.length) return;
        const wrap = document.createElement("details");
        wrap.className = "lit-readings-block";
        wrap.innerHTML =
          `<summary class="lit-readings-summary">` +
          `<span class="lit-readings-chev" aria-hidden="true"></span>` +
          `<span class="lit-readings-title">Čitanja</span>` +
          `<span class="badge">${day.readings.length}</span>` +
          `</summary>` +
          `<div class="lit-readings-body">` +
          day.readings
            .map(
              (r) =>
                `<details class="lit-reading-item">` +
                `<summary class="lit-reading-summary">${esc(r.label)}</summary>` +
                `<div class="lit-reading-text">${esc(r.text)}</div>` +
                `</details>`
            )
            .join("") +
          `</div>`;
        const empty = card.querySelector(".empty-state, .card-sub");
        if (empty) empty.remove();
        card.appendChild(wrap);
      })
      .catch(() => {});
  });

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
})();
