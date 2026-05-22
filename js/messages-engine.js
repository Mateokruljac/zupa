/**
 * Predlošci poruka — SMS / e-mail (kopiraj)
 */
(function (global) {
  const DEFAULT_TEMPLATES = [
    {
      id: "lukno_podsjetnik",
      title: "Podsjetnik — lukno",
      channel: "sms",
      body: "Poštovani, podsjećamo na uplatu župnog lukna za {{godina}}. g. Hvala. {{zupa}}",
    },
    {
      id: "nakana_placanje",
      title: "Nakana — plaćanje",
      channel: "sms",
      body: "Poštovani {{ime}}, vaša misna nakana ({{namjera}}, {{datum}}) čeka uplatu stipendija {{iznos}} €. Župni ured {{zupa}}.",
    },
    {
      id: "krizma_poziv",
      title: "Krizma — sastanak",
      channel: "email",
      body: "Poštovani roditelji,\n\npodsjećamo na sastanak pripreme za sv. Potvrdu ({{godina}}.) u župi {{zupa}}.\n\nS poštovanjem,\n{{zupnik}}",
    },
    {
      id: "posjet_potvrda",
      title: "Posjet zakazan",
      channel: "sms",
      body: "Poštovani, pastoralni posjet župnog ureda zakazan je za {{datum}}. {{zupa}} — {{zupnik}}",
    },
    {
      id: "vjencanje_dokumenti",
      title: "Vjenčanje — dokumenti",
      channel: "email",
      body: "Poštovani,\n\nmolimo donijeti rodne listove i potvrde o krštenju u župni ured prije zakazanog termina pripreme braka.\n\n{{zupa}}",
    },
  ];

  function mergeTemplate(text, vars) {
    let out = text;
    Object.entries(vars).forEach(([k, v]) => {
      out = out.split(`{{${k}}}`).join(String(v ?? ""));
    });
    return out;
  }

  function mountMessagesSection(container, api) {
    const data = api.getData();
    if (!data.messageTemplates?.length) data.messageTemplates = [...DEFAULT_TEMPLATES];
    const settings = api.getSettings();
    const esc = api.escapeHtml;

    container.innerHTML = `
      <section class="card">
        <h2 class="section-title">Predlošci poruka (SMS / e-mail)</h2>
        <p class="card-sub">Odaberite predložak, ispunite podatke, kopirajte u poruku. Slanje nije automatizirano (GDPR).</p>
        <div class="form-group"><label>Predložak</label><select id="msg-tpl-select">${data.messageTemplates.map((t) => `<option value="${t.id}">${esc(t.title)} (${t.channel})</option>`).join("")}</select></div>
        <div class="form-grid" id="msg-vars"></div>
        <div class="form-group form-wide"><label>Tekst poruke</label><textarea id="msg-preview" rows="6" readonly></textarea></div>
        <button type="button" class="btn btn-primary btn-sm" id="msg-copy">Kopiraj tekst</button>
      </section>`;

    const varsDefaults = () => ({
      zupa: settings.name,
      zupnik: settings.pastor,
      godina: new Date().getFullYear(),
      datum: new Date().toLocaleDateString("hr-HR"),
      ime: "",
      namjera: "",
      iznos: "",
    });

    let vars = varsDefaults();

    function refreshPreview() {
      const id = container.querySelector("#msg-tpl-select")?.value;
      const tpl = data.messageTemplates.find((t) => t.id === id);
      const prev = container.querySelector("#msg-preview");
      if (tpl && prev) prev.value = mergeTemplate(tpl.body, vars);
    }

    function buildVarFields() {
      const fields = ["ime", "namjera", "datum", "iznos", "godina"];
      const mount = container.querySelector("#msg-vars");
      mount.innerHTML = fields
        .map(
          (f) =>
            `<div class="form-group"><label>${esc(f)}</label><input data-msg-var="${f}" value="${esc(String(vars[f] ?? ""))}" /></div>`
        )
        .join("");
      mount.querySelectorAll("[data-msg-var]").forEach((inp) => {
        inp.addEventListener("input", () => {
          vars[inp.dataset.msgVar] = inp.value;
          refreshPreview();
        });
      });
      refreshPreview();
    }

    container.querySelector("#msg-tpl-select")?.addEventListener("change", () => {
      vars = varsDefaults();
      buildVarFields();
    });
    container.querySelector("#msg-copy")?.addEventListener("click", async () => {
      const text = container.querySelector("#msg-preview")?.value;
      try {
        await navigator.clipboard.writeText(text);
        api.showToast("Kopirano u međuspremnik");
      } catch {
        api.showToast("Kopiraj ručno iz polja");
      }
    });
    buildVarFields();
  }

  function migrate(data) {
    if (!data.messageTemplates?.length) data.messageTemplates = JSON.parse(JSON.stringify(DEFAULT_TEMPLATES));
    return data;
  }

  global.PastoralMessages = { DEFAULT_TEMPLATES, mergeTemplate, mountMessagesSection, migrate };
})(typeof window !== "undefined" ? window : global);
