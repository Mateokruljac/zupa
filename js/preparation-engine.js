/**
 * Checkliste pripreme sakramenata
 */
(function (global) {
  const TEMPLATES = {
    baptisms: [
      { id: "upis", label: "Upis u evidenciju" },
      { id: "roditelji", label: "Razgovor s roditeljima" },
      { id: "kumovi", label: "Kumovi potvrđeni" },
      { id: "matica", label: "Matični podaci" },
      { id: "stipendij", label: "Naknada / stipendij" },
      { id: "obred", label: "Obred zakazan" },
    ],
    weddings: [
      { id: "upis", label: "Upis para" },
      { id: "dokumenti", label: "Dokumenti (rodni listovi)" },
      { id: "sastanak1", label: "1. sastanak pripreme" },
      { id: "sastanak2", label: "2. sastanak pripreme" },
      { id: "sastanak3", label: "3. sastanak pripreme" },
      { id: "stipendij", label: "Naknada vjenčanja" },
      { id: "proba", label: "Proba / dogovor obreda" },
      { id: "obred", label: "Obred" },
    ],
    confirmations: [
      { id: "upis", label: "Upis krizmanika" },
      { id: "kateheza", label: "Kateheza u tijeku" },
      { id: "pristupnica", label: "Pristupnica potpisana" },
      { id: "naknada", label: "Grupna naknada" },
      { id: "obred", label: "Obred potvrde" },
    ],
  };

  function ensureChecklist(record, arrayKey) {
    const tpl = TEMPLATES[arrayKey];
    if (!tpl) return record;
    if (!record.prepChecklist) {
      record.prepChecklist = tpl.map((t) => ({ id: t.id, done: false }));
    }
    tpl.forEach((t) => {
      if (!record.prepChecklist.find((c) => c.id === t.id)) {
        record.prepChecklist.push({ id: t.id, done: false });
      }
    });
    return record;
  }

  function getProgress(record, arrayKey) {
    ensureChecklist(record, arrayKey);
    const tpl = TEMPLATES[arrayKey] || [];
    const done = (record.prepChecklist || []).filter((c) => c.done).length;
    const total = tpl.length || 1;
    return { done, total, percent: Math.round((done / total) * 100) };
  }

  function renderChecklistHtml(record, arrayKey, esc) {
    ensureChecklist(record, arrayKey);
    const tpl = TEMPLATES[arrayKey] || [];
    const prog = getProgress(record, arrayKey);
    return `
      <div class="prep-block" data-prep-key="${arrayKey}" data-prep-id="${esc(record.id)}">
        <p class="card-sub">Priprema: <strong>${prog.percent}%</strong> (${prog.done}/${prog.total})</p>
        <div class="prep-progress"><div class="prep-progress-bar" style="width:${prog.percent}%"></div></div>
        <ul class="prep-checklist">${tpl
          .map((t) => {
            const c = record.prepChecklist.find((x) => x.id === t.id);
            const checked = c?.done ? "checked" : "";
            return `<li><label><input type="checkbox" data-prep-step="${t.id}" ${checked} /> ${esc(t.label)}</label></li>`;
          })
          .join("")}</ul>
      </div>`;
  }

  function bindChecklist(root, api, arrayKey, onUpdate) {
    root?.addEventListener("change", (ev) => {
      const cb = ev.target.closest("[data-prep-step]");
      if (!cb) return;
      const block = cb.closest("[data-prep-key]");
      const id = block?.dataset.prepId;
      const step = cb.dataset.prepStep;
      const data = api.getData();
      const rec = data[arrayKey]?.find((r) => r.id === id);
      if (!rec) return;
      ensureChecklist(rec, arrayKey);
      const item = rec.prepChecklist.find((c) => c.id === step);
      if (item) item.done = cb.checked;
      if (arrayKey === "weddings" && step.startsWith("sastanak")) {
        rec.preparatorySessions = rec.prepChecklist.filter((c) => c.id.startsWith("sastanak") && c.done).length;
      }
      if (step === "dokumenti") rec.documentsOk = cb.checked;
      api.saveData(data);
      onUpdate?.();
    });
  }

  function migrateAll(data) {
    (data.baptisms || []).forEach((r) => ensureChecklist(r, "baptisms"));
    (data.weddings || []).forEach((r) => ensureChecklist(r, "weddings"));
    (data.confirmations || []).forEach((g) => ensureChecklist(g, "confirmations"));
    return data;
  }

  global.PastoralPreparation = {
    TEMPLATES,
    ensureChecklist,
    getProgress,
    renderChecklistHtml,
    bindChecklist,
    migrateAll,
  };
})(typeof window !== "undefined" ? window : global);
