/**
 * Profesionalne KPI kartice — tonovi boja bez dodatnih animacija
 */
(function (global) {
  const TONES = ["liturgy", "finance", "sacrament", "pastoral", "alert", "success", "neutral", "accent"];

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function classes(tone, opts = {}) {
    const t = TONES.includes(tone) ? tone : "neutral";
    let c = `card kpi-card kpi-tone--${t}`;
    if (opts.link) c += " kpi-card--link";
    return c;
  }

  function sectionClass(tone) {
    const t = TONES.includes(tone) ? tone : "neutral";
    return `card card-section--${t}`;
  }

  /**
   * @param {{ tone?: string, label: string, value: string|number, sub?: string, href?: string }} o
   */
  function item(o) {
    const inner = `<p class="card-label">${esc(o.label)}</p><p class="card-value">${esc(o.value)}</p>${
      o.sub ? `<p class="card-sub">${esc(o.sub)}</p>` : ""
    }`;
    const cls = classes(o.tone || "neutral", { link: !!o.href });
    if (o.href) return `<a href="${o.href}" class="${cls}">${inner}</a>`;
    return `<article class="${cls}">${inner}</article>`;
  }

  function row(items, opts = {}) {
    const html = (items || []).map((x) => (typeof x === "string" ? x : item(x))).join("");
    const rowCls = ["kpi-row", "kpi-row--pro", opts.rowClass].filter(Boolean).join(" ");
    const inner = `<div class="${rowCls}">${html}</div>`;
    if (opts.noStack) return inner;
    const stackCls = ["page-kpi-stack", opts.stackClass].filter(Boolean).join(" ");
    const noStagger = opts.dataNoStagger !== false ? ' data-no-stagger' : "";
    return `<div class="${stackCls}"${noStagger}>${inner}</div>`;
  }

  function stack(innerHtml) {
    return `<div class="page-kpi-stack">${innerHtml || ""}</div>`;
  }

  function hero(o) {
    const t = TONES.includes(o.tone) ? o.tone : "neutral";
    return `<section class="page-hero page-hero--${t}" data-no-stagger>
      <h2 class="page-hero-title">${esc(o.title)}</h2>
      ${o.desc ? `<p class="page-hero-desc">${esc(o.desc)}</p>` : ""}
    </section>`;
  }

  global.PastoralKpi = { TONES, classes, sectionClass, item, row, stack, hero, esc };
})(typeof window !== "undefined" ? window : global);
