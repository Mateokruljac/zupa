# Evidencija audita i kontroliranog refaktoriranja

Datum završnog pregleda: 2026-10-29  
Grana: `features/django-app`  
Status: ponovni audit nakon pulla je proveden; promijenjeni kod je verificiran.

## Opseg i polazno stanje

- Izvor inventara bio je `git ls-files`, dopunjen relevantnim untracked
  first-party `.py` datotekama. Prije ovog zapisa inventar je imao 559 praćenih
  i 8 novih Python datoteka.
- Zatečene staged `.cursor` izmjene korisnika (dvije nove rules datoteke i dva
  premještanja u `rules_bckp`) sačuvane su i nisu prepisane.
- Autoritativno okruženje je Docker: Python 3.13, Django 5.2.16 i PostgreSQL s
  `django-tenants`. Host `python.exe` nije bio izvršiv, pa nije korišten drugi
  interpreter ni zamjenska baza.
- Početni `manage.py check` i `makemigrations --check --dry-run` prošli su.
  Početni puni test pronašao je samo 6 testova i imao jedan postojeći pad:
  kartica obitelji nije označila nepostojeći `streetId` kao prazninu podataka.
  Razlog malog broja testova bio je nedostajući `liturgija/tests/__init__.py`.

## Evidencija pokrivenosti

Status u retku vrijedi za svaku datoteku koja odgovara navedenoj skupini.
Povijesne migracije pregledane su radi modela i pretpostavki, ali nisu stilski
prepravljane.

| Skupina | Obuhvat | Status | Napomena |
| --- | ---: | --- | --- |
| Izmijenjeni aplikacijski Python | 13 `.py` | verified | `core/utils.py`; adapteri u `financije`, `liturgija`, `ured` i `zupa_vjernici`; permission/public-form tokovi u `pastoral`; dashboard u `pregled`. Pojedinačne odgovornosti navedene su u serijama ispod. |
| Preostali aplikacijski Python | 200 `.py` | reviewed-no-change | Pregledani modeli, viewovi, forme, servisi, URL-ovi, middleware, commandi i integracije; nije nađena opravdana promjena unutar zadanih granica. |
| Povijesne migracije | 25 `.py` | reviewed-no-change | Nije potrebna nova migracija; drift provjera prolazi. |
| Testovi i test support | 14 `.py` nakon izmjena | verified | Dodana su package discovery obilježja i fokusirani regresijski testovi. |
| Django predlošci i tekstualni e-mail predlošci | 65 `.html` + 6 `.txt` | verified | Pregledani ugovori konteksta, forme/CSRF i `safe` uporabe; svih 65 HTML predložaka se kompilira. |
| Frontend JavaScript | 23 `.js` | verified | Pregledani fetch/action ugovori, DOM sinkovi i storage; svi prolaze `node --check`. |
| Ručno održavani CSS | 4 `.css` | reviewed-no-change | Uključuje veliki postojeći `styles.css`; nije rađeno nevezano masovno formatiranje. |
| Izmijenjeni manifest i evidencija | `requirements.txt`, ovaj zapis | verified | Uklonjen je dupli dependency zapis; evidencija je usklađena sa završnim stablom i provjerama. |
| Preostala dokumentacija, konfiguracija i mali podaci | README/MD/TXT, Docker, rules te liturgijski JSON/CSV | reviewed-no-change | Pročitane repo upute, sigurnosni zahtjevi i arhitekturne odluke; nije opravdana dodatna promjena. |
| Praćeni generirani artefakti | 185 `.pyc` | excluded-generated | Binarni cache nije analiziran ni mijenjan kao izvorni kod. |
| Ignorirani cache/lokalni podaci | `**/__pycache__/**`, lokalni SQLite, cache/build output | excluded-generated | Nisu first-party izvor. Ignorirane mape s relevantnim nazivom provjerene su; nisu skrivale tekstualni izvor. |
| Osjetljiva konfiguracija | `.env` | excluded-sensitive | Provjerena je prisutnost i struktura referenci kroz settings/Docker bez ispisa vrijednosti. |
| Vendored/third-party izvor i mediji | nema praćenog izvora u ovoj skupini | excluded-third-party | Dependencies se dobavljaju iz `requirements.txt`; nema vendored koda za zaseban audit. |

Otvoreni nalazi imaju status `finding-open`; nijedna druga first-party tekstualna
datoteka iz inventara nije ostala `pending` ili `blocked`.

## Nalazi i provedene serije

### 1. Ovlasti domenskih stranica — P0, verified

`pastoral/decorators.py` je čitao slug samo iz keyword argumenata, dok su ga
factory viewovi slali pozicijski. Zahtjev za npr. blagajnu zato je izgledao kao
dashboard i mogao je zaobići zabranu modula. Factory sada koristi keyword,
dekorator obrambeno podržava oba oblika, a nepoznata uloga ili stranica više ne
nasljeđuje župnikove ovlasti. Dodani su regresijski testovi.

### 2. Integritet paralelnih read-modify-write operacija — P1, verified

Javne prijave i dashboard toggle učitavali su, mijenjali i spremali zajedničko
stanje bez zaključavanja parish retka. Paralelni zahtjevi mogli su prepisati
noviju promjenu. Kritični dijelovi sada koriste `transaction.atomic()` i postojeći
`ParishDataService.lock_for_update()`. Slanje e-maila ostaje izvan transakcije i
izvršava se tek nakon uspješne pohrane.

### 3. Test discovery i postojeća kartica obitelji — P1, verified

Dodan je `liturgija/tests/__init__.py`, pa puni runner otkriva liturgijske testove.
Kartica obitelji sada tretira i zastarjeli/nepostojeći `streetId` kao nedostajuću
teritorijalnu pripadnost, što odgovara postojećem testu i UI mogućnostima.

### 4. Zajedničke legacy UI ↔ ORM pretvorbe — P2, verified

Identična tolerantna pravila za ISO datume, prazni datum i decimalni iznos bila
su kopirana kroz financije, liturgiju, ured i kućanstva. Kanonske funkcije sada
su u `core.utils`; kompatibilni stari privatni nazivi ostaju kao aliasi zbog
mogućih izvanrepozitorijskih pozivatelja. Dodani su karakterizacijski testovi.

### 5. Robusnost administracijskog filtera i dependency manifest — P2, verified

Neispravan `year` query više ne ruši stranicu javnih prijava, nego koristi
tekuću godinu. Dupli `django-jsonform==2.23.2` uklonjen je iz requirementsa.

## Otvoreni nalazi

| Prioritet | Lokacija / dokaz | Rizik i preporučeni sljedeći korak | Status |
| --- | --- | --- | --- |
| P1 | `pastoral.models.ParishMembership`, provisioning i request kontekst | Membership model postoji, ali provisioning/middleware ne postavljaju dosljedno `request.tenant_context`/`request.parish`. Potrebna je zasebna odluka o migraciji postojećih korisnika, provisioningu i tenant middlewareu prije promjene produkcijskog ugovora. | finding-open |
| P1 | `MDs/PUBLIC_FORMS_SECURITY_REQUIREMENTS.md` i javne forme | Rate limiting, honeypot, retention i potpun audit trail dokumentirani su kao zaseban sigurnosni paket, ali još nisu implementirani. Ne uvoditi parcijalno bez odluke o storageu i operativnoj politici. | finding-open |
| P2 | rich-HTML sadržaj listića / `safe` renderiranje | Klijentska sanitizacija nije jednaka server-side sigurnosnoj granici. Definirati dopušteni HTML i sanitizirati pri upisu ili renderiranju, uz testove postojećih layouta. | finding-open |
| P3 | 185 praćenih `.pyc` i ograničena izvorna testna baza | U zasebnoj housekeeping promjeni ukloniti cache iz Git indeksa i postupno dodati testove glavnih cross-app tokova. To nije miješano s funkcionalnim refaktoriranjem. | finding-open |

## Verifikacija

Izvršeno u izoliranom Docker/PostgreSQL razvojnom okruženju, bez slanja stvarnih
e-mailova, produkcijskih migracija ili produkcijskih podataka:

- `docker compose run --rm --no-deps web python manage.py test core.tests zupa_vjernici.tests liturgija.tests`
  — 32 testa, prolaz.
- `docker compose run --rm --no-deps web python manage.py test`
  — 38 testova, prolaz; Django system check bez nalaza.
- Kompilacija svih Django HTML predložaka kroz configured Django template engine
  — 65/65 prolazi.
- `node --check` za svih 23 first-party JavaScript datoteka — prolaz.
- `git diff --check` — prolaz; Git prijavljuje samo informativnu LF/CRLF konverziju
  za dvije postojeće radne datoteke.
- `docker compose run --rm --no-deps web python manage.py check`
  — prolaz, bez nalaza.
- `docker compose run --rm --no-deps web python manage.py makemigrations --check --dry-run`
  — prolaz, nema promjena.

Kompatibilne granice su očuvane: nisu mijenjani javni URL-ovi, payloadi, output
dict ključevi, shema baze, povijesne migracije ni dependency verzije. Namjerne
promjene ponašanja ograničene su na dokumentirane sigurnosne i korektnosne
ispravke iz nalaza 1, 2, 3 i 5.

## Ponovni audit nakon pulla

Ovaj odjeljak je aktualni zapis i nadomješta ranije brojke verifikacije.
Pregledan je `HEAD` 61c7bd8 i svih 42 Python datoteke promijenjene zadnjim
pullom, uz ponovljene projektne pretrage i provjere svih ostalih skupina.

- Inventar: 571 praćena + 12 relevantnih novih putanja; 215 aplikacijskih
  Python datoteka, 28 migracija, 17 testnih datoteka, 66 HTML predložaka,
  27 JavaScript i 4 CSS datoteke te 185 izuzetih praćenih `.pyc` artefakata.
- Prijavljeni import uzrokovao je prijelaz s privatnih na javna imena u
  `core.utils` bez stabilnog ugovora za parcijalni pull. Pozivatelji sada uvoze
  legacy exporte pod opisnim lokalnim aliasima; javni i legacy exporti ostaju
  isti callable objekti i pokriveni su testom.
- `pastoral.services.dates.parse_iso_date` sada koristi isti shared helper
  umjesto još jedne kopije. Stroži sakramentalni parser ostaje odvojen jer
  namjerno prihvaća samo puni datum, ne datetime prefiks.
- Dekorator ovlasti sada izvodi domensku stranicu i iz `resolver_match` kada
  zaseban view nema `page` argument, čime export i slične grane ne izgledaju
  kao dashboard.
- Uplate čuvaju eksplicitnu nulu; nulta uplata ne postaje zadani dug. Brisanje
  nepostojećeg člana/uplate vraća `not_found`, a obiteljski dar ne proizvodi
  podsjetnik za lukno.
- Pull je promijenio ugovor kartice obitelji: postojeći `streetId` bez učitanog
  popisa ulica nije praznina. Ranija stroža korekcija je uklonjena.

Aktualna verifikacija: 47/47 Django testova, 66/66 kompiliranih predložaka,
27/27 JavaScript syntax provjera, Django system check bez nalaza i bez
migration drifta.

### Novi operativni blokatori migracija

- P0, `pastoral/migrations/0003_remove_parish_diocese_delete_diocese.py`:
  lokalno je već označena primijenjenom i briše `Diocese`/FK bez data migracije
  u `EcclesiasticalJurisdiction`. Agregatna provjera nalazi jednu župu bez
  jurisdikcije, nula jurisdikcija i sačuvan legacy naziv u settingsu. Potreban je
  zaseban forward-only prijenos; povijesna migracija nije prepisana.
- P1, `zupa_vjernici/migrations/0004_split_church_donations_into_categories.py`:
  lokalno je primijenjena i trenutni podaci su prošli (maksimalni ID ima 10
  znakova; devet `-dar` redaka). Ipak ima `noop_reverse`, a na drugom skupu
  podataka dodavanje `-dar` može prekoračiti `public_identifier(max_length=64)`
  ili kolidirati s postojećim identifikatorom. Prije drugih deploymenta treba
  pregledati stvarne ID-eve.
