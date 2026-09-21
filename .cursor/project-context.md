# e-Župa — kontekst projekta

Aplikacija župnog ureda (Django 4.2+/5.x, PostgreSQL).
UI je na hrvatskom; identifikatori u kodu na engleskom. Korisnik prijave:
Tenant je jedna PostgreSQL schema (`django-tenants`). `Parish` ostaje
župa unutar te scheme. Domena (Host) bira tenanta.

Primarni dokument arhitekture baze: `MDs/DB_ARCHITECTURE_PROPOSAL.md`.

## Aplikacije

| Aplikacija | Vlasništvo |
|---|---|
| `core` | Samo apstraktne SCD/FACT baze |
| `pastoral` | Shell, auth, OTP, `Parish`, `Diocese`, `ParishMembership` |
| `zupa_vjernici` | `Person`, kanonska pripadnost (latinska / istočna), ulica, kućanstvo, posjete |
| `sakramenti` | Događaji, sudionici, details, priprava |
| `isprave` | Matične knjige, predlošci, potvrde |
| `liturgija` | Raspored misa, nakane, listić, kalendar |
| `financije` | Blagajna, računi, dugovanja, lukno default |
| `ured` | Kalendar, zadaci, vijeća, javne prijave, osnivački dekret |
| `pregled` | Nadzorna ploča (bez vlastitih tablica) |

## Persistencija

Izvor istine je ORM. `pastoral.services.operational_store` je adapter prema
postojećem camelCase UI ugovoru. `Parish.data` se na spremanju prazni.
`Parish.settings` ostaje JSON profil župe.

Član kućanstva je `Person` + otvoreni `HouseholdMembership`. Sakrament na
kartonu čita se iz `SacramentalEvent`, ne iz JSON liste. Vijeća su
`Council` + `CouncilMembership`. Prava ureda nisu `OfficeDirectoryRecord`
— Django groups + `ParishMembership`.

SCD2 čitanje: samo `date_to = 9999-12-31` (`Model.current`). Materijalna
izmjena ide kroz `save_new`. Povijest se zatvara, ne briše.

## Konvencije

- Imena tablica često još `pastoral_*` nakon razdvajanja aplikacija.
- Poslovna jedinstvenost otvorenog SCD2 reda: parcijalni UNIQUE na
  `public_identifier` (ili osoba) uz `date_to` otvoren.
- Novac: `DecimalField`. Vremenska zona: `Europe/Zagreb`.
- Ne izmišljati novi modul za tablicu koja već ima vlasnika.
- Dokumenti (DMS) ostaju otvoreno pitanje; `DocumentBinding` nije spremište datoteka.
