# Pastoral — župna administracija

Jedna župa, jedna administracija (demo u pregledniku). Zadano: **Župa Blažene Djevice Marije**, Slavonski Brod, **Đakovačko-osječka nadbiskupija**, župnik **vlč. Krunoslav Karas**.

## Pokretanje

```bash
cd pastoral-zupa
npx serve -l 3340
```

**http://localhost:3340/login.html** → prijava → nadzorna ploča.

Javni obrasci: **http://localhost:3340/public/index.html**

Ako su podaci prazni ili stari (multitenant): Postavke → **Vrati demo podatke**.

**Paleta boja:** gumb **Boje** gore desno — 6 crkvenih tema + prilagodba glavne i zlatne boje (sprema se u pregledniku).

## Moduli

| Odjeljak | Funkcija |
|----------|----------|
| **Nadzorna ploča** | KPI, današnje nakane, sakramenti, zadaci + **analitika** (nakane po mjesecima, sakramenti) |
| **Misne nakane** | Kalendar — upis nakane; **plaćanje odmah** (simulacija kartice) ili **platiti kasnije** + „Plati sada” |
| **Raspored misa** | Stalni termini misa |
| **Krštenja** | Matična evidencija, kumovi |
| **Prva pričest** | Skupine po godini, prvopričesnici, katehete |
| **Krizma** | **Po godinama** — popis krizmanika + katehete/suradnici |
| **Vjenčanja** | Parovi, priprema braka |
| **Pogrebi** | Opela, groblje |
| **Pomazanje** | Bolesni |
| **Obitelji** | CRUD obitelji i članova · **lukno** i **davanja za crkvu po godinama** |
| **Ulice** | CRUD ulica, pregled obitelji po adresi |
| **Događaji** | Župni kalendar + **liturgijski dani** (API: svetac/blagdan, boja, čitanja) |
| **Posjete** | Pastoral u zajednici |
| **Lektori** | Liturgijske službe |
| **Župni ured** | Zadaci (ŽPV, ŽEV, biskupija) |
| **Dugovanja** | Lukno, nakane, sakramenti — filtri po kategoriji i godini |
| **Računi** | Izdavanje računa, status plaćanja, veza na dugovanje |
| **Potvrde** | Ispis isprava iz evidencije (krizma, krštenje, lukno, nakane…) |
| **Dokumenti** | Predlošci + **Excel/CSV** mapiranje + serijski ispis |
| **Javne prijave** | Pregled prijava s weba; preuzimanje u evidenciju |
| **Javni obrasci** | `/public/` — krizma, krštenje, pričest, ukop (bez prijave) |
| **Obavijesti** | Župni list |
| **Postavke** | Naziv župe, logo URL |

## Tablice (export / import / paginacija)

Na većini evidencija (krštenja, krizma, vjernici, zadaci, …) alatna traka: pretraga, stranice, **CSV/Excel export**, **import** CSV/Excel (gdje je podržan handler).

- `js/table-kit.js` — zajednički modul tablica
- `js/documents-engine.js` — predlošci i ispis
- `js/analytics-engine.js` — grafici na nadzornoj ploči
- `js/debts-engine.js` — dugovanja po kategorijama
- `js/invoices-engine.js` — računi župe
- `js/potvrde-engine.js` — potvrde iz evidencije
- `js/liturgical-api.js` — katolički kalendar preko [LitCal API](https://litcal.johnromanodorazio.com/) (blagdani, čitanja); rezerva [Church Calendar API](http://calapi.inadiutorium.cz/); puni hrvatski tekst → [HILP Liturgija dana](https://hilp.hr/liturgija-dana/)

## ERP za župu — što ima smisla

| Modul | Prioritet | U aplikaciji |
|-------|-----------|--------------|
| Evidencija vjernika / obitelji | Visok | Obitelji, ulice |
| Sakramenti i matične knjige | Visok | Krštenja, pričest, krizma, vjenčanja, pogrebi |
| Liturgija (nakane, mise) | Visok | Nakane, raspored misa |
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
