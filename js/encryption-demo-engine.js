/**
 * Demo: kako će osjetljivi podaci u produkcijskoj PostgreSQL bazi izgledati (AES-256-GCM)
 */
(function (global) {
  const SCHEMA = "pastoral";
  const TABLE = "clanovi";

  const SAMPLE_RECORD = {
    tablica: `${SCHEMA}.${TABLE}`,
    id: "fam_horvat_m1",
    polja: [
      { key: "ime_prezime", label: "Ime i prezime", col: "ime_prezime_enc", osjetljivo: true, plain: "Ana Horvat" },
      { key: "telefon", label: "Telefon", col: "telefon_enc", osjetljivo: true, plain: "091 111 1111" },
      { key: "email", label: "E-mail", col: "email_enc", osjetljivo: true, plain: "ana@demo.hr" },
      { key: "adresa", label: "Adresa", col: "adresa_enc", osjetljivo: true, plain: "Ulica kralja Tomislava 12" },
      { key: "oib", label: "OIB", col: "oib_enc", osjetljivo: true, plain: "12345678901" },
      { key: "biljeske", label: "Pastoralne bilješke", col: "biljeske_enc", osjetljivo: true, plain: "Posjet 12.3. — razgovor o krizmi" },
      { key: "prezime", label: "Prezime (indeks)", col: "prezime", osjetljivo: false, plain: "Horvat" },
      { key: "lukno_godina", label: "Lukno 2026", col: "lukno_2026", osjetljivo: false, plain: "placeno" },
    ],
  };

  /** Redovi u PostgreSQL tablici (demo) */
  const PG_ROWS = [
    {
      id: "fam_horvat_m1",
      obitelj_id: "fam_horvat",
      prezime: "Horvat",
      lukno_2026: "placeno",
      plain: { ime_prezime: "Ana Horvat", telefon: "091 111 1111", email: "ana@demo.hr" },
    },
    {
      id: "fam_kovac_m1",
      obitelj_id: "fam_kovac",
      prezime: "Kovač",
      lukno_2026: "djelomicno",
      plain: { ime_prezime: "Marko Kovač", telefon: "098 222 2222", email: "marko@demo.hr" },
    },
    {
      id: "fam_babic_m2",
      obitelj_id: "fam_babic",
      prezime: "Babić",
      lukno_2026: "nije_placeno",
      plain: { ime_prezime: "Ivana Babić", telefon: "095 333 3333", email: "ivana@demo.hr" },
    },
  ];

  /** Statički „šifrirani” blobovi za prikaz prije klika (izgled kao BYTEA u pgAdmin) */
  const SEED_CIPHER = {
    fam_horvat_m1: {
      ime_prezime_enc: "\\x9f4a2c8e1b07d3a6f5e8c29104b7d2e8a1c3f9056e7d4a2b1c0987654321a8f6e5d4c3b2a10987",
      telefon_enc: "\\x2e8b91c4f0a3d56789012abcdef3456789012ab34cd56ef7890ab12cd34ef5678",
      email_enc: "\\x71c2d9e0f1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6",
      adresa_enc: "\\xa1b2c3d4e5f60718293a4b5c6d7e8f901234567890abcdef1234567890abcdef12",
      oib_enc: "\\x5566778899aabbccddeeff00112233445566778899aabbccddeeff0011223344",
      biljeske_enc: "\\xccddeeff00112233445566778899aabbccddeeff00112233445566778899aabbcc",
    },
    fam_kovac_m1: {
      ime_prezime_enc: "\\x1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b",
      telefon_enc: "\\x8f7e6d5c4b3a291807162534435261708192a3b4c5d6e7f8091a2b3c4d5e6e7f8",
      email_enc: "\\x33445566778899aabbccddeeff00112233445566778899aabbccddeeff00112233",
      adresa_enc: "\\xdeadbeefcafebabe0123456789abcdef0123456789abcdef0123456789ab",
      oib_enc: "\\xfeedface0123456789abcdef0123456789abcdef0123456789abcdef01",
      biljeske_enc: "\\x0badf00d0badf00d0badf00d0badf00d0badf00d0badf00d0badf00d0bad",
    },
    fam_babic_m2: {
      ime_prezime_enc: "\\xabcdef0123456789abcdef0123456789abcdef0123456789abcdef01234567",
      telefon_enc: "\\x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fe",
      email_enc: "\\x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff00",
      adresa_enc: "\\x22223333444455556666777788889999aaaabbbbccccddddeeeeffff0011",
      oib_enc: "\\x3333444455556666777788889999aaaabbbbccccddddeeeeffff00112233",
      biljeske_enc: "\\x444455556666777788889999aaaabbbbccccddddeeeeffff0011223344",
    },
  };

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function bufToHex(buf) {
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  function toPgBytea(hex) {
    return `\\x${hex}`;
  }

  function truncateHex(hex, max = 56) {
    if (hex.length <= max) return hex;
    return `${hex.slice(0, max)}…`;
  }

  function truncatePgBytea(bytea, max = 52) {
    const inner = bytea.replace(/^\\x/, "");
    if (inner.length <= max) return bytea;
    return `\\x${inner.slice(0, max)}…`;
  }

  async function deriveAesKey(passphrase) {
    const enc = new TextEncoder();
    const raw = await crypto.subtle.digest("SHA-256", enc.encode(passphrase));
    return crypto.subtle.importKey("raw", raw, { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
  }

  async function encryptField(plain, key) {
    const enc = new TextEncoder();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = await crypto.subtle.encrypt({ name: "AES-GCM" }, key, enc.encode(plain));
    const combined = new Uint8Array(iv.length + ct.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(ct), iv.length);
    const hex = bufToHex(combined);
    return {
      hex,
      bytea: toPgBytea(hex),
      ivHex: bufToHex(iv),
      preview: `enc:v1:${truncateHex(hex, 28)}`,
    };
  }

  function renderPgTable(cipherByRow) {
    const cols = [
      "id",
      "obitelj_id",
      "prezime",
      "lukno_2026",
      "ime_prezime_enc",
      "telefon_enc",
      "email_enc",
      "adresa_enc",
      "oib_enc",
      "biljeske_enc",
    ];

    const header = cols.map((c) => `<th class="pg-col-${c.includes("_enc") ? "cipher" : "plain"}">${esc(c)}</th>`).join("");

    const body = PG_ROWS.map((row) => {
      const c = cipherByRow[row.id] || SEED_CIPHER[row.id] || {};
      const cells = cols
        .map((col) => {
          if (col.endsWith("_enc")) {
            const val = c[col] || "\\x…";
            return `<td class="pg-cell-cipher" title="BYTEA — nečitljivo bez ključa župe"><code>${esc(truncatePgBytea(val, 44))}</code></td>`;
          }
          const val = row[col] ?? "—";
          return `<td class="pg-cell-plain">${esc(val)}</td>`;
        })
        .join("");
      return `<tr data-pg-id="${esc(row.id)}">${cells}</tr>`;
    }).join("");

    return `
      <div class="pg-demo-window">
        <div class="pg-demo-titlebar">
          <span class="pg-demo-dots" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="pg-demo-title">PostgreSQL 16 · pgAdmin — Query Tool</span>
        </div>
        <pre class="pg-demo-sql" aria-hidden="true">SELECT id, obitelj_id, prezime, lukno_2026,
       ime_prezime_enc, telefon_enc, email_enc, adresa_enc, oib_enc, biljeske_enc
FROM ${SCHEMA}.${TABLE}
WHERE tenant_id = 'zupa-bdm-sb'
ORDER BY prezime
LIMIT 3;</pre>
        <div class="pg-demo-result-label">Rezultat upita (3 retka) — <strong>samo šifrirani blobovi</strong>, bez ključa župe:</div>
        <div class="table-wrap pg-table-wrap">
          <table class="data-table pg-demo-table">
            <thead><tr>${header}</tr></thead>
            <tbody id="enc-pg-tbody">${body}</tbody>
          </table>
        </div>
        <p class="pg-demo-legend card-sub">
          <span class="pg-legend-item pg-legend-item--plain">Običan tekst</span> = indeks / pretraga &nbsp;·&nbsp;
          <span class="pg-legend-item pg-legend-item--cipher">\\x…</span> = BYTEA (AES-256-GCM + IV)
        </p>
      </div>`;
  }

  function renderCompareStrip() {
    return `
      <div class="encryption-compare">
        <div class="encryption-compare-card encryption-compare-card--app">
          <p class="card-label">Što župnik vidi u aplikaciji</p>
          <p class="encryption-compare-value">Ana Horvat · 091 111 1111</p>
          <span class="badge badge-done">Otključano (HTTPS + sesija)</span>
        </div>
        <div class="encryption-compare-arrow" aria-hidden="true">≠</div>
        <div class="encryption-compare-card encryption-compare-card--db">
          <p class="card-label">Što netko vidi u bazi / backupu</p>
          <p class="encryption-compare-value enc-compare-cipher"><code>\\x9f4a2c8e1b07d3a6f5e8c29…</code></p>
          <span class="badge badge-urgent">Nečitljivo bez ključa</span>
        </div>
      </div>`;
  }

  function mountEncryptionDemo(mountEl, api) {
    if (!mountEl) return;

    mountEl.innerHTML = `
      <section class="card wide encryption-demo-card" id="encryption-demo-section">
        <div class="encryption-demo-head">
          <div>
            <h2 class="section-title">Šifriranje podataka u bazi (produkcija)</h2>
            <p class="card-sub">Ispod je primjer kako tablica <code>${SCHEMA}.${TABLE}</code> izgleda u PostgreSQL-u — osjetljiva polja su <strong>BYTEA</strong> (šifrirani blob), ne običan tekst.</p>
          </div>
          <button type="button" class="btn btn-primary btn-sm" id="enc-demo-run">Osvježi demo šifriranje</button>
        </div>

        ${renderCompareStrip()}
        <div id="enc-pg-mount">${renderPgTable(SEED_CIPHER)}</div>

        <details class="encryption-schema-details" open>
          <summary>DDL — definicija tablice (skraćeno)</summary>
          <pre class="encryption-json-pre encryption-json-pre--ddl">CREATE TABLE ${SCHEMA}.${TABLE} (
  id              UUID PRIMARY KEY,
  tenant_id       VARCHAR(64) NOT NULL,
  obitelj_id      UUID NOT NULL,
  prezime         VARCHAR(120) NOT NULL,        -- indeks (pretraga)
  lukno_2026      VARCHAR(32),                  -- indeks
  ime_prezime_enc BYTEA NOT NULL,               -- AES-256-GCM
  telefon_enc     BYTEA,
  email_enc       BYTEA,
  adresa_enc      BYTEA,
  oib_enc         BYTEA,
  oib_hash        CHAR(64),                     -- SHA-256 za lookup
  biljeske_enc    BYTEA,
  created_at      TIMESTAMPTZ DEFAULT now()
);</pre>
        </details>

        <div class="encryption-flow" aria-hidden="true">
          <span class="encryption-flow-step">Aplikacija (HTTPS)</span>
          <span class="encryption-flow-arrow">→</span>
          <span class="encryption-flow-step encryption-flow-step--key">Ključ župe (HSM / vault)</span>
          <span class="encryption-flow-arrow">→</span>
          <span class="encryption-flow-step encryption-flow-step--db">PostgreSQL BYTEA</span>
        </div>
        <div class="encryption-key-box" id="enc-demo-key-box">
          <p class="card-label">Simulirani župni ključ (demo)</p>
          <code class="encryption-key-val" id="enc-demo-key">Primjer već učitan — kliknite za novo šifriranje</code>
        </div>
        <div class="table-wrap">
          <table class="data-table encryption-table">
            <thead>
              <tr>
                <th>Polje</th>
                <th>U aplikaciji</th>
                <th>U stupcu baze</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="enc-demo-tbody">
              ${SAMPLE_RECORD.polja
                .map((f) => {
                  const seed = SEED_CIPHER.fam_horvat_m1[f.col];
                  const cipherPreview = f.osjetljivo
                    ? seed
                      ? `<code class="enc-hex">${esc(truncatePgBytea(seed, 40))}</code>`
                      : '<span class="badge">—</span>'
                    : `<span class="enc-plain-small">${esc(f.plain)}</span>`;
                  return `
                <tr data-field="${esc(f.key)}">
                  <td><strong>${esc(f.label)}</strong><br><small class="card-sub">${esc(f.col || f.key)}</small></td>
                  <td class="enc-plain">${esc(f.plain)}</td>
                  <td class="enc-cipher">${cipherPreview}</td>
                  <td>${f.osjetljivo ? '<span class="badge badge-urgent">BYTEA</span>' : '<span class="badge badge-done">indeks</span>'}</td>
                </tr>`;
                })
                .join("")}
            </tbody>
          </table>
        </div>
        <details class="encryption-json-details">
          <summary>Jedan redak kao JSON (pg_dump / API)</summary>
          <p class="card-sub">Kako izgleda u bazi — nema čitljivog imena ni telefona:</p>
          <pre class="encryption-json-pre encryption-json-pre--cipher" id="enc-demo-json-after">${esc(
            JSON.stringify(
              {
                id: "fam_horvat_m1",
                tenant_id: "zupa-bdm-sb",
                prezime: "Horvat",
                lukno_2026: "placeno",
                ime_prezime_enc: SEED_CIPHER.fam_horvat_m1.ime_prezime_enc,
                telefon_enc: SEED_CIPHER.fam_horvat_m1.telefon_enc,
                email_enc: SEED_CIPHER.fam_horvat_m1.email_enc,
              },
              null,
              2
            )
          )}</pre>
        </details>
        <ul class="encryption-notes">
          <li><strong>BYTEA</strong> u PostgreSQL-u — binarni blob; u pgAdminu prikaz <code>\\x9f4a2c…</code>.</li>
          <li><strong>AES-256-GCM</strong> — IV (12 B) + ciphertext u istom blobu.</li>
          <li><strong>Backup / curenje</strong> — dump baze bez ključa župe = samo hex, kao gore.</li>
        </ul>
      </section>`;

    mountEl.querySelector("#enc-demo-run")?.addEventListener("click", () => runDemo(mountEl, api));
  }

  async function runDemo(mountEl, api) {
    const btn = mountEl.querySelector("#enc-demo-run");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Šifriram…";
    }

    const passphrase = `pastoral-zupa-demo-${Date.now().toString(36)}`;
    const keyEl = mountEl.querySelector("#enc-demo-key");
    if (keyEl) keyEl.textContent = `${passphrase.slice(0, 28)}… (demo)`;

    let key;
    try {
      key = await deriveAesKey(passphrase);
    } catch {
      api?.showToast?.("Preglednik ne podržava Web Crypto API");
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Osvježi demo šifriranje";
      }
      return;
    }

    const cipherByRow = {};
    const dbRecord = { id: SAMPLE_RECORD.id, tenant_id: "zupa-bdm-sb", tablica: SAMPLE_RECORD.tablica };

    for (const pgRow of PG_ROWS) {
      cipherByRow[pgRow.id] = { ...SEED_CIPHER[pgRow.id] };
      for (const [plainKey, plainVal] of Object.entries(pgRow.plain)) {
        const enc = await encryptField(plainVal, key);
        const col = `${plainKey}_enc`;
        cipherByRow[pgRow.id][col] = enc.bytea;
      }
    }

    const pgMount = mountEl.querySelector("#enc-pg-mount");
    if (pgMount) pgMount.innerHTML = renderPgTable(cipherByRow);

    for (const field of SAMPLE_RECORD.polja) {
      const row = mountEl.querySelector(`tr[data-field="${field.key}"]`);
      const cipherCell = row?.querySelector(".enc-cipher");
      if (!row || !cipherCell) continue;

      if (field.osjetljivo) {
        const enc = await encryptField(field.plain, key);
        cipherCell.innerHTML = `<code class="enc-hex" title="${esc(enc.hex)}">${esc(truncatePgBytea(enc.bytea, 42))}</code>`;
        dbRecord[field.col || `${field.key}_enc`] = enc.bytea;
      } else {
        cipherCell.innerHTML = `<span class="enc-plain-small">${esc(field.plain)}</span>`;
        dbRecord[field.col || field.key] = field.plain;
      }
    }

    const afterEl = mountEl.querySelector("#enc-demo-json-after");
    if (afterEl) {
      afterEl.textContent = JSON.stringify(
        {
          id: dbRecord.id,
          tenant_id: dbRecord.tenant_id,
          prezime: "Horvat",
          lukno_2026: "placeno",
          ime_prezime_enc: dbRecord.ime_prezime_enc,
          telefon_enc: dbRecord.telefon_enc,
          email_enc: dbRecord.email_enc,
          adresa_enc: dbRecord.adresa_enc,
          oib_enc: dbRecord.oib_enc,
          biljeske_enc: dbRecord.biljeske_enc,
        },
        null,
        2
      );
    }

    if (btn) {
      btn.disabled = false;
      btn.textContent = "Osvježi demo šifriranje";
    }
    api?.showToast?.("PostgreSQL prikaz ažuriran — novi šifrirani blobovi");
  }

  global.PastoralEncryptionDemo = {
    mountEncryptionDemo,
    SAMPLE_RECORD,
    SEED_CIPHER,
    renderPgTable,
  };
})(typeof window !== "undefined" ? window : global);
