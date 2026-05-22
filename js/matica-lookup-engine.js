/**
 * Pretraga matičnih knjiga — krštenja, vjenčanja, umrli
 */
(function (global) {
  function fmt(d) {
    if (!d) return "";
    return new Date(d + "T12:00:00").toLocaleDateString("hr-HR");
  }

  function searchBaptisms(data, q) {
    const s = String(q).toLowerCase().trim();
    if (!s) return [];
    return (data.baptisms || [])
      .filter(
        (b) =>
          b.childName?.toLowerCase().includes(s) ||
          b.parents?.toLowerCase().includes(s) ||
          b.registryNo?.toLowerCase().includes(s)
      )
      .slice(0, 20)
      .map((b) => ({
        type: "krštenja",
        id: b.id,
        label: `${b.childName} — krštenje ${fmt(b.baptismDate)}`,
        payload: {
          dijete: b.childName,
          ime_prezime: b.childName,
          roditelji: b.parents,
          kumovi: b.godparents,
          datum_krstenja: fmt(b.baptismDate),
          maticni_broj: b.registryNo,
          birthDate: b.birthDate,
          parents: b.parents,
        },
      }));
  }

  function searchWeddings(data, q) {
    const s = String(q).toLowerCase().trim();
    if (!s) return [];
    return (data.weddings || [])
      .filter((w) => w.couple?.toLowerCase().includes(s))
      .slice(0, 20)
      .map((w) => {
        const parts = (w.couple || "").split("&").map((x) => x.trim());
        return {
          type: "vjenčanja",
          id: w.id,
          label: `${w.couple} — ${fmt(w.weddingDate)}`,
          payload: {
            mladenci: w.couple,
            mladzenja: parts[0] || "",
            mlada: parts[1] || "",
            datum: fmt(w.weddingDate),
            datum_vjencanja: fmt(w.weddingDate),
            svjedoci: w.witnesses,
          },
        };
      });
  }

  function searchFunerals(data, q) {
    const s = String(q).toLowerCase().trim();
    if (!s) return [];
    return (data.funerals || [])
      .filter((f) => f.deceased?.toLowerCase().includes(s) || f.familyContact?.toLowerCase().includes(s))
      .slice(0, 20)
      .map((f) => ({
        type: "umrli",
        id: f.id,
        label: `${f.deceased} — ${fmt(f.funeralDate)}`,
        payload: {
          pokojnik: f.deceased.replace(/^\+?\s*/, ""),
          datum_smrti: fmt(f.deathDate),
          datum_pogreba: fmt(f.funeralDate),
          prebivaliste: f.cemetery,
        },
      }));
  }

  function search(data, types, q) {
    const out = [];
    if (types.includes("krštenja")) out.push(...searchBaptisms(data, q));
    if (types.includes("vjenčanja")) out.push(...searchWeddings(data, q));
    if (types.includes("umrli")) out.push(...searchFunerals(data, q));
    return out;
  }

  function openSearchModal(api, opts) {
    const { types = ["krštenja", "vjenčanja", "umrli"], onPick, title = "Pretraga matice" } = opts;
    const M = global.PastoralModal;
    if (!M) return;

    M.openDetail({
      title,
      size: "md",
      body: `
        <div class="form-group">
          <label>Ime ili prezime (min. 2 znaka)</label>
          <input type="search" id="matica-q" placeholder="Pretraži…" autocomplete="off">
        </div>
        <ul id="matica-results" class="matica-results-list"></ul>`,
      onOpen: (overlay) => {
        const input = overlay.querySelector("#matica-q");
        const list = overlay.querySelector("#matica-results");
        const run = () => {
          const q = input?.value || "";
          const hits = q.length >= 2 ? search(api.getData(), types, q) : [];
          list.innerHTML = hits.length
            ? hits
                .map(
                  (h) =>
                    `<li><button type="button" class="btn btn-ghost btn-sm matica-pick" data-pick-id="${api.escapeHtml(h.id)}" data-pick-type="${h.type}" style="width:100%;text-align:left">${api.escapeHtml(h.label)} <span class="badge">${h.type}</span></button></li>`
                )
                .join("")
            : `<li class="card-sub">${q.length < 2 ? "Upišite barem 2 znaka." : "Nema rezultata."}</li>`;
          list.querySelectorAll(".matica-pick").forEach((btn) => {
            btn.addEventListener("click", () => {
              const hit = hits.find((x) => x.id === btn.dataset.pickId && x.type === btn.dataset.pickType);
              if (hit) {
                onPick(hit);
                M.close();
              }
            });
          });
        };
        input?.addEventListener("input", run);
      },
    });
  }

  global.PastoralMaticaLookup = { search, openSearchModal, searchBaptisms, searchWeddings, searchFunerals };
})(typeof window !== "undefined" ? window : global);
