# Pastoral — župna administracija

Jedna župa, jedna administracija (demo u pregledniku). Zadano: **Župa Blažene Djevice Marije**, Slavonski Brod, **Đakovačko-osječka nadbiskupija**, župnik **vlč. Krunoslav Karas**.

## Pokretanje

```bash
cd pastoral-zupa
npx serve -l 3340
```

**Ne otvarajte** `file:///...` direktno — preglednik često blokira skripte. Uvijek `npx serve`.

| Što | URL |
|-----|-----|
| Administracija | http://localhost:3340/login.html |
| Nadzorna ploča | http://localhost:3340/app.html |
| **Uredbe i dokumentacija** | http://localhost:3340/pages/admin-paket.html |
| **Javni portal** | http://localhost:3340/public/index.html |
| Sigurnost (demo) | http://localhost:3340/pages/sigurnost.html |

**Kriva putanja** `pages/public/index.html` → automatski preusmjerava na `public/`.

**Prezentacija prodaja:** `login.html` pa gumb **Prezentacija** ili `app.html?prezentacija=1` (automatski pokreće priču, uklj. slajd o sigurnosti).

**Sigurnost na demu:** stranica **Sigurnost** u izborniku + trust traka na nadzornoj ploči + prijava s ulogom i sesijom (8 h).

### OTP prijava (e-mail)

1. Na `login.html` unesite e-mail i ulogu → **Pošalji kod za prijavu**.
2. Kod (6 znamenki) — Netlify funkcija `send-otp` (simulacija ili Resend).
3. Unesite kod → **Potvrdi kod i uđi**.

**Da radi nakon deploya na Netlify:**

| Postavka | Vrijednost |
|----------|------------|
| Base directory | `pastoral-zupa` |
| Publish directory | `.` (korijen te mape) |
| Functions | `netlify/functions` (iz `netlify.toml`) |

**Environment variables** (Site configuration → Environment variables):

```
OTP_RECIPIENT=mateokruljac123@gmail.com
OTP_SIMULATE=true
OTP_EXPOSE_DEV_OTP=true
```

U **simulaciji** (bez `RESEND_API_KEY`): pravi Gmail ne dobiva mail, ali prijava radi — kod se prikaže na ekranu (demo okvir) i piše se u **Functions log** na Netlifyu.

**Pravo slanje na Gmail:** dodaj `RESEND_API_KEY` s [resend.com](https://resend.com) — tada se `OTP_SIMULATE` automatski isključuje.

**Lokalno testiranje kao na Netlifyu:** u mapi `pastoral-zupa` pokreni `npm install` pa `npm run dev` (ne samo `npx serve`).

U `js/otp-mail-config.js` je `provider: "netlify"` — na `*.netlify.app` to se automatski koristi.

Ako su podaci prazni ili stari (multitenant): Postavke → **Vrati demo podatke**.

**Paleta boja:** gumb **Boje** gore desno — 6 crkvenih tema + prilagodba glavne i zlatne boje (sprema se u pregledniku).

## Moduli

| Odjeljak | Funkcija |
|----------|----------|
| **Nadzorna ploča** | KPI, današnje nakane, sakramenti, zadaci + **analitika** (nakane po mjesecima, sakramenti) |
| **Uredbe i dokumentacija** | HBK pravilnici (str. 8–16), obrasci vizitacija, evidencija imovine, ugovori, programi kateheze — povezano na module |
| **Misne nakane** | Kalendar — upis nakane; **plaćanje odmah** (simulacija kartice) ili **platiti kasnije** + „Plati sada” |
| **Raspored misa** | Stalni termini misa |
| **Krštenja** | Matična evidencija, kumovi |
| **Prva pričest** | Skupine po godini, prvopričesnici, katehete |
| **Krizma** | **Po godinama** — popis krizmanika + katehete/suradnici |
| **Vjenčanja** | Parovi, priprema braka |
| **Pogrebi** | Opela, groblje |
| **Pomazanje** | Bolesni |
| **Obitelji** | Karton s tabovima (osnovno, muž/žena, djeca, rođaci, bilješke, lukno) · **učitavanje iz matice** |
| **Korisnici i grupe** | Grupe pristupa (posebno **Svećenici župe**), korisnici aplikacije, evidencija svećenika, dozvole po modulima |
| **Ulice** | CRUD ulica, pregled obitelji po adresi |
| **Događaji** | Župni kalendar + **liturgijski dani** (API: svetac/blagdan, boja, čitanja) |
| **Posjete** | Pastoral u zajednici |
| **Župni ured** | Zadaci (ŽPV, ŽEV, biskupija) |
| **Prezentacija** | Hero na ploči, priča za prodaju (~5 min), portal vjernika |
| **Sigurnost / GDPR** | Zaštita podataka **župljana**: privola na prijavi i portalu, banner u uredu, potvrda pri izvozu, puna obavijest |
| **Matične knjige** | Pregled knjiga (kan. 535, povrat u župu) |
| **Vijeća ŽPV/ŽEV** | Članovi, sastanci (kan. 536–537, sinoda) |
| **Kanonski okvir** | Na svakoj stranici — sklopivi panel (CIC 515–552) |
| **Formulari** | Katalog kao [župni-ured](https://zupni-ured.com.hr/manual.pdf) — krsni/vjenčani/smrtni list |
| **Poruke ureda** | Interni inbox između korisnika |
| **Fin. izvješća** | Kvartalni obračunski + godišnji financijski list |
| **Blagajna** | Plavi i crveni dnevnik (filter) · automatski unosi (npr. nadbiskupija → darovi) |
| **Dugovanja** | Lukno, nakane, sakramenti — filtri po kategoriji i godini |
| **Računi** | Izdavanje računa, status plaćanja, veza na dugovanje |
| **Potvrde** | Ispis isprava iz evidencije (krizma, krštenje, lukno, nakane…) |
| **Dokumenti** | Predlošci + **Excel/CSV** mapiranje + serijski ispis |
| **Javne prijave** | Pregled prijava s weba; preuzimanje u evidenciju |
| **Javni obrasci** | `/public/` — krizma, krštenje, pričest, ukop (bez prijave) |
| **Podsjetnici** | Inbox obaveza (prijave, lukno, posjeti, pripreme…) |
| **Posjete** | Pastoralni posjeti, kućna pričest |
| **Blagajna** | Dnevnik + godišnji izvještaj ŽEV |
| **Gregorijanske nakane** | 30 uzastopnih misa (kalendar nakana) |
| **Župni list** | Ispis nakana za tjedan |
| **Predlošci poruka** | SMS/e-mail — kopiraj (komunikacija) |
| **Obavijesti** | Župni list |
| **Postavke** | Naziv župe, logo URL · PWA manifest |

## Tablice (export / import / paginacija)

Na većini evidencija (krštenja, krizma, vjernici, zadaci, …) alatna traka: pretraga, stranice, **CSV/Excel export**, **import** CSV/Excel (gdje je podržan handler).

- `js/table-kit.js` — zajednički modul tablica
- `js/documents-engine.js` — predlošci i ispis
- `js/chart-loader.js` — učitavanje Chart.js (CDN)
- `js/analytics-engine.js` — Chart.js: veliki grafovi samo na nadzornoj ploči
- `js/debts-engine.js` — dugovanja po kategorijama
- `js/invoices-engine.js` — računi župe
- `js/potvrde-engine.js` — potvrde iz evidencije
- `js/reminders-engine.js` — inbox podsjetnika
- `js/visits-engine.js` — pastoralni posjeti
- `js/preparation-engine.js` — checkliste sakramenata
- `js/cashbook-engine.js` — blagajna
- `js/messages-engine.js` — predlošci poruka
- `js/bulletin-engine.js` — brzi ispis nakana za tjedan (nakane)
- `js/zupni-listic-engine.js` — župni listić (predložak HTML, unos, povijest)
- `js/gregorian-engine.js` — Gregorijanska serija
- `js/security-engine.js` — sigurnost (demo)
- `js/gdpr-engine.js` — GDPR župljana (privola, izvoz, obavijest)
- `js/login-reveal.js` — križ s zoomom pri ulasku u portal nakon prijave
- `js/sidebar-nav-engine.js` — puni izbornik, sklopive sekcije (Pregled, Župa, Sakramenti…)
- `js/kpi-theme.js` — profesionalne KPI kartice po tonovima (liturgija, financije, sakramenti…)
- `js/ui-polish.js` — vizualni efekti na svim admin stranicama (ambijent, stagger, KPI animacija, scroll reveal)
- `js/canon-compliance.js` — kanonski zahtjevi po modulu (CIC, sinoda)
- `public/loader.js` — učitavanje javnog portala (serve + file://)
- `js/liturgical-api.js` — katolički kalendar preko [LitCal API](https://litcal.johnromanodorazio.com/) (blagdani, čitanja); rezerva [Church Calendar API](http://calapi.inadiutorium.cz/); puni hrvatski tekst → [HILP Liturgija dana](https://hilp.hr/liturgija-dana/)

## ERP za župu — što ima smisla

| Modul | Prioritet | U aplikaciji |
|-------|-----------|--------------|
| Evidencija vjernika / obitelji | Visok | Obitelji, ulice |
| Sakramenti i matične knjige | Visok | Krštenja, pričest, krizma, vjenčanja, pogrebi |
| Liturgija (nakane, mise) | Visok | Nakane, raspored misa, **župni listić** |
| **Potvrde / isprave** | Visok | **Potvrde** + Dokumenti |
| **Naplata i dugovanja** | Visok | **Dugovanja**, stipendiji, lukno |
| **Računi / blagajna** | Visok | **Računi** (demo, bez fiskalizacije) |
| Zadaci i vijeća (ŽPV, ŽEV) | Srednji | Zadaci, zapisnici u dokumentima |
| Javne prijave | Srednji | Javne prijave, public obrasci |
| Analitika | Srednji | Nadzorna ploča |
| Zalihe / inventar crkve | Nizak | Nije u demo-u (ERP preširok) |
| Plaće ministranata | Nizak | Vanjsk knjigovodstvo |
| Nabava / dobavljači | Nizak | Samo župna ekonomija — opcionalno kasnije |
| Fiskalizacija / e-Račun | Produkcija | Integracija s knjigovođom |

Produkcija: backend, uloge (župnik / ured / blagajna), arhiva matičnih knjiga, PDF potpisi.

## Tehnički

- `js/parish-config.js` — podaci o župi (nije multitenant)
- `js/data-seed.js` — jedna baza `pastoral_data` u localStorage
- Produkcija: backend + korisnici + prave matične knjige
