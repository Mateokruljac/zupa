# Database architecture — e-Župa

**Status: primary / mandatory.** This is the source of truth for domain models. `MDs/db_arhitecture.md` is the original brief only. New models, migrations, and ORM work must follow this file and the abstract bases in `core/models.py`.

Every persisted business model is one of:

| Kind | Abstract base (`core.models`) | Meaning |
|---|---|---|
| DIM SCD1 | `SCD1` | Overwrite in place (`unified_key`, `is_active`) |
| DIM SCD2 | `SCD2` | Versioned (`date_from` / `date_to`, open row = `9999-12-31`) |
| DIM SCD2A | `SCD2A` | SCD2 plus `is_active` |
| FACT A | `FCTA` | Transaction / event / registry line, UUID `id` |
| FACT B | `FCTB` | Same as FACT A with big-integer `id` (only if volume requires it) |
| Draft | `SCDD` | Staging before a DIM/FACT row exists |
| Report | `SCDR` | Read model / projection, not office writes |

`id` is the physical `record_id`. Do not invent a second PK. `content_hash` lives on SCD1, SCD2, FCTA, and FCTB. Call `save_new(...)` for SCD inserts/updates so unified keys and versioning stay consistent.

---

## A. Domain Overview

A Croatian Catholic parish office runs a small number of daily jobs:

1. **Know who belongs here** — households on streets, people in those households, who moved, who died, who still gets pastoral visits.
2. **Record sacraments as they happen** — baptism, first communion, confirmation, marriage, funeral, anointing — including preparation years for communion and confirmation.
3. **Keep official books** — matične knjige with sequential numbers that must still be true in thirty years.
4. **Run the liturgy week** — recurring Mass times, exceptions, intentions, stipend tracking, župni listić.
5. **Handle money simply** — lukno and gifts per family, ordinary parish cash, diocesan collections that are not parish money, construction campaigns, Mass offerings, incoming bills, who owes whom.
6. **Take public requests** — web forms for baptism, communion, confirmation, wedding, burial. Those are applications, not books.
7. **Run the office** — calendar, tasks, pastoral and economic councils, settings.

The priest does not think in FACT tables. He thinks: *obitelj Horvat, krštenje djeteta, upis u maticu, nakana za nedjelju, lukno za 2026.*

Existing product modules already match that: `zupa_vjernici`, `sakramenti`, `isprave`, `liturgija`, `financije`, `ured`, `pregled`, `pastoral`. Keep them.

---

## B. Proposed Modules

Keep the current Django apps. Shared SCD/FACT bases live in **`core`** (abstract models only). Domain tables stay in their owner apps.

### Module: `core`
Responsibility: DRY SCD/FACT/DIM abstract bases (`SCDD`, `SCDR`, `SCD1`, `SCD2`, `SCD2A`, `FCTA`, `FCTB`).
Owned models: none concrete.
Why: one file, one versioning/hash contract.

### Module: `pastoral`
Responsibility: tenant, users, staff membership, OTP.
Owned models: `Parish`, `Diocese`, `User`, `ParishMembership`, `OtpChallenge`.
Referenced models: church/jurisdiction/tradition FKs owned elsewhere.
Why: authentication and tenant scope are not parishioner data.

### Module: `zupa_vjernici`
Responsibility: people, households, streets, pastoral visits, church sui iuris enrollment.
Owned models: `ChurchSuiIuris`, `EcclesiasticalJurisdiction`, `Person`, `ChurchEnrollment`, `Street`, `Household`, `HouseholdMembership`, `HouseholdContributionYear`, `PastoralVisit`.
Referenced models: `Parish`.
Why: the card file of the parish.

### Module: `sakramenti`
Responsibility: sacramental facts, participants, sacrament-specific operational details, formation years.
Owned models: `SacramentalEvent`, `EventParticipant`, `BaptismDetails`, `MarriageDetails`, `FuneralDetails`, `AnointingDetails`, `FormationProgramYear`, `FormationCandidate`.
Referenced models: `Person`, `Parish`, `User`, `LiturgicalTradition`.
Why: a baptism is not a household field and not a register-book row.

### Module: `isprave`
Responsibility: official books, numbered entries, templates, certificate generation, registry audit.
Owned models: `RegisterBook`, `RegisterBookYear`, `RegisterEntry`, `GeneralRegisterEntry`, `RegisterTemplate`, `RegisterTemplateVersion`, `RegistryAuditEvent`.
Referenced models: `SacramentalEvent`, `Parish`.
Why: the book can exist without the operational workflow, and vice versa.

### Module: `liturgija`
Responsibility: Mass timetable, intentions, bulletin, imported liturgical calendar.
Owned models: `LiturgicalTradition`, `LiturgicalCalendarImport`, `LiturgicalCalendarEntry`, `MassScheduleSlot`, `MassException`, `MassScheduleLogEntry`, `MassIntention`, `BulletinLayout`, `BulletinIssue`.
Referenced models: `Parish`.
Why: weekly liturgy is not the civil calendar of parish events.

### Module: `financije`
Responsibility: parish cash movement, invoices, debts, default lukno amount.
Owned models: `FinanceSettings`, `CashbookEntry`, `Invoice`, `ParishDebt`.
Referenced models: `Parish`, optionally `Household` / `MassIntention` as links, not owners of money.
Why: money has one grain: a dated movement or a bill/obligation.

### Module: `ured`
Responsibility: office calendar, tasks, councils, public intake, lightweight document bindings, parish settings UI.
Owned models: `ParishCalendarEvent`, `OfficeTask`, `Council`, `CouncilMembership`, `PublicSubmission`, `Announcement`, `DocumentBinding` (until attachments are needed).
Referenced models: `Parish`, later `Person`.
Why: office work is not liturgy and not the register.

### Module: `pregled`
Responsibility: read-only dashboards.
Owned models: none.
Why: reporting must not become a second write model.

---

## C. Review of My Proposed Models

Every original item maps to a `core` base. FACT/SCD labels **are** the required classification. They describe office data, not a BI star schema.

| Original proposal | Recommended name | Base | Module | Grain | Keep / Change | Reason |
|---|---|---|---|---|---|---|
| SCD2 Family | `Household` | **SCD2A** | zupa_vjernici | One household identity; versions on address/surname/street/status | Keep as SCD2 | Close the current row on material change. Exclude `pastoral_notes` and `last_visit_on` from versioning. |
| SCD2 Family Member | `Person` **SCD1** + `HouseholdMembership` **SCD2** | SCD1 + SCD2 | zupa_vjernici | One person; one membership period | **Split** | Person overwrites; belonging is dated. |
| SCD1 Reference Data | `FinanceSettings` + enums | **SCD1** | financije | One settings row per parish | Keep as SCD1 | No generic key/value table. |
| FACT Family Contributions | `HouseholdContributionYear` + `CashbookEntry` | **FCTA** | zupa_vjernici / financije | One lukno year; one cash movement | **Split** | Two grains, both facts. |
| SCD2 Streets | `Street` | **SCD2A** | zupa_vjernici | One street identity | Keep as SCD2 | Baptisms snapshot street **name text**, not a live street row. |
| FACT Calendar | `ParishCalendarEvent` | **FCTA** | ured | One event (date not unique) | Keep as FACT | |
| FACT Mass Intention | `MassIntention` | **FCTA** | liturgija | One requested intention | Keep as FACT | |
| SCD1 Mass Schedule | `MassScheduleSlot` **SCD1** + `MassException` **FCTA** | SCD1 + FCTA | liturgija | Recurring slot; dated exception | Keep | Do not mix template and occurrence in one table. |
| FACT Parish Bulletin | `BulletinIssue` **FCTA**, `BulletinLayout` **SCD1** | FCTA / SCD1 | liturgija | One issue; one layout | Keep | |
| FACT Baptism | `SacramentalEvent` + `BaptismDetails` | **FCTA** | sakramenti | One baptism | Keep as FACT | Details 1:1, also FCTA. |
| FACT First Communion | `FormationProgramYear` **SCD1** + `FormationCandidate` **FCTA** + event **FCTA** | mixed | sakramenti | Year vs candidate vs confirmed event | **Split** | |
| FACT Confirmation | same pattern | mixed | sakramenti | same | **Split** | |
| FACT Funeral / Anointing | event + details | **FCTA** | sakramenti | One funeral / one anointing | Keep as FACT | |
| FACT Incoming Invoice | `Invoice` | **FCTA** | financije | One invoice | Keep as FACT | |
| SCD1 Debt Types | enum on `ParishDebt` | code enum | financije | — | **Change** | Not a table until parishes edit types. |
| FACT Receivables / Payables | `ParishDebt` | **FCTA** | financije | One obligation | **Merge** | `direction` on one fact. |
| FACT Economic / Pastoral Council | `Council` **SCD1** + `CouncilMembership` **SCD2** | SCD1 + SCD2 | ured | Council; membership period | **Split** | |
| FACT Events and Tasks | `ParishCalendarEvent` **FCTA** + `OfficeTask` **FCTA** | FCTA | ured | Event vs task | **Split** | Two facts, not one table. |
| FACT Public applications | `PublicSubmission` | **FCTA** | ured | One submitted form | **Merge** | Optional **SCDD** only if a staging copy is needed later. |

---

## D. Recommended Operational Model

Shared conventions (all business tables unless noted):

- Inherit the matching abstract from `core.models` (`SCD1`, `SCD2`, `SCD2A`, `FCTA`, rarely `FCTB`)
- PK: UUID `id` (the pattern’s `record_id`; use `FCTB` only when a big-integer key is justified)
- Tenant: required `parish_id` (FK `Parish`, `PROTECT` on historical/sacramental/finance; `CASCADE` only for pure children of a disposable parent)
- UI key: `public_identifier` unique per parish (or per parent) where the screen already uses string ids
- Audit: `created_at`, `updated_at`; `created_by` / `updated_by` on registers, sacraments, cashbook, invoices
- `content_hash` — see section O
- Money: `Numeric(12,2)`, EUR implied, no currency column
- Do not use `payload` for new fields; retire existing payload as columns are typed

Boolean names: `is_active`, `is_current`, `is_paid`, `is_cancelled`. Dates: `occurred_at` / `event_date` / `valid_from` — never a bare `date`.

### Identity and household

**`Person`** — Osoba  
Purpose: one natural person known to this parish.  
Grain: one person.  
Business key: none guaranteed; search by normalized name + DOB; optional later OIB unique per parish if collected.  
History: SCD1 on current name; sacramental snapshots elsewhere.  
Mutable: yes (current identity). Soft archive via `status`, no physical delete if sacraments exist.

Important fields:

| Field | HR | Type | Req | Mutable | In hash | Notes |
|---|---|---|---|---|---|---|
| `given_names` | Ime | varchar | yes | yes | yes | Current legal/pastoral name |
| `surname` | Prezime | varchar | yes | yes | yes | |
| `birth_surname` | Rođeno prezime | varchar | no | yes | yes | Maiden / birth surname |
| `sex` | Spol | enum | yes | restricted | yes | `female\|male\|unknown` |
| `date_of_birth` | Datum rođenja | date | no | restricted | yes | Unknown for some historical people |
| `place_of_birth` | Mjesto rođenja | varchar | no | yes | yes | Free text; no city table |
| `status` | Status | enum | yes | yes | no | `active\|merged\|archived` |
| `father_id` / `mother_id` | Otac / majka | FK Person | no | yes | no | Convenience; baptism snapshots win historically |

Keep `ChurchEnrollment` as dated sui iuris belonging (already SCD2-lite). Do not duplicate it.

**`Household`** — Kućanstvo / obitelj  
Purpose: current parish household card (what the priest calls obitelj).  
Grain: one household.  
Business key: none; display `surname` + address.  
History: **SCD2A**. `unified_key` is parish + household identity. Version on surname, street, house number, address, status.  
Fields: `surname`, `street_id`, `house_number` (add; today mashed into `address`), `address_line` (remainder), `phone`, `email`, `status` enum `active\|inactive\|moved\|deceased_household`, `preferred_mass`, `origin_place`, `pastoral_notes`, `last_visit_on`.  
Remove JSON `husband` / `wife` — those are people via membership.  
Remove member-level `sacraments` JSON — source of truth is sacramental models.

**`HouseholdMembership`** — Članstvo u kućanstvu  
Replaces `HouseholdMember` as identity.  
Grain: one person belonging to one household for one period.  
Business key: unique current membership `(household_id, person_id)` where `valid_until` is null.  
History: dated relation (`valid_from`, `valid_until`) — the only household SCD2 we need.  
Fields: `person_id` (required once cutover is done), `role` enum `husband\|wife\|child\|other` (Croatian labels in UI), `is_head`, `notes`, `sort_order`.  
Until cutover completes, `historical_name` may remain nullable for unmigrated strings.

**`HouseholdRelative`** — postpone / drop  
Non-resident relatives as free-text notes on the household unless they become `Person`. Do not keep a parallel person-ish table.

**`Street`** — Ulica  
Grain: one named street in the parish. **SCD2A**. Fields: `name`, `zone`, `sort_order`, `notes`, `is_active`. `unified_key` from parish + stable street identity. Current rows: `date_to = 9999-12-31`.

**`PastoralVisit`** — Pastoralna posjeta  
Grain: one visit. Mutable operational. FK `household_id` optional, `scheduled_on`, `is_done`, `visit_type`, `person_name` (until Person link), `address` snapshot, `priest`, `purpose`, `report`.

### Sacraments (summary; deep dive in E/F)

**`SacramentalEvent`** — Sakramentalni događaj  
Grain: one celebrated (or scheduled) sacrament of one type in one parish.  
Business key: `(parish_id, event_type, public_identifier)` when identifier set.  
Mutable until `locked`; then correction flow only.  
Shared fields already exist: `event_type`, `event_date`, `place_name`, `minister_id`, `minister_name` (snapshot), traditions, `status`, `source`.

**`EventParticipant`** — Sudionik  
Grain: one role on one event. Person FK **or** `historical_name`. Add snapshot fields: `snapshot_given_names`, `snapshot_surname` filled at confirm/lock. Roles: recipient, parent, godparent, spouse, witness, sponsor.

Typed 1:1 details stay: `BaptismDetails`, `MarriageDetails`, `FuneralDetails`, `AnointingDetails`.

**`FormationProgramYear` / `FormationCandidate`** — keep. Candidate is operational; linking `sacramental_event_id` is how a year becomes an official confirmation/communion fact.

### Registers — see G

### Liturgy

**`MassScheduleSlot`** — Recurring template: weekdays, time, location, celebrant, `valid_from`/`valid_until`, `no_mass`.  
**`MassException`** — Dated override (cancel/add).  
**`MassIntention`** — One request: `intention_date`, `mass_time`, `requested_by`, `intention_for`, `stipend`, `is_paid`, `status` enum `requested\|scheduled\|fulfilled\|transferred\|cancelled`, `notes`.  
Do **not** add `MassOccurrence` now. The priest schedules against date+time; exceptions cover feast days.

**`ParishCalendarEvent`** — Civil/pastoral event. `title`, `starts_on` (date), optional `starts_at`/`ends_at`, `is_all_day`, `place`, `event_type`, `description`. Date is **not** unique.

**`OfficeTask`** — `title`, `description`, `due_on`, `assignee_name` (or later user FK), `priority`, `is_done`, `category`.

**`BulletinIssue`** — generated view of a period; store layout JSON and publication status; pull intentions by date range at render time.

### Finance — see H

**`FinanceSettings`** — 1:1 parish: `lukno_default_amount`, later `bell_ringing_fee` if used.  
**`CashbookEntry`** — one money movement.  
**`Invoice`** — one vendor/customer invoice.  
**`ParishDebt`** — one obligation, `direction` `receivable\|payable`.  
**`HouseholdContributionYear`** — one calendar year of lukno/gift flags for one household (not the cash movement).

### Office

**`Council`** — `council_type` enum `pastoral\|economic`, optional title, `is_active`. One active row per type per parish is enough.  
**`CouncilMembership`** — `person_id` or `member_name`, `role`, `valid_from`, `valid_until`.  
**`PublicSubmission`** — intake; see J.  
**`Parish` settings** — keep JSON for theme/contact until a `ParishProfile` is worth typing. Not a generic ReferenceData table.

---

## E. Sacramental Architecture

Shared:

- `SacramentalEvent` (type, date, place, minister snapshot, status, source)
- `EventParticipant` (role + person and/or historical/snapshot names)
- lock / correct / do not cascade-delete
- optional `RegisterEntry` 1:1 when entered in the book

Not shared (typed details):

| Sacrament | Extra | Why separate |
|---|---|---|
| Baptism | godparent cert, stipend, parents/godparents roles | Canonical register of identity |
| Marriage | preparation, documents, two spouses, witnesses, stipend | Already first-class in the product |
| Funeral | death date, cemetery, family contact, requiem Mass | Death ≠ funeral |
| Anointing | time, address, contact, completed; **no stipend** | Privacy, pastoral visit |
| First communion / Confirmation | formation year + candidates; sponsor; school | Group sacrament, not a singleton like baptism |

Do **not** create one fat `Sacrament` row with nullable columns for godparents, spouses, cemetery, and school.

Marriage is **required** in the architecture even though it was missing from the initial list. The app already has events, details, books (`vjenčanja`), and a public form.

First communion book type should be added to `RegisterBook.RegistryType` when a parish actually keeps that book. Until then, the formation year plus a locked `SacramentalEvent` is enough.

Duplicate sacrament rule: at most one **locked** baptism (and similarly confirmation, for this parish’s books) per `Person`. Application-enforced plus unique partial index where `role=recipient` and event status is locked. Historical imports may use `legacy_imported` without forcing uniqueness blindly.

---

## F. Baptism Deep Dive

```
Person (current name)
    │
    ├── HouseholdMembership (current household, dated)
    │
    └── EventParticipant role=recipient
            └── SacramentalEvent type=baptism
                    ├── BaptismDetails (ops: stipend, godparent cert)
                    ├── EventParticipant role=parent (×2, optional unknown father)
                    ├── EventParticipant role=godparent (1–2, not required to be Person)
                    ├── minister_name snapshot (+ optional User)
                    └── RegisterEntry (optional 1:1)
                            └── RegisterBookYear → RegisterBook
```

**Recipient.** Prefer `person_id`. At lock time copy `snapshot_given_names`, `snapshot_surname`, `snapshot_sex`, `snapshot_date_of_birth`, `snapshot_place_of_birth` onto the participant (or onto `BaptismDetails` if we want one place — recommend **participant snapshots** so parents/godparents follow the same rule).

**Parents.** Participants with role `parent` plus optional `parent_side` `father\|mother`. Names as recorded in the book stay on the participant even if `Person.surname` later changes. `Person.father_id` is a convenience for the living card, not the register.

**Godparents.** Same participant model. May be only `historical_name` (kum from another parish). Certificate received stays on `BaptismDetails`.

**Minister.** `minister_id` if staff user; always persist `minister_name` as written.

**Place / parish.** `place_name` + owning `parish_id`. Emergency baptism elsewhere: still this parish’s book if they record it; `place_name` holds the hospital/other church.

**Register.** `RegisterEntry.entry_number` unique per book-year. `page_number` optional. `entry_reference` for inherited numbering text.

**Immutable after lock.** Event date, place, minister_name, participant snapshots, register number. Operational stipend flags may remain editable or move to cashbook — recommend: after lock, stipend only via finance, not by editing the baptism.

**Annotations / corrections.** Do not overwrite a locked event. Create a new `RegisterEntry` with `previous_entry_id` and `correction_reason`; mark old as `corrected`. Optional later: `RegisterAnnotation` (short note, date, author) — **future**, not now; `correction_reason` + registry audit is enough.

If Ana Horvat is baptized in 2010 as Ana Kovač, and she marries and her `Person.surname` becomes Horvat in 2035, the locked participant snapshot and register entry still read **Kovač**. The family card shows Horvat. Certificates print from the register snapshot, not from `Person`.

---

## G. Sacramental Registers / Matične knjige

Keep the existing three-level book:

```
RegisterBook          (volume, type, years span, status)
 └── RegisterBookYear (calendar year, next_entry_number)
      └── RegisterEntry 1:1 SacramentalEvent
```

This is the simplest design that matches the current screen (book → year → lines) and official numbering.

- **Do not** introduce a generic `RegisterEntry` that is also baptism/marriage/funeral without `SacramentalEvent`. Sacramental lines always point at an event. `GeneralRegisterEntry` stays for non-sacramental “ostalo” books only.
- Numbering: `UNIQUE (register_book_year_id, entry_number)` where number is not null. Allocate from `next_entry_number` in a transaction.
- Volume/year: book has `volume`, `year_from`, `year_until`; year rows allow empty years.
- Corrections: chain `previous_entry`; locked rows are immutable (already coded).
- Snapshots: on participants at lock, not live Person.
- Certificates: generate from `RegisterEntry` + template version; do not store a second copy of names on the certificate row until a Document model exists. Print log can wait (audit event is enough).

First communion is often a group ceremony; many parishes do **not** keep a separate communion book. Do not force a book. Confirmation and marriage books already exist in `RegistryType`.

---

## H. Finance Architecture

Four **meanings**, one **movement table**, four **ledger codes** (already in `financije/ledgers.py`):

| Ledger | Meaning | In parish balance? |
|---|---|---|
| `crkveni` | Ordinary parish money (lukno, gifts, bills, pastoral) | Yes |
| `kolekte` | Diocesan collections held in transit | No |
| `gradnja` | Construction / named campaign | No (separate pot) |
| `misne` | Mass offerings / obligations | No |

**Share:** `CashbookEntry` — grain: one dated inflow or outflow on one ledger.

Fields: `entry_date`, `entry_type` (`inflow\|outflow` — replace `ulaz` as stored English code with HR labels in UI), `ledger`, `category` (configurable-ish but start with current enum: lukno, donacija, rezije, …), `amount` > 0 CHECK, `payment_method`, `description`, optional `household_id`, optional `mass_intention_id`, `content_hash`.

**Keep separate:**

- `HouseholdContributionYear` — did this family settle lukno / gift for year Y? Amounts here are **plan/status**. When money actually hits the till, write a cashbook row (same year, category `lukno`). Do not pretend the yearly flag is the ledger.
- `Invoice` — vendor document, VAT, due date, payment status. Paying it should create/link cashbook outflow; do not collapse invoice into cashbook.
- `ParishDebt` — who owes whom, `direction`, `amount`, `due_on`, `is_paid`. Partial payments: not now; one `paid_amount` if needed later. Settlement may link a cashbook id in a nullable `settled_by_entry_id` later — optional.
- Mass stipend on `MassIntention` is **operational** (is this intention paid?). Money still belongs in `misne` cashbook when received. Same idea as lukno flags vs cash.

**Do not build:** chart of accounts, double-entry, Fund entity table, campaign entity table (ledger `gradnja` + description is enough until there are concurrent campaigns), multi-currency.

Bell-ringing fee: a `FinanceSettings` decimal plus cashbook category, not a new model.

---

## I. Calendar, Masses and Mass Intentions

```
MassScheduleSlot (recurring template)
MassException    (this week/feast differs)
        │
        ▼  priest picks a date+time
MassIntention    (request: for whom, from whom, stipend, status)
        │
        ▼  paid money
CashbookEntry ledger=misne

ParishCalendarEvent  — parish life (concert, meeting). Not a Mass.
OfficeTask           — do this by Friday.
BulletinIssue        — prints intentions and events for a date range.
```

Intention lifecycle: `requested → scheduled → fulfilled | transferred | cancelled`. Reschedule = change `intention_date` / `mass_time` while not fulfilled. No separate MassObligation entity: unpaid vs paid is `is_paid` + stipend amount; the `misne` ledger is the money pot.

Do not generate a row per Sunday from the template.

---

## J. Public Applications

Keep **one** `PublicSubmission`.

`form_type` enum: `baptism`, `first_communion`, `confirmation`, `marriage`, `funeral` (store English; UI already uses `prijava-krsenje` etc. — map, do not create five tables).

`status` enum: `submitted → under_review → approved → converted | rejected | cancelled`.

Store the form as `form_data` JSON **because the intake shape is wide and form-versioned**. Authoritative parish data is created only on **convert**:

1. Find or create `Person` (and parents as persons if enough data).
2. Find or create `Household` / membership.
3. Create `SacramentalEvent` draft **or** `FormationCandidate`, never a locked register line.
4. Set `converted_event_id` / `converted_candidate_id` / `converted_person_id` so the submission is a pointer, not a second register.

GDPR consents stay on the submission (timestamp + version). They are not copied into the baptism book.

Wedding and burial public forms are in scope of the same pipeline (already in the product).

---

## K. Documents

**Not a full Document/Attachment model now.**

Certificates are generated from register + templates (`RegisterTemplateVersion`). Invoice scans and application files are not first-class today. `DocumentBinding` payload is a leftover — leave it frozen; do not grow it.

Add `Attachment` later when a priest must upload a scan of a historical page or an invoice PDF. Minimum then: `id`, `parish_id`, `stored_path`, `original_filename`, `mime_type`, `category` enum, `uploaded_at`, `uploaded_by`, and **typed FKs** (`register_entry_id` xor `invoice_id` xor `public_submission_id`) — not a polymorphic `object_id`.

Until that pain is real, postpone.

---

## L. Missing Models

### Required

| Model | Reason | Module | Grain |
|---|---|---|---|
| `HouseholdMembership` | Person must leave/join households without losing sacraments | zupa_vjernici | one membership period |
| Marriage (already exists) | Parish cannot omit vjenčanja | sakramenti | one marriage event |
| `Council` + `CouncilMembership` | Replace JSON `CouncilBundle` | ured | council; membership period |

### Strongly recommended

| Model | Reason | Module | Grain |
|---|---|---|---|
| Participant snapshot columns | Stop silent register mutation | sakramenti | per participant |
| `MassIntention.status` enum | Requested/scheduled/fulfilled is currently implicit | liturgija | one intention |
| First communion on `RegisterBook.RegistryType` | Only if books are kept | isprave | book type |
| Typed `house_number` on household | Public forms already collect it | zupa_vjernici | household |

### Optional / future

Cemetery/grave, OIB unique, `RegisterAnnotation`, `MassOccurrence`, `FundraisingCampaign`, `Attachment`, `ParishProfile` typed, inter-parish Person, full certificate issuance log, `HouseholdAddressHistory`, phase-two collections (`deanery`, room bookings, …).

Do not build these now.

---

## M. Relationship Map

```
Parish
├── Street
│    └── Household
│         ├── HouseholdMembership ── Person
│         ├── HouseholdContributionYear
│         └── PastoralVisit
├── Person
│    ├── ChurchEnrollment
│    ├── EventParticipant ── SacramentalEvent
│    ├── FormationCandidate
│    └── CouncilMembership
├── SacramentalEvent
│    ├── BaptismDetails | MarriageDetails | FuneralDetails | AnointingDetails
│    ├── EventParticipant
│    └── RegisterEntry ── RegisterBookYear ── RegisterBook
├── FormationProgramYear ── FormationCandidate
├── MassScheduleSlot / MassException
├── MassIntention
├── ParishCalendarEvent
├── OfficeTask
├── CashbookEntry
├── Invoice
├── ParishDebt
├── FinanceSettings
├── PublicSubmission  (optional FKs to Person / Event / Candidate after convert)
└── Council ── CouncilMembership
```

Person is **not** a child of Household. HouseholdMembership is.

---

## N. Historical Strategy

Every model uses a `core` base. Mapping:

| Base | Used for |
|---|---|
| **SCD1** | `Person`, `Parish`, `Diocese`, `User`, `ChurchSuiIuris`, `EcclesiasticalJurisdiction`, `LiturgicalTradition`, `FinanceSettings`, `Council`, `BulletinLayout`, `RegisterTemplate`, `RegisterBook`, `RegisterBookYear`, `FormationProgramYear`, `MassScheduleSlot` |
| **SCD2** | `HouseholdMembership`, `ChurchEnrollment`, `CouncilMembership`, `ParishMembership` |
| **SCD2A** | `Household`, `Street` |
| **FCTA** | Sacraments, participants, details, candidates, register entries, cashbook, invoices, debts, calendar, tasks, visits, intentions, exceptions, bulletin issues, public submissions, announcements, audit events, OTP (no secret fields in hash) |
| **FCTB** | Do not use unless a table is proven high-volume; current `Parish` integer PK is legacy, target SCD1 UUID |
| **SCDD** | Optional future public-form drafts |
| **SCDR** | Optional future `pregled` read models |
| Snapshot columns | EventParticipant names at lock; `minister_name` |
| Event sourcing | **Not used** |

Household/street SCD2 versions **material** fields only (`save_new(..., exclude=...)`). Phone/email/notes stay in-place on the current household row so a typo does not clone the family.

Open SCD2 row: `date_to = OPEN_ENDED_VALID_TO` (`9999-12-31`). Unique current: `(unified_key)` where `date_to` is open.

---

## O. Hash Strategy

Field name: `content_hash` (varchar 64). The brief’s `hash` is this column.

**Purpose:** detect accidental or concurrent change of business content; support later sync/export; integrity of locked register rows. Not encryption, not deduplication primary key, not OTP.

**Generation:** SHA-256 hex of canonical JSON, implemented on `ContentHashedModel.save()` in `core/models.py`. Override `content_hash_field_names()` per model when the default is wrong.

**Included:** business attributes and stable FK ids that define meaning (`person_id`, `event_date`, amounts, names).

**Excluded:** `id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `content_hash` itself, search `normalized_*`, `payload` leftovers, `public_identifier` if it is only a UI handle (include it if it is printed as a business reference).

**Relations:** include FK ids, not nested related hashes (avoids cascade recomputes). Participant rows hash themselves; the event hash includes participant ids + their hashes only if we need a rollup — **recommend event hash = event columns only**; participants hash separately.

**SCD:** membership rows hash their own period fields. Do not hash “the family through time”.

**Index:** btree index optional; **not unique**. Collisions are not the point; equality checks are.

**Required on:** Person, Household, HouseholdMembership, Street, sacramental events/details/participants, register books/entries, cashbook, invoice, debt, mass intention, public submission, formation year/candidate, council membership.

**Skip:** none of the DIM/FACT tables. Only omit **fields** that are secrets (`OtpChallenge.code`) or dump JSON (`raw_data`).

---

## P. Data Integrity

Database should enforce:

- `UNIQUE (parish, public_identifier)` where UI ids exist
- `UNIQUE (register_book_year, entry_number)` where number not null
- `UNIQUE (parish, event_type, public_identifier)` where identifier not empty
- Partial unique: one current SCD2/SCD2A row per `unified_key` (`date_to = 9999-12-31`)
- Partial unique: one current `HouseholdMembership` per person (open `date_to`)
- Partial unique: one current confirmed `ChurchEnrollment` per person (already exists)
- `UNIQUE (parish, user)` on `ParishMembership` (exists)
- CHECK amount > 0 on cashbook; CHECK `valid_until >= valid_from`
- CHECK participant has `person_id` OR non-empty historical/snapshot name (exists)
- FK `ON DELETE PROTECT` for Person, events, register, cashbook
- No CASCADE from Parish to sacraments/registers (today some operational tables CASCADE — **change to PROTECT** for anything historical)
- Intention: do not delete fulfilled intentions; status `cancelled`
- Public submission: `converted_*` FKs set only in `converted` status (app + optional CHECK)
- Locked event/entry: already blocked in `save()`/`delete()`; keep it
- Money: never Float
- Duplicate locked baptism per person: unique index on participant (person, role=recipient) joined to locked baptism events — implement as unique constraint on a generated stored pair or application + periodic check if the join unique is awkward in Django

Application still validates workflows; the database catches the expensive mistakes.

---

## Q. Simplification Review

Intentionally **not** introducing:

- Extra history tables besides SCD2 `date_from`/`date_to` on the same model
- Star-schema FACT/DIM reporting copies (`SCDR`) until pregled needs them
- Generic `ReferenceData` / EAV
- Generic `Sacrament` God-table
- Separate public application tables per sacrament
- Separate receivable vs payable tables
- `Fund`, `Campaign`, `MassOccurrence`, `MassObligation` entities
- Combined Event+Task model
- `FamilyMember` as a person
- `HouseholdRelative` as a long-term model
- Cemetery plot registry
- Document management
- Event sourcing
- Multi-currency
- Database-per-parish router
- `FCTB` by default (UUID `FCTA` / SCD UUID `id` is the project standard)

`core` exists only for abstract bases. Domain tables stay in owner apps.

Removed vs current code (target): `Household.husband`/`wife` JSON, `HouseholdMember.sacraments` JSON, `Parish.data` as store, `CouncilBundle` payload, new fields in `payload`.

---

## R. Final Recommended Model Inventory

`core` — abstract only: `SCDD`, `SCDR`, `SCD1`, `SCD2`, `SCD2A`, `FCTA`, `FCTB`

### pastoral
- Parish — **SCD1**
- Diocese — **SCD1**
- User — **SCD1**
- ParishMembership — **SCD2**
- OtpChallenge — **FCTA** (exclude `code` from hash)

### zupa_vjernici
- ChurchSuiIuris, EcclesiasticalJurisdiction — **SCD1**
- Person — **SCD1**
- ChurchEnrollment — **SCD2**
- Street — **SCD2A**
- Household — **SCD2A**
- HouseholdMembership — **SCD2**
- HouseholdContributionYear — **FCTA**
- PastoralVisit — **FCTA**

### sakramenti
- SacramentalEvent, EventParticipant, BaptismDetails, MarriageDetails, FuneralDetails, AnointingDetails — **FCTA**
- FormationProgramYear — **SCD1**
- FormationCandidate — **FCTA**

### isprave
- RegisterTemplate — **SCD1**
- RegisterTemplateVersion — **SCD1** (published versions are overwrite-protected; new version = new row)
- RegisterBook, RegisterBookYear — **SCD1**
- RegisterEntry, GeneralRegisterEntry, RegistryAuditEvent — **FCTA**

### liturgija
- LiturgicalTradition — **SCD1**
- LiturgicalCalendarImport, LiturgicalCalendarEntry — **FCTA**
- MassScheduleSlot — **SCD1**
- MassException, MassScheduleLogEntry, MassIntention, BulletinIssue — **FCTA**
- BulletinLayout — **SCD1**

### financije
- FinanceSettings — **SCD1**
- CashbookEntry, Invoice, ParishDebt — **FCTA**

### ured
- ParishCalendarEvent, OfficeTask, PublicSubmission, Announcement, DocumentBinding — **FCTA**
- Council — **SCD1**
- CouncilMembership — **SCD2**

### pregled
- none yet; future dashboards are **SCDR**

### Future (not inventory)
- Attachment **FCTA**, RegisterAnnotation **FCTA**, FundraisingCampaign **SCD1**, cemetery, phase-two office collections

---

## S. Architectural Decisions

| Decision | Recommendation | Reason |
|---|---|---|
| Primary architecture file | `MDs/DB_ARCHITECTURE_PROPOSAL.md` | Mandatory source of truth |
| SCD/FACT DRY | `core/models.py` only | One `save_new` / hash / validity contract |
| Person vs FamilyMember | `Person` SCD1 + `HouseholdMembership` SCD2 | Stable human vs dated belonging |
| SCD2 Family | **Yes, SCD2A `Household`** | Address/surname history without a second history table |
| Street history | **SCD2A** + name snapshot on sacraments | Book text must not follow a later rename |
| Baptism snapshots | Snapshot names/DOB on participants at lock | Person SCD1 will change |
| Sacramental register | Book → year → entry 1:1 event; books DIM, entries FACT | Matches paper books |
| Generic vs separate sacraments | Shared event FACT + typed detail FACT | Avoids nullable cemetery-on-baptism |
| Finance / funds | Cashbook FACT + four ledger codes | One till, four meanings |
| Events vs tasks | Two FCTA models | Happens-at vs must-complete |
| Document model | Postpone | Certificates generate |
| Public applications | One FCTA `PublicSubmission` | Convert to Person/event |
| Councils | Council SCD1 + membership SCD2 | Queryable history |
| Hash | `content_hash` on SCD/FACT bases | Implemented in `ContentHashedModel` |
| PK | UUID `id` as `record_id`; FCTB only if needed | Matches existing parish tables |
| Marriage | Required FCTA | Already in the product |
| Mass occurrences | Do not add | Template SCD1 + exception FACT |
| Debts | One FCTA, `direction` | Same fields both ways |

---

## Mapping from current code

1. Inherit `core` bases; add `unified_key` / `date_from` / `date_to` / `is_active` where the type requires them.
2. Use `save_new(unified_key_origin_fields=...)` for SCD writes.
3. Introduce `HouseholdMembership` and backfill from `HouseholdMember` + husband/wife JSON; attach `Person`.
4. Snapshot columns on `EventParticipant` at lock.
5. Replace `CouncilBundle` with `Council` / `CouncilMembership`.
6. Type `PublicSubmission.status` / `form_type`; add converted FKs.
7. Stop writing new attributes into `payload`.
8. PROTECT historical FKs.

`Diocese` and `ParishMembership` already inherit `FCTA` timestamps/`content_hash` via `UUIDTimestampedModel`. They still need the remaining SCD1/SCD2 columns in a later migration.

Existing forms remain evidence: family form stays household-shaped; member rows should pick a Person. Baptism form fields (`childName`, `parents`, `godparents`, `registryNo`) map to event + participants + register, not to one JSON blob. Do not let the camelCase UI contract dictate new columns named `childName`.
