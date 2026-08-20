# Razvojni checkpoint

Datum zapisa: 3. kolovoza 2026.

## Trenutačno stanje

Završena je prva, kompatibilna faza SaaS arhitekture:

- uvedena je aplikacija `control_plane`;
- svaka župa ima jedinstveni tenant UUID i lifecycle status;
- uvedena su članstva korisnika po župi i tenant kontekst;
- uvedeni su modeli licenci, ručnih uplata, entitlementa i odluka o licenci;
- uvedeni su neizmjenjivi control-plane audit događaji;
- Django administracija prikazuje članstva, licence, uplate, tenant baze i audit;
- postojeća demo župa, korisnik i licenca migrirani su bez promjene postojeće frontend funkcionalnosti;
- svih 31 testova prolazi, nema sistemskih ni nedostajućih migracija.

Detaljni smjer nalazi se u `SAAS_ARHITEKTURA.md`.

## Točka na kojoj je razvoj zaustavljen

Pastoralni podaci još nisu fizički premješteni u zasebnu PostgreSQL bazu za svaku župu. Control plane i tenant kontekst su pripremljeni, ali fail-closed database router i produkcijsko provođenje licence još nisu uključeni.

## Sljedeća SaaS faza

1. Podići dvije testne tenant PostgreSQL baze.
2. Dodati fail-closed Django database router.
3. Migrirati jednu demo župu u njezinu tenant bazu.
4. Testirati da korisnik jedne župe nikada ne može dohvatiti podatke druge župe.
5. Uvesti izolirane cache ključeve, dokumente i pozadinske zadatke po tenantu.
6. Nakon provjere uključiti obavezno provođenje statusa licence.
7. Pripremiti kontrolirani postupak provisioninga, backupa, obnove i offboardinga župe.

## Nova ideja za razradu

Razmotriti opcionalni modul za izradu javne web-stranice župe. Preporučeni početni smjer je modul unutar iste platforme i control planea, ali s odvojenim javnim publishing slojem, domenama, predlošcima, cacheom i sigurnosnom granicom. Ne uvoditi ga u pastoralnu jezgru prije zasebnog MVP-a i potvrde interesa župa.

### Implementirani demo temelj

- javna web-stranica izdvojena je u samostalni projekt `website_project`;
- aktivacija se veže uz licencno pravo `public_website`;
- u lokalnom demo načinu zahtjev se automatski odobrava;
- automatski se kreiraju web-stranica, rezervirana poddomena i početni proizvodni build;
- frontend prikazuje napredak, dovršetak demo generiranja i objavu;
- objavljena demo stranica dostupna je na `/zupa/<subdomain>/`;
- produkcijski auto-activation ostaje isključen i kasnije se spaja na potvrđenu uplatu;
- stvarni statički generator, CDN publishing i uređivanje pojedinih javnih sekcija ostaju sljedeća faza ovog modula.

### Prošireni javni župni portal

- javna stranica sada prikazuje liturgijski dan i boju, današnje mise i redovni raspored;
- prikazuje samo obavijesti koje nisu označene kao interne;
- javni kalendar izostavlja privatne događaje;
- prikazuje pregled aktualnog ili objavljenog župnog listića bez izlaganja privatnih nakana i podnositelja;
- dostupni su tenant-specifični obrasci za krštenje, prvu pričest, krizmu i dogovor ukopa;
- dodane su sekcije o župi, župnom uredu, ispovijedi, kontaktima, karti, društvenim mrežama i donacijama;
- web-postavke imaju zasebna polja za javni telefon, e-mail, adresu, radno vrijeme, IBAN, primatelja i opis uplate;
- izdvojeni projekt ne pristupa bazi e-Župe i objavljuje isključivo unaprijed odobreni `published_snapshot`; obitelji, privatne bilješke, financije, podnositelji i sakramentalni zapisi nisu dio javnog snapshot-a;
- responzivni prikaz provjeren je na desktop i mobilnoj širini od 390 px.

## Cjenovni smjer

Detaljni radni troškovnik nalazi se u `CJENOVNI_MODEL_I_TROSKOVNIK.md`. Trenutačna preporuka je puna cijena od 500 EUR godišnje po župi, uz vremenski ograničenu pilot-cijenu od 200–300 EUR i odvojenu naplatu početnog postavljanja, neurednih migracija i posebnih prilagodbi.
