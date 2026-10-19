/**
 * Župni listić — Ovaj tjedan / Sastavi / Povijest.
 *
 * Urednički fokus: obavijesti i slobodni tekst.
 * Auto-blokovi (mise, nakane…) samo u „Prilagodi sastav”.
 */
(function (global) {
  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function clone(v) {
    return JSON.parse(JSON.stringify(v));
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function weekStartFrom(iso) {
    const d = new Date((iso || new Date().toISOString().slice(0, 10)) + "T12:00:00");
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    return d.toISOString().slice(0, 10);
  }

  function weekEndFrom(start) {
    const d = new Date(start + "T12:00:00");
    d.setDate(d.getDate() + 6);
    return d.toISOString().slice(0, 10);
  }

  function fmtShort(iso) {
    if (!iso) return "—";
    return new Date(iso + "T12:00:00").toLocaleDateString("hr-HR", {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
  }

  function swalAlert(title, text, icon) {
    if (global.Swal) {
      return global.Swal.fire({
        title: title || "Obavijest",
        text: text || "",
        icon: icon || "info",
        confirmButtonText: "U redu",
        heightAuto: false,
      });
    }
    global.alert(text || title);
    return Promise.resolve();
  }

  function swalConfirm(title, text, confirmButtonText) {
    if (global.Swal) {
      return global.Swal.fire({
        title: title,
        text: text || "",
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: confirmButtonText || "Obriši",
        cancelButtonText: "Odustani",
        reverseButtons: true,
        focusCancel: true,
        heightAuto: false,
      }).then((result) => Boolean(result.isConfirmed));
    }
    return Promise.resolve(global.confirm(text || title));
  }

  function printHtml(html, title) {
    if (global.PastoralPrint?.printHtml) {
      global.PastoralPrint.printHtml(html, title);
      return;
    }
    const w = window.open("", "_blank");
    if (!w) {
      swalAlert("Ispis", "Omogućite skočne prozore za ispis.", "warning");
      return;
    }
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

  function migrate(data) {
    if (!Array.isArray(data.zupniListicIssues)) data.zupniListicIssues = [];
    return data;
  }

  function isEditorialBlock(block, types) {
    const meta = types[block.type] || {};
    if (block.type === "footer") return true;
    return !meta.auto;
  }

  function editorialCard(block, meta) {
    const showTitle = block.type !== "footer";
    return `<article class="listic-block-card listic-block-card--editorial${block.enabled === false ? " is-disabled" : ""}" data-block-id="${esc(block.id)}">
      <div class="listic-block-card-head">
        <label class="listic-block-enable">
          <input type="checkbox" data-block-enabled="${esc(block.id)}" ${block.enabled !== false ? "checked" : ""} />
          <strong>${esc(meta.label)}</strong>
        </label>
      </div>
      ${
        showTitle
          ? `<input type="text" class="listic-block-title-input" data-block-title="${esc(block.id)}" value="${esc(block.title || meta.label)}" placeholder="Naslov sekcije" />`
          : ""
      }
      <div class="listic-rte-host" data-block-body="${esc(block.id)}"></div>
    </article>`;
  }

  function structureRow(block, meta, i, n) {
    const canRemove = !meta.fixed && block.type === "custom_text";
    return `<div class="listic-structure-row${block.enabled === false ? " is-disabled" : ""}" data-block-id="${esc(block.id)}">
      <label class="listic-block-enable">
        <input type="checkbox" data-block-enabled="${esc(block.id)}" ${block.enabled !== false ? "checked" : ""} />
        <strong>${esc(meta.label)}</strong>
      </label>
      <span class="card-sub">${esc(meta.desc || "")}</span>
      <div class="listic-block-move">
        <button type="button" class="btn btn-ghost btn-sm" data-block-up="${esc(block.id)}" ${i === 0 ? "disabled" : ""} title="Gore">↑</button>
        <button type="button" class="btn btn-ghost btn-sm" data-block-down="${esc(block.id)}" ${i === n - 1 ? "disabled" : ""} title="Dolje">↓</button>
        ${canRemove ? `<button type="button" class="btn btn-ghost btn-sm" data-block-del="${esc(block.id)}" title="Ukloni">×</button>` : ""}
      </div>
    </div>`;
  }

  function init(root) {
    const boot = JSON.parse($("#listic-initial-data")?.textContent || "{}");
    const types = boot.config?.blockTypes || {};
    const defLayout = () => clone(boot.config?.defaultLayout || { blocks: [] });
    const { getData, action } = api();

    let weekStart = root.dataset.weekStart || weekStartFrom();
    let editLayout = clone(boot.editLayout || defLayout());
    let editingId = root.dataset.editingId || null;
    let previewTimer;

    const editorFields = $("#listic-editor-fields", root);
    const structureList = $("#listic-structure", root);
    const previewBox = $("#listic-preview", root);
    const weekInput = $("#listic-week-start", root);
    const weekHomeInput = $("#listic-week-start-home", root);

    function readBody(id, scope) {
      const wrap = scope.querySelector(`[data-block-body="${id}"]`);
      if (!wrap) return null;
      return global.PastoralRichText?.getHtml?.(wrap) ?? wrap.value ?? "";
    }

    function readBlocks(blocks) {
      const out = clone({ blocks }).blocks;
      const scopes = [editorFields, structureList].filter(Boolean);
      out.forEach((b) => {
        for (const scope of scopes) {
          const en = scope.querySelector(`[data-block-enabled="${b.id}"]`);
          if (en) b.enabled = en.checked;
          const ti = scope.querySelector(`[data-block-title="${b.id}"]`);
          if (ti) b.title = ti.value;
          const body = readBody(b.id, scope);
          if (body !== null) b.body = body;
        }
      });
      return out;
    }

    function mountRte(scope, blocks, onEdit) {
      if (!global.PastoralRichText || !scope) return;
      scope.querySelectorAll("[data-block-body]").forEach((wrap) => {
        const b = blocks.find((x) => x.id === wrap.dataset.blockBody);
        global.PastoralRichText.mount(wrap, {
          html: b?.body || "",
          placeholder: "Upišite tekst…",
          onChange: onEdit,
        });
      });
    }

    function paintEditors(onEdit) {
      const blocks = editLayout.blocks || [];
      if (editorFields) {
        const editorial = blocks.filter((b) => isEditorialBlock(b, types));
        editorFields.innerHTML = editorial.length
          ? editorial
              .map((b) => editorialCard(b, types[b.type] || { label: b.type, desc: "" }))
              .join("")
          : '<p class="empty-state">Nema uredničkih sekcija. Uključite obavijesti u sastavu listića.</p>';
        mountRte(editorFields, blocks, onEdit);
      }
      if (structureList) {
        structureList.innerHTML = blocks
          .map((b, i) => structureRow(b, types[b.type] || { label: b.type, desc: "" }, i, blocks.length))
          .join("");
      }
      $("#listic-cancel-edit", root)?.classList.toggle("hidden", !editingId);
    }

    function schedulePreview() {
      clearTimeout(previewTimer);
      previewTimer = setTimeout(updatePreview, 250);
    }

    async function updatePreview() {
      if (!previewBox) return;
      editLayout = { blocks: readBlocks(editLayout.blocks) };
      try {
        const res = await action("render_listic_preview", { layout: editLayout, weekStart });
        previewBox.innerHTML = res.html || "";
      } catch {
        previewBox.innerHTML = '<p class="card-sub">Pregled nije dostupan.</p>';
      }
    }

    function issueForWeek(ws) {
      const issues = getData().zupniListicIssues || boot.issues || [];
      return issues.find((x) => x.weekStart === ws) || null;
    }

    function refreshWeekHero() {
      const issue = issueForWeek(weekStart);
      const end = weekEndFrom(weekStart);
      const label = `${fmtShort(weekStart)} – ${fmtShort(end)}`;
      const labelEl = $("#listic-week-label", root);
      if (labelEl) labelEl.textContent = label;

      const statusEl = $("#listic-week-status", root);
      if (statusEl) {
        if (issue) {
          const badge =
            issue.status === "izdan"
              ? '<span class="badge badge-done">Izdan</span>'
              : '<span class="badge">Nacrt</span>';
          statusEl.innerHTML = `${badge}<span class="card-sub">${esc(issue.title || "")}</span>`;
        } else {
          statusEl.innerHTML =
            '<span class="badge">Nema izdanja</span><span class="card-sub">Još nije spremljen listić za ovaj tjedan.</span>';
        }
      }

      const cta = $("#listic-cta-compose", root);
      if (cta) cta.textContent = issue ? "Nastavi sastavljanje" : "Sastavi listić";
      $("#listic-cta-print", root)?.classList.toggle("hidden", !issue);

      if (weekInput) weekInput.value = weekStart;
      if (weekHomeInput) weekHomeInput.value = weekStart;
    }

    function switchTab(tab) {
      root.querySelectorAll(".listic-tab").forEach((b) => b.classList.toggle("is-active", b.dataset.tab === tab));
      root.querySelectorAll(".listic-panel").forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== tab));
      if (tab === "edit") {
        paintEditors(schedulePreview);
        updatePreview();
      }
      if (tab === "week") refreshWeekHero();
    }

    function bindStructureMoves(scope) {
      if (!scope) return;
      scope.addEventListener("click", (e) => {
        const up = e.target.closest("[data-block-up]");
        const down = e.target.closest("[data-block-down]");
        const del = e.target.closest("[data-block-del]");
        let blocks = readBlocks(editLayout.blocks);
        if (up) {
          const i = blocks.findIndex((b) => b.id === up.dataset.blockUp);
          if (i > 0) [blocks[i - 1], blocks[i]] = [blocks[i], blocks[i - 1]];
        } else if (down) {
          const i = blocks.findIndex((b) => b.id === down.dataset.blockDown);
          if (i >= 0 && i < blocks.length - 1) [blocks[i + 1], blocks[i]] = [blocks[i], blocks[i + 1]];
        } else if (del) {
          blocks = blocks.filter((b) => b.id !== del.dataset.blockDel);
        } else return;
        editLayout = { blocks };
        paintEditors(schedulePreview);
        schedulePreview();
      });
      scope.addEventListener("change", (e) => {
        if (e.target.matches("[data-block-enabled]")) schedulePreview();
      });
    }

    function bindEditorInputs(scope) {
      if (!scope) return;
      scope.addEventListener("input", (e) => {
        if (e.target.matches("[data-block-title], [data-block-enabled]")) schedulePreview();
      });
      scope.addEventListener("change", (e) => {
        if (e.target.matches("[data-block-enabled]")) schedulePreview();
      });
    }

    bindEditorInputs(editorFields);
    bindStructureMoves(structureList);
    bindEditorInputs(structureList);

    async function saveIssue(status) {
      const ws = weekInput?.value || weekStart;
      weekStart = ws;
      editLayout = { blocks: readBlocks(editLayout.blocks) };
      const res = await action("upsert_listic_issue", {
        issue: {
          id: editingId || undefined,
          weekStart: ws,
          status,
          layoutSnapshot: editLayout,
        },
      });
      if (res?.item?.id) editingId = res.item.id;
      root.dataset.editingId = editingId || "";
      refreshWeekHero();
      if (global.showToast) {
        global.showToast(status === "izdan" ? "Listić označen kao izdan" : "Nacrt spremljen");
      }
      paintEditors(schedulePreview);
    }

    root.querySelectorAll(".listic-tab").forEach((b) =>
      b.addEventListener("click", () => switchTab(b.dataset.tab))
    );
    root.querySelectorAll("[data-goto-edit]").forEach((b) =>
      b.addEventListener("click", () => switchTab("edit"))
    );
    root.querySelectorAll("[data-goto-history]").forEach((b) =>
      b.addEventListener("click", () => switchTab("history"))
    );

    function onWeekChange(value) {
      weekStart = value || weekStartFrom();
      const issue = issueForWeek(weekStart);
      editingId = issue?.id || null;
      root.dataset.editingId = editingId || "";
      editLayout = clone(issue?.layoutSnapshot || boot.editLayout || defLayout());
      refreshWeekHero();
      if (!$(".listic-panel[data-panel='edit']", root)?.classList.contains("hidden")) {
        paintEditors(schedulePreview);
        updatePreview();
      }
    }

    weekInput?.addEventListener("change", (e) => onWeekChange(e.target.value));
    weekHomeInput?.addEventListener("change", (e) => {
      const ws = e.target.value || weekStartFrom();
      const url = new URL(location.href);
      url.searchParams.set("week", ws);
      url.searchParams.delete("tab");
      location.href = url.pathname + "?" + url.searchParams.toString();
    });

    root.querySelectorAll("[data-add-text-block]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const block = {
          id: `blk_${Date.now().toString(36).slice(-6)}`,
          type: "custom_text",
          enabled: true,
          title: "Nova sekcija",
          body: "",
        };
        editLayout = { blocks: [...readBlocks(editLayout.blocks), block] };
        paintEditors(schedulePreview);
        updatePreview();
        $("#listic-structure-wrap", root)?.setAttribute("open", "");
      });
    });

    $("#listic-print-btn", root)?.addEventListener("click", async () => {
      editLayout = { blocks: readBlocks(editLayout.blocks) };
      const res = await action("render_listic_preview", { layout: editLayout, weekStart });
      printHtml(res.html, `Župni listić ${weekStart}`);
    });

    $("#listic-cta-print", root)?.addEventListener("click", () => {
      const issue = issueForWeek(weekStart);
      if (issue?.renderedHtml) {
        printHtml(issue.renderedHtml, issue.title);
        return;
      }
      switchTab("edit");
      $("#listic-print-btn", root)?.click();
    });

    $("#listic-save-draft", root)?.addEventListener("click", () => saveIssue("nacrt"));
    $("#listic-save-issue", root)?.addEventListener("click", () => saveIssue("izdan"));

    $("#listic-cancel-edit", root)?.addEventListener("click", () => {
      editingId = null;
      root.dataset.editingId = "";
      editLayout = clone(boot.config?.defaultLayout || defLayout());
      weekStart = weekStartFrom();
      if (weekInput) weekInput.value = weekStart;
      if (weekHomeInput) weekHomeInput.value = weekStart;
      paintEditors(schedulePreview);
      refreshWeekHero();
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
        if (issue) {
          global.PastoralModal?.openDetail?.({
            title: issue.title,
            body: `<div class="listic-preview">${issue.renderedHtml || ""}</div>`,
            size: "xl",
          });
        }
      }
      if (edit) {
        const issue = issues.find((x) => x.id === edit.dataset.listicEdit);
        if (!issue) return;
        editingId = issue.id;
        root.dataset.editingId = editingId;
        weekStart = issue.weekStart || weekStartFrom();
        editLayout = clone(issue.layoutSnapshot || defLayout());
        if (weekInput) weekInput.value = weekStart;
        if (weekHomeInput) weekHomeInput.value = weekStart;
        switchTab("edit");
      }
      if (print) {
        const issue = issues.find((x) => x.id === print.dataset.listicPrintId);
        if (issue?.renderedHtml) printHtml(issue.renderedHtml, issue.title);
      }
      if (del) {
        swalConfirm("Obrisati listić?", "Ova radnja se ne može poništiti.", "Obriši").then((ok) => {
          if (!ok) return;
          action("delete_listic_issue", { id: del.dataset.listicDel }).then(() => location.reload());
        });
      }
    });

    paintEditors(schedulePreview);
    refreshWeekHero();

    const params = new URLSearchParams(location.search);
    const tab = params.get("tab");
    if (tab === "history" || tab === "edit" || tab === "week") switchTab(tab);
    else switchTab("week");
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
