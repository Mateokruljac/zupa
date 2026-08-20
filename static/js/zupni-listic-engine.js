/**
 * Župni listić — minimalni kontroler (pregled na serveru, ostalo lokalno).
 */
(function (global) {
  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function clone(v) {
    return JSON.parse(JSON.stringify(v));
  }

  function weekStartFrom(iso) {
    const d = new Date((iso || new Date().toISOString().slice(0, 10)) + "T12:00:00");
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    return d.toISOString().slice(0, 10);
  }

  function printHtml(html, title) {
    if (global.PastoralPrint?.printHtml) {
      global.PastoralPrint.printHtml(html, title);
      return;
    }
    const w = window.open("", "_blank");
    if (!w) return alert("Omogućite skočne prozore za ispis.");
    w.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>${title || "Župni listić"}</title>
      <style>body{padding:24px;max-width:720px;margin:0 auto}</style></head><body>${html}</body></html>`);
    w.document.close();
    w.print();
  }

  function api() {
    return {
      getData: () => clone(global.PastoralApi?.getCache?.() || {}),
      action: (name, payload) => global.PastoralApi.action(name, payload),
    };
  }

  function migrate(data, defaultLayout) {
    if (!data.zupniListicLayout?.blocks?.length && defaultLayout) {
      data.zupniListicLayout = clone(defaultLayout);
    }
    if (!Array.isArray(data.zupniListicIssues)) data.zupniListicIssues = [];
    return data;
  }

  function blockCard(block, meta, i, n) {
    const esc = (s) =>
      String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/"/g, "&quot;");
    const showTitle = block.type !== "header" && block.type !== "footer";
    const canRemove = !meta.fixed && block.type === "custom_text";
    const body = meta.auto || block.type === "header"
      ? `<p class="card-sub listic-block-auto-hint">${esc(meta.desc)}</p>`
      : `<div class="listic-rte-host" data-block-body="${esc(block.id)}"></div>`;
    return `<article class="listic-block-card${block.enabled === false ? " is-disabled" : ""}" data-block-id="${esc(block.id)}">
      <div class="listic-block-card-head">
        <label class="listic-block-enable"><input type="checkbox" data-block-enabled="${esc(block.id)}" ${block.enabled !== false ? "checked" : ""} /><strong>${esc(meta.label)}</strong></label>
        <div class="listic-block-move">
          <button type="button" class="btn btn-ghost btn-sm" data-block-up="${esc(block.id)}" ${i === 0 ? "disabled" : ""}>↑</button>
          <button type="button" class="btn btn-ghost btn-sm" data-block-down="${esc(block.id)}" ${i === n - 1 ? "disabled" : ""}>↓</button>
          ${canRemove ? `<button type="button" class="btn btn-ghost btn-sm" data-block-del="${esc(block.id)}">×</button>` : ""}
        </div>
      </div>
      ${showTitle ? `<input type="text" class="listic-block-title-input" data-block-title="${esc(block.id)}" value="${esc(block.title || meta.label)}" />` : `<span class="listic-block-fixed-title">${esc(meta.label)}</span>`}
      ${body}
    </article>`;
  }

  function init(root) {
    const boot = JSON.parse($("#listic-initial-data")?.textContent || "{}");
    const types = boot.config?.blockTypes || {};
    const defLayout = () => clone(boot.config?.defaultLayout || { blocks: [] });
    const { getData, action } = api();

    let weekStart = root.dataset.weekStart || weekStartFrom();
    let editLayout = clone(boot.editLayout || defLayout());
    let savedLayout = clone(boot.savedLayout || defLayout());
    let editingId = null;
    let previewTimer;

    const builderEdit = $("#listic-builder-edit", root);
    const previewBox = $("#listic-preview", root);

    function readBody(id, scope) {
      const wrap = scope.querySelector(`[data-block-body="${id}"]`);
      if (!wrap) return null;
      return global.PastoralRichText?.getHtml?.(wrap) ?? wrap.value ?? "";
    }

    function readBlocks(builder, blocks) {
      const out = clone({ blocks }).blocks;
      out.forEach((b) => {
        const en = builder.querySelector(`[data-block-enabled="${b.id}"]`);
        if (en) b.enabled = en.checked;
        const ti = builder.querySelector(`[data-block-title="${b.id}"]`);
        if (ti) b.title = ti.value;
        const body = readBody(b.id, builder);
        if (body !== null) b.body = body;
      });
      return out;
    }

    function mountRte(builder, blocks, onEdit) {
      if (!global.PastoralRichText) return;
      builder.querySelectorAll("[data-block-body]").forEach((wrap) => {
        const b = blocks.find((x) => x.id === wrap.dataset.blockBody);
        global.PastoralRichText.mount(wrap, {
          html: b?.body || "",
          placeholder: "Upišite tekst…",
          onChange: onEdit,
        });
      });
    }

    function paintBuilder(builder, blocks, onEdit) {
      if (!builder) return;
      builder.innerHTML = blocks.map((b, i) => blockCard(b, types[b.type] || { label: b.type, desc: "" }, i, blocks.length)).join("");
      mountRte(builder, blocks, onEdit);
    }

    function schedulePreview() {
      clearTimeout(previewTimer);
      previewTimer = setTimeout(updatePreview, 250);
    }

    async function updatePreview() {
      if (!previewBox) return;
      editLayout = { blocks: readBlocks(builderEdit, editLayout.blocks) };
      try {
        const res = await action("render_listic_preview", { layout: editLayout, weekStart });
        previewBox.innerHTML = res.html || "";
      } catch {
        previewBox.innerHTML = "<p class=\"card-sub\">Pregled nije dostupan.</p>";
      }
    }

    function switchTab(tab) {
      root.querySelectorAll(".listic-tab").forEach((b) => b.classList.toggle("is-active", b.dataset.tab === tab));
      root.querySelectorAll(".listic-panel").forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== tab));
      if (tab === "edit") updatePreview();
    }

    function bindBuilder(builder, getBlocks, setBlocks, onEdit) {
      builder.addEventListener("input", (e) => {
        if (e.target.matches("[data-block-title], [data-block-enabled]")) onEdit?.();
      });
      builder.addEventListener("click", (e) => {
        const up = e.target.closest("[data-block-up]");
        const down = e.target.closest("[data-block-down]");
        const del = e.target.closest("[data-block-del]");
        let blocks = readBlocks(builder, getBlocks());
        if (up) {
          const i = blocks.findIndex((b) => b.id === up.dataset.blockUp);
          if (i > 0) [blocks[i - 1], blocks[i]] = [blocks[i], blocks[i - 1]];
        } else if (down) {
          const i = blocks.findIndex((b) => b.id === down.dataset.blockDown);
          if (i >= 0 && i < blocks.length - 1) [blocks[i + 1], blocks[i]] = [blocks[i], blocks[i + 1]];
        } else if (del) {
          blocks = blocks.filter((b) => b.id !== del.dataset.blockDel);
        } else return;
        setBlocks(blocks);
        paintBuilder(builder, blocks, onEdit);
        onEdit?.();
      });
    }

    bindBuilder(
      builderEdit,
      () => editLayout.blocks,
      (blocks) => { editLayout = { blocks }; },
      schedulePreview
    );

    mountRte(builderEdit, editLayout.blocks, schedulePreview);

    root.querySelectorAll(".listic-tab").forEach((b) => b.addEventListener("click", () => switchTab(b.dataset.tab)));

    $("#listic-week-start", root)?.addEventListener("change", (e) => {
      weekStart = e.target.value || weekStartFrom();
      updatePreview();
    });

    root.querySelectorAll("[data-add-text-block]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const block = { id: `blk_${Date.now().toString(36).slice(-6)}`, type: "custom_text", enabled: true, title: "Nova sekcija", body: "" };
        editLayout = { blocks: [...readBlocks(builderEdit, editLayout.blocks), block] };
        paintBuilder(builderEdit, editLayout.blocks, schedulePreview);
        updatePreview();
      });
    });

    $("#listic-print-btn", root)?.addEventListener("click", async () => {
      const res = await action("render_listic_preview", { layout: { blocks: readBlocks(builderEdit, editLayout.blocks) }, weekStart });
      printHtml(res.html, `Župni listić ${weekStart}`);
    });

    $("#listic-save-issue", root)?.addEventListener("click", async () => {
      const ws = $("#listic-week-start", root)?.value || weekStart;
      await action("upsert_listic_issue", {
        issue: {
          id: editingId || undefined,
          weekStart: ws,
          status: "izdan",
          layoutSnapshot: { blocks: readBlocks(builderEdit, editLayout.blocks) },
        },
      });
      location.href = location.pathname + "?tab=history";
    });

    $("#listic-cancel-edit", root)?.addEventListener("click", () => {
      editingId = null;
      $("#listic-cancel-edit", root)?.classList.add("hidden");
      editLayout = clone(boot.editLayout || defLayout());
      $("#listic-week-start", root).value = root.dataset.weekStart || weekStartFrom();
      paintBuilder(builderEdit, editLayout.blocks, schedulePreview);
      updatePreview();
    });

    $("#listic-history-body", root)?.addEventListener("click", (e) => {
      const view = e.target.closest("[data-listic-view]");
      const edit = e.target.closest("[data-listic-edit]");
      const print = e.target.closest("[data-listic-print-id]");
      const del = e.target.closest("[data-listic-del]");
      const issues = getData().zupniListicIssues || [];
      if (view) {
        const issue = issues.find((x) => x.id === view.dataset.listicView);
        if (issue) global.PastoralModal?.openDetail?.({ title: issue.title, body: `<div class="listic-preview">${issue.renderedHtml || ""}</div>`, size: "xl" });
      }
      if (edit) {
        const issue = issues.find((x) => x.id === edit.dataset.listicEdit);
        if (!issue) return;
        editingId = issue.id;
        weekStart = issue.weekStart || weekStartFrom();
        editLayout = clone(issue.layoutSnapshot || savedLayout);
        $("#listic-week-start", root).value = weekStart;
        $("#listic-cancel-edit", root)?.classList.remove("hidden");
        paintBuilder(builderEdit, editLayout.blocks, schedulePreview);
        switchTab("edit");
        updatePreview();
      }
      if (print) {
        const issue = issues.find((x) => x.id === print.dataset.listicPrintId);
        if (issue?.renderedHtml) printHtml(issue.renderedHtml, issue.title);
      }
      if (del && confirm("Obrisati listić?")) {
        action("delete_listic_issue", { id: del.dataset.listicDel }).then(() => location.reload());
      }
    });

    if (new URLSearchParams(location.search).get("tab") === "history") switchTab("history");
  }

  function mountZupniListicPage(root) {
    if (root) init(root);
  }

  document.addEventListener("DOMContentLoaded", () => {
    global.PastoralApi?.ensureLoaded?.().catch(() => {});
    const root = document.getElementById("page-root");
    if (root?.dataset.djangoPage) init(root);
  });

  global.PastoralZupniListic = { migrate, mountZupniListicPage, weekStartFrom, printHtml };
})(window);
