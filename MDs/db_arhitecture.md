# BRIEF (not the source of truth)

The **mandatory / primary** architecture is:

`MDs/DB_ARCHITECTURE_PROPOSAL.md`

Shared SCD/FACT bases: `core/models.py`.

The text below is the original design prompt. Do not treat it as the current schema.

---

You are acting as a Principal Data Engineer, Database Architect, Software Architect, and Domain Analyst.

The project is a **Parish Management System** for managing the operational, sacramental, financial, pastoral, and administrative activities of a Catholic parish.

Your responsibility in this phase is to design the **database architecture and domain model only**.

Do NOT implement code yet.

Do NOT create migrations yet.

Do NOT generate ORM models yet.

Do NOT modify application code yet.

The goal is to first establish a simple, coherent, maintainable, historically correct database architecture.

---

# 0. FIRST: UNDERSTAND THE PROJECT

You should already have access to the existing project through Cursor.

Before analyzing the proposed models, inspect the existing project and understand:

* module structure,
* architecture,
* existing entities/models,
* existing naming conventions,
* IDs and key strategy,
* ORM/database technology,
* repositories,
* services,
* APIs,
* shared/common modules,
* events,
* configuration,
* authentication/authorization concepts,
* current project conventions.

If sufficient architectural/project context does NOT already exist, create it first inside:

`.cursor/`

Create concise architecture/context files that describe the existing project sufficiently for future Cursor sessions.

Do not create excessive documentation.

The purpose of `.cursor/` context is to prevent future architectural decisions from being made without understanding the project.

---

# 1. MOST IMPORTANT PRINCIPLE: KEEP IT SIMPLE

This project must remain understandable and maintainable.

Do NOT over-engineer the database.

Do NOT introduce tables, abstractions, layers, events, dimensions, snapshots, bridges, or SCD structures unless they solve a concrete business problem.

The guiding principle is:

> Use the simplest model that correctly represents the parish domain and preserves the historical information that genuinely matters.

We explicitly want to avoid creating an architecture that becomes so complex that we "bury ourselves" in our own design.

Therefore:

* prefer fewer well-designed models over many tiny models,
* avoid premature generalization,
* avoid generic "everything tables",
* avoid excessive inheritance,
* avoid EAV unless absolutely unavoidable,
* avoid event sourcing unless there is an exceptional reason,
* avoid SCD2 where ordinary history is enough,
* avoid FACT/DIM modeling where an operational transactional model is more appropriate,
* avoid duplicate sources of truth,
* avoid unnecessary cross-module dependencies.

When proposing any additional model, ask:

1. Does the parish actually need this?
2. Does it solve a real workflow or historical requirement?
3. Could the same requirement be solved more simply?
4. Will a future developer understand why this table exists?

If the answer is not convincing, do not add the model.

---

# 2. THINK LIKE A PRIEST AND PARISH OFFICE USER

Do not analyze the system only from a technical perspective.

Also think from the perspective of:

* a parish priest,
* parish administrator,
* parish office employee,
* person responsible for sacramental registers,
* person responsible for parish finances,
* person preparing parish announcements,
* person managing Mass intentions,
* person preparing diocesan reports,
* person searching historical sacramental records.

Ask yourself:

> If I were responsible for running a parish every day, what information would I actually need?

Consider realistic workflows such as:

* finding a family,
* finding a parishioner,
* changing a family's address,
* recording someone leaving or entering the parish,
* recording Baptism,
* recording First Communion,
* recording Confirmation,
* recording a funeral,
* recording Anointing of the Sick,
* issuing certificates,
* finding historical sacramental information,
* correcting registry information,
* recording Mass intentions,
* tracking Mass obligations,
* recording family contributions,
* recording diocesan collections,
* tracking construction fundraising campaigns,
* recording parish expenses,
* tracking parish debts,
* preparing parish bulletins,
* maintaining council memberships,
* managing pastoral tasks,
* accepting public sacrament applications.

At the same time, do NOT invent features merely because they could theoretically exist.

Prioritize actual parish workflows.

---

# 3. LANGUAGE

All:

* model names,
* table names,
* field names,
* relationship names,
* enum names,
* technical terminology in the proposed schema

must be in **English**.

Business explanations may remain readable and descriptive, but the proposed model architecture itself must use English naming.

---

# 4. MODULE BOUNDARIES

The application is modular.

Respect module ownership.

Everything that logically belongs to a module should remain within that module.

Do NOT create one global namespace containing unrelated models.

Start by proposing sensible modules.

Likely examples could include concepts such as:

* Parish / Registry
* Families / Parishioners
* Sacraments
* Liturgical / Masses
* Finance
* Calendar
* Pastoral
* Councils
* Public Applications
* Documents
* Settings / Reference Data

These are examples only.

Use the existing project architecture first.

Do not create a new module merely because a table exists.

For each model specify:

* owning module,
* whether it is internal to the module,
* whether another module references it,
* whether a shared model is truly required.

Avoid circular module dependencies.

---

# 5. HASH FIELD IS MANDATORY

Every relevant persisted business model must contain a `hash` field.

Evaluate and define its intended purpose consistently.

Determine whether the hash represents:

* data integrity,
* change detection,
* synchronization,
* deduplication,
* SCD change detection,
* or another project-specific purpose.

Do not merely add a meaningless hash column.

Recommend:

* what data contributes to the hash,
* whether technical fields such as timestamps should be excluded,
* when the hash is recalculated,
* whether the hash needs to be indexed or unique.

If different classes of models require different hashing rules, explain them.

---

# 6. OPERATIONAL MODEL FIRST, ANALYTICS SECOND

My initial labels such as `FACT`, `SCD1`, and `SCD2` represent my current thinking.

They are NOT unquestionable requirements.

Critically evaluate them.

If I marked something as `FACT`, but it is actually better represented as:

* operational transaction,
* aggregate root,
* child entity,
* event,
* association entity,
* registry entry,
* document,
* snapshot,

say so.

Likewise, if I marked something as SCD2 but a simpler history model would be more appropriate, explain that.

Do not force classical Data Warehouse terminology into the operational database.

For each concept distinguish between:

### Operational representation

Used by the application.

and, only where useful:

### Analytical representation

Used for reporting, historical analysis, BI, aggregates, or dimensional analytics.

The operational database remains the primary concern.

---

# 7. SCD GUIDELINES

Use SCD only where historical versions are meaningful.

Evaluate:

* SCD Type 0,
* SCD Type 1,
* SCD Type 2,
* explicit history table,
* append-only event/history model,
* simple mutable entity.

For SCD2 candidates explain:

* business key,
* surrogate key,
* `valid_from`,
* `valid_to`,
* `is_current`,
* `version`,
* `hash`,
* which fields trigger a new version,
* which fields can be updated without creating history.

Do not create a new version because an irrelevant technical field changed.

---

# 8. GRAIN

Every important transactional, registry, historical, or fact-like model must have a clearly defined grain.

Example:

> One row represents one sacramental Baptism record for one person.

or:

> One row represents one financial contribution made by one family toward one contribution category.

Never mix multiple grains inside one model.

Point out every place where my proposed model appears to mix grains.

---

# 9. PARISH FAMILY AND PARISHIONERS

Review these concepts carefully:

### Proposed

1. SCD2 — Family
2. SCD2 — Family Member

The Family concept should support at least the domain questions around:

* family identity,
* family name/display name,
* parish household,
* address,
* contact information,
* notes,
* active/inactive state,
* parish membership status if appropriate.

Determine whether:

`FamilyMember`

should actually be a real person entity such as:

`Person`

or:

`Parishioner`

with a separate membership/relationship model such as:

`FamilyMembership`.

Consider situations such as:

* a person moving from one household to another,
* marriage,
* children leaving the family household,
* deceased members,
* historical family membership,
* one person needing sacramental records independent of the family,
* a person existing before being associated with a family.

Avoid designing sacraments directly around `FamilyMember` if a stable `Person` identity is more correct.

Propose the simplest architecture that handles real parish life correctly.

---

# 10. STREETS / ADDRESSES

Proposed:

SCD2 — Streets

Investigate whether `Street` genuinely needs SCD2.

Consider separating:

* Street
* Address
* Settlement / City
* Postal Code

only if necessary.

Look at the existing project and commonly accepted address modeling conventions.

Do not normalize addresses excessively.

Determine how historical family addresses should work.

An address change must not destroy important historical parish records.

---

# 11. REFERENCE DATA / SYSTEM PARAMETERS

Proposed:

SCD1 — Reference Data

This includes values such as:

* family parish contribution amount ("lukno"),
* family gift/contribution,
* bell-ringing fee,
* other configurable parish values.

Also consider application/system parameters.

Determine whether these belong in:

`ReferenceData`

`SystemSetting`

`ContributionType`

`FeeType`

or several small, strongly typed concepts.

Avoid one massive untyped key/value table if that damages data integrity.

At the same time, do not create dozens of unnecessary lookup tables.

Find a pragmatic balance.

---

# 12. FAMILY CONTRIBUTIONS

Proposed:

FACT — Family Contributions to Parish

Design the concept around actual financial transactions.

It should be possible to determine:

* which family contributed,
* amount,
* date,
* contribution category,
* payment method if needed,
* accounting/reference period if needed,
* notes/reference,
* whether the contribution relates to a specific campaign or obligation.

Consider categories such as:

* regular parish contribution,
* family gift,
* bell-ringing fee,
* construction campaign,
* special collection,
* diocesan collection,
* other.

Do not hard-code all financial categories directly into the transaction model.

---

# 13. PARISH FINANCIAL STREAMS

Special attention is required here.

Determine the simplest clean architecture for separating:

### Parish accounts / ordinary parish funds

Money belonging to normal parish operations.

### Diocesan collections

Collections received by the parish but intended for the diocese or another external destination.

### Construction / fundraising campaigns

Money collected for a specific project or campaign.

### Mass obligations / Mass offerings

Money and obligations associated with Mass intentions.

These are financially and semantically different.

Determine whether they should use:

* one transaction model with typed categories,
* accounts/funds,
* allocation models,
* dedicated submodels,
* or a combination.

Avoid creating four completely separate financial systems if a common transaction foundation can represent them safely.

However, do not merge them so aggressively that their different accounting meaning is lost.

Explicitly propose a recommended structure.

---

# 14. MASS INTENTIONS

Proposed:

FACT — Mass Intention

This is an important parish workflow.

Design it from the priest's operational perspective.

Consider concepts such as:

* intention,
* requested by,
* intention text,
* offering,
* requested date,
* scheduled Mass,
* celebrant if relevant,
* fulfilled status,
* transfer/forwarding if relevant,
* notes.

Determine whether Mass intention and Mass obligation should be separate concepts.

Determine what happens if an intention is:

* requested,
* scheduled,
* rescheduled,
* fulfilled,
* transferred,
* cancelled.

Keep the workflow simple.

---

# 15. MASS SCHEDULE

Proposed:

SCD1 — Mass Schedule

Analyze whether this should represent:

* recurring weekly Mass schedule,
* individual scheduled Mass celebrations,
* liturgical exceptions,
* or a template.

Do not mix:

"Every Sunday at 09:00"

with:

"Mass on 25 December 2026 at 09:00"

unless the architecture explicitly distinguishes schedule template vs occurrence.

---

# 16. CALENDAR

Proposed:

FACT — Calendar

It must be possible to have multiple events on the same date.

Therefore, date must NOT be unique.

Analyze whether `Calendar` should actually be something such as:

`CalendarEvent`

or:

`ParishEvent`.

Support overlapping events.

Potential concepts:

* title,
* description,
* start date/time,
* end date/time,
* all-day event,
* category,
* location,
* liturgical relevance,
* recurrence if genuinely required.

Avoid building a full Google Calendar clone.

---

# 17. PARISH BULLETIN

Proposed:

FACT — Parish Bulletin

Determine whether this should instead be a document/content aggregate such as:

`ParishBulletin`

with related items such as:

`ParishBulletinItem`

only if genuinely useful.

Consider:

* publication period,
* title,
* content,
* announcements,
* Mass intentions shown in bulletin,
* events,
* generated document/file,
* publication status.

Avoid duplicating source data simply because it appears in the bulletin.

If events and Mass intentions already exist elsewhere, consider references or generated content rather than creating duplicate authoritative records.

---

# 18. SACRAMENTS

This area requires particularly careful domain modeling.

Proposed:

* FACT — Baptism
* FACT — First Communion
* FACT — First Communion + communicants relation
* FACT — Confirmation
* FACT — Confirmation + confirmands relation
* FACT — Funeral
* FACT — Anointing of the Sick

Do not assume all sacraments should have exactly the same structure.

However, identify common reusable concepts where they genuinely reduce duplication.

Possible concepts to analyze:

* person receiving sacrament,
* sacrament date,
* parish/location,
* minister,
* register reference,
* witnesses,
* godparents,
* parents,
* sponsor,
* certificate data,
* notes,
* canonical/legal annotations.

Do NOT create one gigantic generic `Sacrament` table if that makes the model vague.

Likewise, do not duplicate identical technical fields across every sacrament without considering a sensible shared pattern.

Find the simplest maintainable balance.

---

# 19. BAPTISM — SPECIAL ATTENTION

Baptism and the baptismal register are especially important.

Analyze Baptism from both:

* operational parish perspective,
* canonical/historical registry perspective.

Think carefully about information that a priest may need decades later.

The Baptism model should be evaluated for concepts such as:

### Person being baptized

* stable person identity,
* baptismal/given name,
* surname,
* sex if required by the registry,
* date of birth,
* place of birth.

### Parents

* father,
* mother,
* their names/surnames,
* potentially maiden surname,
* residence,
* relationship to Person where possible.

Historical register data must remain valid even if Person records change later.

Therefore determine where snapshots/historical textual values may be required.

### Godparents / Sponsors

Determine whether these should be:

* references to existing Person records,
* external persons,
* participant records,
* snapshot text,
* or combination.

Do not require every godparent to be a registered parishioner.

### Baptism itself

Consider:

* baptism date,
* baptism place,
* minister,
* parish,
* register,
* register year,
* entry number,
* page/folio if applicable,
* notes,
* annotations,
* conditional/emergency baptism if relevant.

### Later annotations

A baptismal record may later receive annotations related to other events in the person's ecclesiastical life.

Determine whether annotations should be modeled separately rather than modifying the original record.

Keep this pragmatic.

Do not attempt to implement an entire canon-law system.

---

# 20. SACRAMENTAL REGISTERS / MATIČNE KNJIGE

This needs a dedicated architectural proposal.

Design how parish sacramental registers should work.

The architecture should make it possible to represent official parish register entries while preserving historical correctness.

Analyze whether the following concept makes sense:

`SacramentalRegister`

representing a physical/logical register book.

Possible fields:

* register type,
* parish,
* year or year range,
* volume,
* title,
* status.

And:

`RegisterEntry`

or sacrament-specific register references.

However, do NOT automatically introduce a generic `RegisterEntry` if direct links from sacrament records provide a simpler solution.

Consider how to represent:

* Baptism Register,
* First Communion Register,
* Confirmation Register,
* Marriage Register if the future domain requires it,
* Death/Funeral Register if applicable.

Even if Marriage is not currently in my proposed model list, identify whether its absence is suspicious for a parish-management system.

Do not automatically add it without explaining why.

For register entries analyze:

* register/volume,
* year,
* ordinal entry number,
* page/folio,
* original entry data,
* subsequent annotations,
* corrections,
* certificate issuance,
* immutable historical fields.

Important:

Official historical records should not silently change merely because the current `Person`, `Family`, or `Address` record changes.

Determine whether sacramental records need historical snapshots of names, parents, addresses, ministers, witnesses, etc.

Explain exactly which values should remain immutable and which references can remain dynamic.

---

# 21. FIRST COMMUNION

Proposed:

* First Communion — basic event information
* relation to communicants

Evaluate whether the best design is:

`FirstCommunionEvent`

and:

`FirstCommunionParticipant`

rather than treating both as FACT tables.

Possible event data:

* date,
* parish,
* church/location,
* celebrant,
* group,
* notes.

Possible participant data:

* person,
* event,
* status,
* notes,
* certificate/register information if required.

Define the grain explicitly.

---

# 22. CONFIRMATION

Similarly evaluate:

`ConfirmationEvent`

and:

`ConfirmationParticipant`

Possible participant information may include:

* confirmand,
* sponsor,
* confirmation name if used,
* minister,
* register information.

Do not duplicate event-level information for every participant unnecessarily.

---

# 23. FUNERAL

Analyze whether Funeral should reference:

* deceased Person,
* family,
* death date,
* funeral date,
* burial location,
* celebrant,
* cemetery,
* grave information if within project scope,
* notes.

Distinguish:

`death`

from:

`funeral`.

Do not assume they are the same event.

---

# 24. ANOINTING OF THE SICK

Keep this especially simple and privacy-aware.

Determine the minimum operational information actually needed.

Avoid collecting unnecessary sensitive medical details.

This system is for parish administration, not medical records.

---

# 25. PUBLIC SACRAMENT APPLICATIONS

Proposed:

* Public Baptism Application
* Public Confirmation Application
* Public First Communion Application

These are application/intake models, not sacramental records.

They must not become official sacrament records automatically.

Analyze a workflow such as:

`Submitted → UnderReview → Approved → Converted/Linked → Rejected/Cancelled`

Determine whether the three application types need:

* independent models,
* shared base/application infrastructure,
* typed application,
* related child data.

Prioritize clarity over excessive abstraction.

Explain how an accepted public application eventually relates to official domain models without duplicating sources of truth.

---

# 26. INCOMING INVOICES

Proposed:

FACT — Incoming Invoice

Analyze proper operational modeling.

Potential concepts:

* supplier,
* invoice number,
* invoice date,
* due date,
* amount,
* tax if needed,
* category,
* fund/account,
* payment status,
* payment date,
* attachment/document reference,
* notes.

Do not build full enterprise accounting unless required.

---

# 27. DEBTS / OBLIGATIONS

Proposed:

* SCD1 — Debt Types
* FACT — Debts owed to Parish
* FACT — Parish debts toward external parties

Determine whether both directions can share one underlying `Obligation` concept with a direction/type, or whether separate models are clearer.

Explicitly compare both designs.

Consider:

* debtor,
* creditor,
* amount,
* due date,
* status,
* type,
* settlement/payment,
* partial payments if required.

Again, keep it simple.

---

# 28. PARISH ECONOMIC COUNCIL

Proposed:

FACT — Parish Economic Council

This is probably not a FACT in the dimensional sense.

Analyze domain concepts such as:

`ParishEconomicCouncil`

`CouncilMembership`

or similar.

Consider historical membership:

* member,
* role,
* valid from,
* valid to,
* active status.

Determine whether council itself needs a persistent model or whether membership under a council type is sufficient.

---

# 29. PARISH PASTORAL COUNCIL

Perform the same analysis for the Pastoral Council.

Look for opportunities to share a simple council/membership model without creating a needlessly generic framework.

---

# 30. EVENTS AND TASKS

Proposed:

FACT — Events and Tasks combined.

Critically evaluate whether combining them is genuinely useful.

A calendar event and a task have different semantics:

Event:

* happens at a time.

Task:

* needs to be completed.

A simple shared concept is acceptable only if it does not make queries and workflows confusing.

Potential task fields:

* title,
* description,
* due date,
* assignee,
* status,
* priority,
* related entity.

Do NOT create a full project-management system.

---

# 31. DOCUMENT MANAGEMENT

Determine whether dedicated document models are actually needed.

Possible use cases:

* sacramental certificates,
* scanned historical records,
* incoming invoices,
* council documents,
* parish bulletins,
* application attachments.

Do not create a full document management system unless required.

Evaluate whether a minimal generic model such as:

`Document`

or:

`Attachment`

could be enough.

Consider:

* storage key/path,
* original filename,
* MIME type,
* document category,
* uploaded date,
* owning/reference entity,
* metadata.

Avoid polymorphic relations if they create unnecessary complexity or weak referential integrity.

Explicitly state whether you recommend document models now or later.

---

# 32. DATA INTEGRITY AND IMMUTABILITY

Pay particular attention to historical church records.

A modern mutable person profile is not necessarily the same thing as an official historical register entry.

Determine which information should be:

* mutable current data,
* versioned,
* snapshotted,
* immutable after approval,
* corrected only through an explicit correction/annotation mechanism.

For example:

If a person's surname changes years after Baptism, the historical Baptism record must not silently appear as though the new surname existed at the time of Baptism.

Design for this intentionally.

---

# 33. KEYS

For each important model define:

* primary key,
* business/natural key,
* surrogate key where appropriate,
* external ID if relevant,
* unique constraints,
* composite uniqueness constraints.

For registers consider constraints such as:

`register + entry_number`

or another domain-appropriate uniqueness rule.

Do not assume UUID alone is sufficient for domain integrity.

---

# 34. RELATIONSHIPS

For every important relationship define:

* source,
* target,
* 1:1 / 1 / N,
* optional/required,
* foreign key owner,
* deletion behavior,
* historical implications.

Avoid cascade deletes for historical sacramental and financial records unless there is an extremely strong reason.

Prefer preserving records.

---

# 35. MISSING MODELS

Actively detect missing models.

However, classify every recommendation as:

### Required

Without this, an important domain workflow cannot be represented correctly.

### Strongly Recommended

Likely necessary and prevents significant architectural problems.

### Optional / Future

Useful but should NOT be built now unless needed.

Be conservative.

We are explicitly trying to avoid scope explosion.

---

# 36. PARTICULARLY CHECK FOR MISSING PARISH CONCEPTS

From the perspective of real parish administration, specifically consider whether we are missing something important around:

* Person / Parishioner,
* household/family membership,
* clergy/minister,
* parish/church/location,
* sacramental registers,
* marriage,
* certificates,
* annotations/corrections,
* Mass obligations,
* funds/accounts,
* diocesan collections,
* campaigns,
* payments,
* external contacts,
* cemetery/burial,
* documents.

Do not add all of these automatically.

Explain which are truly required by the existing scope.

---

# 37. MY INITIAL MODEL PROPOSAL

This is my current proposal.

Treat it as architectural input, not as a mandatory final schema.

1. SCD2 — Family

   * basic family information
   * note
   * address
   * contact email
   * active/inactive

2. SCD2 — Family Member

   * related to Family

3. SCD1 — Reference Data / Configuration

   * family parish contribution ("lukno")
   * family gift
   * bell-ringing fee
   * other parish-defined values

4. FACT — Family Contributions to Parish

   * contribution amount
   * contribution category

5. SCD2 — Streets

   * inspect appropriate address/street standard

6. FACT — Calendar

   * multiple records on the same date must be supported because celebrations/events may overlap

7. FACT — Mass Intention

8. SCD1 — Mass Schedule

9. FACT — Parish Bulletin

10. FACT — Baptism

11. FACT — First Communion

* basic event information

12. FACT — First Communion Participants

13. FACT — Confirmation

* basic event information

14. FACT — Confirmation Participants

15. FACT — Funeral

16. FACT — Anointing of the Sick

17. FACT — Incoming Invoices

18. SCD1 — Debt Types

19. FACT — Receivables / Obligations Owed to Parish

20. FACT — Parish Payables / Obligations Toward External Parties

21. FACT — Parish Economic Council

22. FACT — Parish Pastoral Council

23. FACT — Events and Tasks

* currently envisioned as one concept, but evaluate this critically

24. FACT — Public Baptism Application

25. FACT — Public Confirmation Application

26. FACT — Public First Communion Application

Additional requirements:

* Design the architecture for sacramental registers / parish register books.
* Determine how to separate parish accounts, diocesan collections, construction/fundraising campaigns, and Mass obligations.
* Determine whether document/attachment models are necessary.
* Application settings/system parameters belong conceptually to configuration/reference data, but evaluate the best implementation.
* Every relevant persisted business model requires a `hash`.

---


# 39. EXISTING FORMS ARE INPUT, NOT THE FINAL SCHEMA

Inspect the existing application forms, DTOs, request schemas, UI fields, validation rules, and workflows.

Use them as an important source of domain knowledge.

Existing forms can help determine:

* which information users currently enter,
* which fields are operationally important,
* which fields are required vs optional,
* which relationships already exist implicitly,
* which concepts users think of as one workflow,
* which historical data may already be expected.

However:

> Existing forms are evidence of the current implementation, not the final authority for the database design.

Do NOT blindly reproduce form fields as database columns.

Do NOT assume that:

* every form field deserves its own database column,
* every database field needs to appear on a form,
* the current form structure reflects the correct domain boundaries,
* the current validation rules are sufficient,
* the current naming is correct,
* existing forms contain all required fields.

When analyzing a form:

1. identify the business concept behind each field,
2. determine which model should actually own that data,
3. identify whether the field is:

   * persisted,
   * derived,
   * transient,
   * display-only,
   * lookup/reference,
   * snapshot data,
   * historical data,
4. detect missing domain fields that are not present in the UI,
5. detect UI fields that should NOT become persistent schema fields.

If an existing form conflicts with good domain/database architecture, prefer the correct architecture and explicitly explain what should change in the form later.

Do not modify forms in this phase.

---

# 40. BILINGUAL MODEL AND FIELD DOCUMENTATION

All technical identifiers must remain in English.

This includes:

* model names,
* table names,
* field names,
* enum names,
* relation names,
* class names,
* constraint names where relevant.

However, for every model and every important field, also provide a Croatian description so the business meaning is immediately clear.

Use the following format.

Example:

Model:

`Person`
Croatian meaning: `Osoba`

Purpose:
Represents one natural person known to the parish.

Croatian explanation:
Predstavlja jednu fizičku osobu evidentiranu u sustavu župe.

Fields:

`first_name` — Ime
Person's current first name.

`last_name` — Prezime
Person's current surname.

`date_of_birth` — Datum rođenja
Date on which the person was born.

`family_id` — Obitelj
Do NOT use this field if family membership needs historical modeling; prefer the appropriate relationship model.

For every recommended model, include:

* English model name,
* Croatian model meaning,
* English purpose,
* Croatian short explanation.

For every important field, include:

* English field name,
* Croatian meaning,
* short explanation,
* data type recommendation where useful,
* required/optional,
* immutable/mutable where relevant.

Do not translate identifiers themselves into Croatian.

Correct:

`baptism_date` — Datum krštenja

Incorrect:

`datum_krstenja`

---

# 41. FIELD-LEVEL ARCHITECTURE

For each important model, do not stop at model-level design.

Propose the important fields required by the domain.

Use this structure:

Field:
`field_name`

Croatian meaning:
`...`

Purpose:
`...`

Type:
`...`

Required:
Yes / No

Mutable:
Yes / No / Restricted

Included in hash:
Yes / No

Notes:
`...`

Do not list trivial framework-generated fields unless they matter architecturally.

Focus on business fields.

---

# 42. EXISTING FORM GAP ANALYSIS

For each major domain model, compare:

* what exists in forms today,
* what the domain actually needs,
* what should be stored,
* what is missing,
* what may be unnecessary.

Use a compact structure:

Existing Form Signal:
`...`

Recommended Model Field:
`...`

Decision:
Keep / Rename / Move / Split / Remove / Add

Reason:
`...`

This is especially important for:

* Family,
* Person / Parishioner,
* Baptism,
* First Communion,
* Confirmation,
* Funeral,
* Mass Intention,
* financial contributions,
* public applications,
* incoming invoices.

Do not let the existing UI limit the domain model.

---

# 43. DEVELOPMENT AND CODE QUALITY STANDARDS

The proposed architecture must follow established software engineering standards.

Use:

* clear domain-driven naming,
* explicit ownership,
* predictable naming conventions,
* strong typing,
* database constraints,
* normalized operational data where appropriate,
* simple and explicit relationships,
* separation of concerns,
* low coupling,
* high cohesion,
* maintainable module boundaries.

Avoid:

* magic strings,
* unclear abbreviations,
* ambiguous model names,
* overloaded models,
* nullable fields used to represent unrelated workflows,
* generic `data`, `value`, `type`, or `metadata` fields where strongly typed fields are appropriate,
* excessive polymorphism,
* hidden business rules in application code when the database can safely enforce them.

Prefer explicit domain semantics.

---

# 44. PYTHON / PEP STANDARDS

If the project is Python-based, all future implementation must follow relevant Python standards.

Architecture and naming should anticipate clean Python implementation.

Follow, where applicable:

* PEP 8 — style and naming conventions,
* PEP 257 — docstrings,
* PEP 484 — type hints,
* PEP 526 — variable annotations,
* PEP 563 / modern postponed annotation practices where supported by the project's Python version,
* modern Python typing conventions,
* clear module boundaries,
* explicit imports,
* deterministic behavior,
* readable code over clever code.

Use:

* `snake_case` for database fields and Python attributes,
* `PascalCase` for model/classes,
* descriptive names,
* enums for stable bounded domain choices where appropriate.

Do not create abbreviations unless they are universally obvious in the domain.

Example:

Prefer:

`SacramentalRegister`

over:

`SacrReg`

Prefer:

`family_membership`

over:

`fam_rel`

---

# 45. DATABASE NAMING STANDARD

Recommend one consistent naming convention for the database.

Default recommendation unless the existing project uses another established convention:

Models / ORM classes:
`PascalCase`

Example:
`MassIntention`

Tables:
`snake_case`, preferably plural or singular consistently according to the current project standard.

Example:
`mass_intentions`

Fields:
`snake_case`

Example:
`requested_at`

Foreign keys:

`<referenced_entity>_id`

Example:
`person_id`

Boolean fields should clearly express boolean meaning:

`is_active`
`is_current`
`is_cancelled`

Avoid:

`active`
`current`
`flag`

Timestamps should communicate semantics.

Prefer:

`created_at`
`updated_at`
`occurred_at`
`scheduled_at`
`approved_at`
`valid_from`
`valid_to`

Do not use a generic `date` field when the business meaning is known.

---

# 46. ENUMS AND REFERENCE TABLES

Do not automatically create a database table for every finite list.

For each bounded value set, determine whether it should be:

* code enum,
* database enum,
* reference table,
* configurable reference data.

Use an enum when:

* values are stable,
* they are part of application behavior,
* administrators should not freely modify them.

Use reference/configuration data when:

* parish users need to configure the values,
* values may change,
* new values may be added without code deployment.

Example:

A workflow state such as:

`SUBMITTED`
`APPROVED`
`REJECTED`

is likely an enum.

A contribution category such as:

`Family Gift`
`Construction Campaign`
`Special Collection`

may be configurable reference data depending on requirements.

Explicitly make this distinction.

---

# 47. NULLABILITY

Avoid nullable fields without a business reason.

For every optional field, explain why absence is valid.

Do not use `NULL` to encode business state.

Example:

Bad:

`approved_at = NULL` meaning five different possible statuses.

Better:

`status = PENDING`

and `approved_at` remains nullable because it is not applicable until approval occurs.

---

# 48. DATABASE CONSTRAINTS BEFORE APPLICATION-ONLY RULES

Where practical, important invariants should be protected at database level.

Evaluate:

* NOT NULL,
* UNIQUE,
* CHECK,
* FOREIGN KEY,
* composite unique constraints,
* indexes.

Examples:

* sacramental register entry number uniqueness,
* one current SCD2 version,
* positive monetary amounts where appropriate,
* valid date ranges,
* duplicate participant prevention,
* duplicate family membership prevention.

Application validation is still necessary, but it should not be the only protection for critical data integrity.

---

# 49. MONEY

All financial values must use a proper decimal/fixed-precision monetary representation.

Never use floating-point types for monetary amounts.

For every money field specify:

* recommended precision,
* currency strategy,
* whether negative values are allowed.

If the system currently operates only in EUR, keep the solution simple.

Do not introduce multi-currency infrastructure unless there is an actual requirement.

---

# 50. DATES AND TIME

Use the correct temporal type for the meaning.

Examples:

`date_of_birth`
→ date only

`baptism_date`
→ usually date unless exact time has domain significance

`mass_start_at`
→ timezone-aware datetime

`created_at`
→ timezone-aware timestamp

Do not store everything as datetime.

Do not store date/time values as strings.

Use timezone-aware timestamps wherever exact moments matter.

Follow the existing project timezone strategy.

---

# 51. NOTES AND FREE TEXT

Avoid creating many unrelated free-text fields.

For each `note`, `description`, `comment`, or `remarks` field, determine its precise purpose.

Prefer specific naming when the semantics are known.

Example:

`pastoral_note`

may communicate more meaning than:

`note`

However, do not over-specialize fields when a generic note is genuinely sufficient.

---

# 52. AUDIT FIELDS

Determine one project-wide strategy for standard audit fields.

Potential fields:

`created_at`
`updated_at`
`created_by`
`updated_by`

Do not automatically put full audit metadata on every lookup table if unnecessary.

For sensitive historical records, consider stronger auditing.

Sacramental registers and financial transactions may require more rigorous auditability than ordinary configuration data.

Keep audit strategy proportional to domain importance.

---

# 53. SOFT DELETE

Do not automatically add `is_deleted` or `deleted_at` everywhere.

For every model determine whether deletion should be:

* allowed,
* prohibited,
* soft deletion,
* archival/inactivation.

Important sacramental and financial records should generally not disappear through ordinary deletion.

For master data such as Family or Person, archival/inactive state may be more meaningful than deletion.

Explicitly recommend the strategy per model category.

---

# 54. ARCHITECTURE BEFORE FRAMEWORK

Do not let the current ORM dictate the business architecture.

Design:

1. domain,
2. data ownership,
3. relationships,
4. constraints,
5. history,

first.

Only afterward should this be mapped to ORM/framework constructs.

If the framework encourages a technically convenient but conceptually weak model, prefer the correct domain model.

---

# 55. FINAL SELF-REVIEW

Before presenting the final architecture, perform a developer-quality review.

Check:

### Naming

Are model and field names explicit and predictable?

### Simplicity

Can any model or relation be removed?

### Domain correctness

Would a priest recognize the represented workflows?

### Data integrity

Can invalid states be created too easily?

### Historical correctness

Can old sacramental information silently change?

### Module boundaries

Is ownership clear?

### Forms

Did we use forms as evidence rather than treating them as the database schema?

### Python standards

Would the design map naturally to clean PEP-compliant Python?

### Future maintainability

Would another developer understand the architecture without reverse-engineering hidden assumptions?

If any answer is no, revise the proposal before presenting it.




# LAST -  REQUIRED OUTPUT

Do not implement anything.

Return an architectural analysis.

Use this structure:










## A. Domain Overview

Explain the main parish-management domains and workflows.

---

## B. Proposed Modules

For every proposed module:

Module:
Responsibility:
Owned Models:
Referenced Models:
Why this boundary exists:

Keep the number of modules reasonable.

---

## C. Review of My Proposed Models

For every model I proposed provide:

Original proposal:
Recommended English model name:
Recommended classification:
Module:
Grain:
Keep / Change / Split / Merge:
Reason:

For FACT/SCD labels specifically say whether my original classification is appropriate.

---

## D. Recommended Operational Model

For every recommended operational model:

Model:
Purpose:
Module:
Grain:
Primary Key:
Business Key:
Hash:
Important Fields:
Relationships:
History Strategy:
Mutable / Immutable:
Notes:

Do not list every trivial audit column unless relevant.

---

## E. Sacramental Architecture

Provide a focused design for:

* Baptism
* First Communion
* Confirmation
* Funeral
* Anointing of the Sick

Explain shared concepts vs sacrament-specific concepts.

---

## F. Baptism Deep Dive

Provide the recommended Baptism architecture in greater detail.

Include:

* Person relationship,
* parents,
* godparents,
* minister,
* place/parish,
* register reference,
* immutable historical data,
* annotations,
* corrections.

Show a textual relationship diagram.

---

## G. Sacramental Registers / Matične Knjige

Propose the simplest robust architecture for official parish registers.

Explain:

* register model,
* entry numbering,
* volume/year,
* sacrament relation,
* corrections,
* annotations,
* historical snapshots,
* certificate lookup.

Include an example showing what happens when a Person's current data changes after an old Baptism record was created.

---

## H. Finance Architecture

Design a simple coherent structure covering:

* family contributions,
* regular parish income,
* diocesan collections,
* construction/fundraising campaigns,
* Mass offerings/obligations,
* incoming invoices,
* parish receivables,
* parish payables.

Clearly state which concepts should share common models and which should remain separate.

---

## I. Calendar, Masses and Mass Intentions

Explain the relationship between:

* recurring Mass schedule,
* actual Mass occurrence,
* calendar events,
* Mass intentions,
* Mass obligations.

Avoid unnecessary complexity.

---

## J. Public Applications

Design the intake → approval → official record flow for:

* Baptism,
* First Communion,
* Confirmation.

Explain where temporary public-submission data ends and authoritative parish data begins.

---

## K. Documents

Answer directly:

Do we need a Document/Attachment model now?

If yes:
propose the minimum useful architecture.

If no:
explain why we should postpone it.

---

## L. Missing Models

Separate into:

### Required

### Strongly Recommended

### Optional / Future

For each:

Model:
Reason:
Module:
Grain:

Do NOT inflate the scope.

---

## M. Relationship Map

Provide a readable relationship map.

Example:

Family
└── 1 FamilyMembership
└── N:1 Person

Person
├── 1 Baptism
├── 1 ConfirmationParticipant
└── ...

Use the actual recommended architecture.

---

## N. Historical Strategy

Summarize which models use:

* normal mutable state,
* SCD1,
* SCD2,
* history table,
* immutable transaction/registry entry,
* snapshot.

Explain why.

---

## O. Hash Strategy

Define one consistent project-wide rule for `hash`.

Explain:

* purpose,
* generation,
* included fields,
* excluded fields,
* SCD usage,
* whether relations contribute to the hash,
* indexing/uniqueness recommendations.

---

## P. Data Integrity

List important database-level constraints.

Especially cover:

* sacramental register numbering,
* duplicate sacrament records,
* financial transaction integrity,
* family/person relationships,
* public application conversion,
* historical records.

---

## Q. Simplification Review

This section is mandatory.

After proposing the architecture, review your OWN proposal and ask:

> What can we remove or simplify without damaging the domain?

List anything you initially considered but intentionally decided NOT to introduce.

The final architecture should be intentionally smaller than the maximal architecture.

---

## R. Final Recommended Model Inventory

Provide a final tree grouped by module:

Module
├── Model
├── Model
└── Model

Separate where useful:

* Core / Operational
* History
* Reference Data
* Transactions
* Documents
* Public Intake

Do not include hypothetical future models in the main inventory.

Put future ideas separately.

---

## S. Architectural Decisions

Finish with a concise table:

Decision | Recommendation | Reason

Include the most important architectural decisions such as:

* Person vs FamilyMember
* SCD2 Family
* Street history
* Baptism snapshots
* Sacramental register design
* generic vs separate sacrament models
* finance/funds design
* events vs tasks
* document model
* public application architecture
* councils
* hash strategy

---

# FINAL RULE

The goal is NOT to build the theoretically most sophisticated database.

The goal is to build the **smallest architecture that correctly supports real parish work, preserves important historical and sacramental records, remains understandable to developers, and can grow later without requiring a rewrite**.

Whenever choosing between:

* a sophisticated generic abstraction,

and

* a few clear domain-specific models,

prefer the clear domain model unless the abstraction provides a concrete and immediate benefit.

Think like both:

1. an experienced database architect, and
2. a parish priest who actually has to use this system every day.

Architecture first.

Implementation later.
