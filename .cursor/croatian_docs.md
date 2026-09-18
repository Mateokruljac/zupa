You are working on an existing software project that is already relatively complex.

One of the highest priorities from this point forward is:

> The project must remain understandable to the developer maintaining it.

Code quality alone is NOT sufficient.

Every important part of the system must clearly communicate:

* what it does,
* why it exists,
* how it works,
* what it depends on,
* what calls it,
* what it returns or changes,
* what business concept it represents,
* what would break if it were removed or changed.

The developer must be able to return to any part of the project months later and quickly understand its purpose.

---

# 1. LANGUAGE RULE

All source-code identifiers must remain in English.

This includes:

* class names,
* function names,
* method names,
* variables,
* database models,
* fields,
* enums,
* modules,
* packages,
* files,
* API names.

However:

> All explanatory documentation intended to help understand the code must be written in Croatian.

This includes:

* docstrings,
* meaningful inline comments,
* module documentation,
* architectural notes,
* service descriptions,
* domain explanations,
* workflow documentation,
* `.cursor/` project documentation.

Do not translate technical identifiers themselves.

Example:

```python
def create_baptism_record(...):
    """
    Kreira službeni zapis krštenja za određenu osobu.

    Ova funkcija predstavlja završni korak procesa evidentiranja krštenja
    nakon što su svi potrebni podaci provjereni.
    """
```

Not:

```python
def kreiraj_krstenje(...):
```

---

# 2. DOCUMENTATION IS MANDATORY

Do NOT treat documentation as optional.

Every important:

* module,
* class,
* service,
* repository,
* use case,
* function,
* method,
* domain model,
* API endpoint,
* workflow,
* background process,
* complex block of code,

must explain its purpose in Croatian.

Do not create meaningless comments that merely repeat the code.

Bad:

```python
# Povećaj brojač za 1
counter += 1
```

Good:

```python
# Redni broj upisa povećavamo tek nakon uspješnog spremanja zapisa
# kako ne bismo potrošili broj u slučaju neuspjele transakcije.
```

Comments and documentation must explain:

* intent,
* business reason,
* architectural reason,
* non-obvious behavior.

---

# 3. EVERY MODULE MUST EXPLAIN ITS PURPOSE

Every meaningful module/package should have a clear Croatian description.

For example:

```python
"""
Modul za upravljanje sakramentalnim zapisima župe.

Odgovoran je za:
- krštenja,
- prve pričesti,
- krizme,
- veze sa sakramentalnim maticama,
- povijesne podatke vezane uz sakramente.

Ovaj modul ne upravlja obiteljima niti financijama.
Te informacije koristi kroz definirane veze prema drugim modulima.
"""
```

A developer opening a module for the first time should immediately understand:

* what belongs there,
* what does not belong there,
* what business responsibility it owns.

---

# 4. EVERY CLASS MUST HAVE A PURPOSE

Every non-trivial class must explain:

* what it represents,
* why it exists,
* its responsibility,
* what it must NOT be responsible for,
* important collaborators/dependencies.

Example:

```python
class BaptismService:
    """
    Aplikacijski servis odgovoran za poslovni proces evidentiranja krštenja.

    Njegova odgovornost je koordinirati:
    - provjeru osobe,
    - provjeru podataka potrebnih za krštenje,
    - dodjelu broja zapisa u matici,
    - kreiranje zapisa krštenja,
    - spremanje povezanih podataka.

    Servis ne sadrži logiku pristupa bazi izravno.
    Za pristup podacima koristi odgovarajuće repozitorije.
    """
```

Do not use vague descriptions such as:

"This class handles baptism."

Explain the actual responsibility.

---

# 5. EVERY FUNCTION AND METHOD MUST EXPLAIN WHAT IT DOES

Every public or non-trivial function/method must have a Croatian docstring.

The documentation should explain:

1. what the function does,
2. why it exists,
3. important input parameters,
4. what it returns,
5. relevant side effects,
6. important business rules,
7. exceptions/errors where relevant.

Example:

```python
def register_baptism(
    person_id: UUID,
    baptism_data: BaptismCreateData,
) -> Baptism:
    """
    Evidentira novo krštenje za postojeću osobu.

    Funkcija provjerava da osoba postoji, validira podatke potrebne
    za službeni zapis te kreira zapis krštenja povezan s odgovarajućom
    matičnom knjigom.

    Args:
        person_id:
            Identifikator osobe koja prima sakrament.

        baptism_data:
            Podaci potrebni za evidentiranje krštenja.

    Returns:
        Kreirani zapis krštenja.

    Raises:
        PersonNotFoundError:
            Ako osoba ne postoji.

        DuplicateBaptismError:
            Ako osoba već ima evidentirano krštenje.

    Side effects:
        Kreira novi zapis u bazi podataka i može rezervirati sljedeći
        redni broj u matici krštenih.
    """
```

---

# 6. PRIVATE METHODS ALSO NEED EXPLANATION WHEN LOGIC IS NOT OBVIOUS

Do not document trivial getters/setters unnecessarily.

However, private methods containing:

* business rules,
* transformations,
* non-obvious calculations,
* filtering logic,
* complex queries,
* historical resolution,
* authorization logic,

must have Croatian documentation.

Example:

```python
def _resolve_family_at_date(...):
    """
    Pronalazi obitelj kojoj je osoba pripadala na zadani datum.

    Ova metoda se koristi kod povijesnih izvještaja gdje trenutačna
    obitelj osobe nije nužno ista kao obitelj kojoj je pripadala
    u trenutku događaja.
    """
```

---

# 7. EXPLAIN COMPLEX CODE BLOCKS

Whenever a block of code is not immediately obvious, place a concise Croatian explanation before it.

Especially document:

* complex conditions,
* nested loops,
* dynamic query construction,
* ORM optimization,
* transactions,
* locking,
* caching,
* SCD logic,
* hash comparisons,
* historical versioning,
* unusual performance optimizations.

Example:

```python
# Zaključavamo trenutačni zapis obitelji tijekom kreiranja nove SCD2 verzije.
# Bez ovog zaključavanja dva paralelna zahtjeva mogla bi istovremeno
# označiti različite verzije kao trenutačne.
```

Explain WHY, not only WHAT.

---

# 8. DATABASE MODELS REQUIRE DOMAIN DOCUMENTATION

Every database/domain model must explain in Croatian:

* what real-world concept it represents,
* its grain,
* why it exists,
* whether it contains current or historical state,
* important relationships,
* important invariants.

Example:

```python
class Family:
    """
    Predstavlja jedno župno kućanstvo odnosno obitelj.

    Jedan zapis predstavlja jednu verziju podataka o obitelji.

    Ako se koristi SCD2 pristup, promjena poslovno važnih podataka
    ne mijenja postojeći zapis nego kreira novu verziju.

    Osobe nisu izravno vlasništvo ovog modela.
    Njihova pripadnost obitelji evidentira se preko FamilyMembership.
    """
```

---

# 9. EVERY FIELD MUST BE UNDERSTANDABLE

For non-obvious model fields, document their Croatian business meaning.

Example:

```python
valid_from: datetime
"""Vrijeme od kojeg ova verzija podataka vrijedi."""

valid_to: datetime | None
"""Vrijeme do kojeg je verzija vrijedila. NULL označava trenutačnu verziju."""

is_current: bool
"""Označava trenutačno aktivnu SCD2 verziju zapisa."""

hash: str
"""
Hash poslovno važnih vrijednosti modela.

Koristi se za otkrivanje promjena relevantnih za kreiranje nove verzije
zapisa te ne uključuje tehnička polja poput updated_at.
"""
```

Do not document self-explanatory fields excessively.

Focus on fields whose business meaning could later become ambiguous.

---

# 10. SERVICES MUST EXPLAIN THE WORKFLOW

Every application/service layer component should explain the complete business responsibility.

For every important service answer:

* What workflow does it implement?
* Who initiates it?
* What models does it use?
* What business rules does it enforce?
* What does it persist?
* Which other modules does it communicate with?

Example:

`PublicBaptismApplicationService`

should explain the entire flow:

public submission
→ validation
→ parish review
→ approval/rejection
→ connection to authoritative parish records.

---

# 11. REPOSITORIES MUST EXPLAIN QUERY SEMANTICS

Do not describe repository methods merely as:

"Gets a family."

Explain what type of family data is returned.

Example:

```python
def get_current_family(...):
    """
    Dohvaća trenutačno važeću verziju obitelji.

    Povijesne SCD2 verzije se namjerno ne vraćaju ovom metodom.
    Za povijesni prikaz potrebno je koristiti get_family_at().
    """
```

This distinction is critical.

---

# 12. API ENDPOINTS MUST EXPLAIN USER INTENT

Every endpoint should document in Croatian:

* what user action it represents,
* expected caller,
* main validation,
* result,
* important permissions,
* side effects.

Do not document only HTTP mechanics.

Explain the business action.

---

# 13. EXPLAIN BUSINESS RULES WHERE THEY LIVE

Whenever code implements a business rule, explicitly document that rule.

Example:

```python
# Službeni zapis krštenja ne brišemo fizički.
# Nakon zaključavanja matice eventualni ispravak evidentira se kao
# nova napomena/ispravak kako bi se sačuvao povijesni trag.
```

A developer must not have to infer major business rules from conditions.

---

# 14. IMPORTANT DECISIONS MUST INCLUDE THE REASON

Whenever the implementation contains something that may initially look unnecessarily complicated, explain the architectural reason.

Example:

```python
# Ovdje namjerno spremamo ime majke kao povijesnu snapshot vrijednost,
# iako postoji veza prema Person modelu.
#
# Razlog je što službeni zapis krštenja mora zadržati podatak kakav je
# bio zapisan u trenutku nastanka matičnog zapisa. Kasnija promjena
# podataka na Person modelu ne smije retroaktivno promijeniti maticu.
```

These comments are more valuable than comments describing syntax.

---

# 15. DO NOT OVER-COMMENT SIMPLE CODE

Documentation must improve understanding, not create noise.

Do NOT write comments for:

* obvious assignments,
* trivial conditions,
* simple constructors,
* standard framework behavior,
* obvious CRUD operations.

Bad:

```python
# Kreiraj listu
items = []
```

Good documentation answers:

> Why does this exist?

not:

> What does this Python syntax do?

---

# 16. DOCUMENT CROSS-MODULE RELATIONSHIPS

If one module depends on another module, document why.

Example:

```python
"""
Sacraments modul koristi Person model iz People modula jer je osoba
zajednički identitet kroz cijeli sustav.

Sacraments modul ne smije mijenjati osnovne podatke osobe izravno.
Takve promjene pripadaju People modulu.
"""
```

This is especially important for avoiding future architectural erosion.

---

# 17. DOCUMENT DATA FLOW

For every important workflow, maintain a short Croatian explanation of the data flow.

Examples:

### Baptism

Public application
→ review
→ Person identification/creation
→ Baptism record
→ Sacramental Register
→ optional certificate.

### Family contribution

Family
→ Contribution
→ Contribution Type
→ Fund/Campaign if applicable
→ Financial reporting.

### Mass intention

Request
→ Mass Intention
→ scheduling
→ Mass occurrence
→ fulfilment.

These explanations should exist in `.cursor/` architecture documentation.

---

# 18. CREATE PROJECT DOCUMENTATION IN `.cursor/`

If it does not already exist, create a concise project knowledge structure inside:

`.cursor/`

Recommended structure:

```text
.cursor/
├── project-overview.md
├── architecture.md
├── modules.md
├── domain-model.md
├── database.md
├── workflows.md
├── conventions.md
└── glossary.md
```

Do not generate huge documents for the sake of documentation.

The documentation should remain practical and navigable.

---

# 19. `.cursor/project-overview.md`

Explain in Croatian:

* what the project is,
* who uses it,
* primary business goals,
* main functional areas,
* high-level project architecture.

A new developer should understand the essence of the system in a few minutes.

---

# 20. `.cursor/architecture.md`

Explain:

* architectural style,
* layers,
* module boundaries,
* dependency direction,
* shared components,
* database strategy,
* important technical decisions.

For every important architectural choice explain WHY it exists.

---

# 21. `.cursor/modules.md`

For each module explain:

### Module name

Croatian meaning:

Responsibility:

Contains:

Depends on:

Used by:

Must NOT contain:

Main models:

Main services:

Main workflows:

This file should serve as the map of the system.

---

# 22. `.cursor/domain-model.md`

Document important domain concepts.

For each model:

`Person`
— Osoba

`Family`
— Obitelj / župno kućanstvo

`FamilyMembership`
— Pripadnost osobe obitelji

`Baptism`
— Krštenje

etc.

For each concept explain:

* Croatian meaning,
* purpose,
* ownership,
* important relationships,
* lifecycle,
* historical behavior.

---

# 23. `.cursor/database.md`

Explain the database architecture.

Include:

* operational models,
* relationships,
* keys,
* historical models,
* SCD strategy,
* immutable records,
* financial architecture,
* sacramental registers,
* hashing strategy.

Every table/model should have a Croatian explanation.

---

# 24. `.cursor/workflows.md`

Document important workflows step by step.

Examples:

### Evidentiranje krštenja

1. Pronaći ili kreirati osobu.
2. Validirati osnovne podatke.
3. Odrediti odgovarajuću maticu.
4. Dodijeliti redni broj.
5. Kreirati zapis krštenja.
6. Evidentirati roditelje/kumove.
7. Spremiti povijesne vrijednosti potrebne za maticu.
8. Zaključiti transakciju.

Do this for every major business workflow.

---

# 25. `.cursor/conventions.md`

Document development conventions.

Include:

* PEP 8,
* PEP 257,
* typing,
* naming,
* imports,
* errors/exceptions,
* repositories,
* services,
* transactions,
* testing,
* database naming,
* docstring rules,
* Croatian documentation requirement.

---

# 26. `.cursor/glossary.md`

Maintain a bilingual domain glossary.

Example:

| English technical term | Croatian meaning    | Explanation                                   |
| ---------------------- | ------------------- | --------------------------------------------- |
| Family                 | Obitelj / kućanstvo | Osnovna obiteljska jedinica u evidenciji župe |
| Parishioner            | Župljanin           | Osoba povezana sa župom                       |
| Baptism                | Krštenje            | Sakrament krštenja                            |
| Sacramental Register   | Matična knjiga      | Službena knjiga sakramentalnih zapisa         |
| Mass Intention         | Misna nakana        | Nakana za koju se slavi misa                  |
| Offering               | Dar / stipendij     | Novčani prilog vezan uz određeni proces       |

Whenever a new important domain term is introduced, update the glossary.

---

# 27. DOCUMENT FUNCTION CALL CHAINS WHEN USEFUL

For complex operations explain the execution path.

Example:

```text
POST /baptisms
        │
        ▼
BaptismController
        │
        ▼
BaptismService.register()
        │
        ├── PersonRepository
        ├── SacramentalRegisterRepository
        └── BaptismRepository
                │
                ▼
             Database
```

Under the diagram explain in Croatian what each step does.

Do not produce these diagrams for trivial CRUD flows.

Use them where they genuinely help comprehension.

---

# 28. DOCUMENT SIDE EFFECTS

Functions that do more than their name might suggest must explicitly state side effects.

Examples:

* database writes,
* new SCD versions,
* status changes,
* file creation,
* external calls,
* event emission,
* notifications,
* financial transaction creation.

A developer should never discover a major side effect accidentally.

---

# 29. DOCUMENT TRANSACTIONS

Whenever several writes must succeed or fail together, explain the transaction boundary.

Example:

```python
# Kreiranje zapisa krštenja i dodjela broja u matici čine jednu
# transakcijsku cjelinu. Ako bilo koji korak ne uspije, niti jedan
# zapis ne smije ostati djelomično spremljen.
```

---

# 30. DOCUMENT ERROR HANDLING

For custom exceptions explain:

* what the error means,
* where it originates,
* whether it represents:

  * invalid user input,
  * business rule violation,
  * missing resource,
  * conflict,
  * infrastructure failure.

Do not use generic exceptions when a domain-specific error improves understanding.

---

# 31. DOCUMENT STATUS FIELDS AND STATE MACHINES

Whenever a model contains `status`, explain:

* available states,
* meaning of each state,
* allowed transitions.

Example:

```text
PublicBaptismApplication

SUBMITTED
→ UNDER_REVIEW
→ APPROVED
→ CONVERTED

or

SUBMITTED
→ UNDER_REVIEW
→ REJECTED
```

Explain in Croatian what every transition means.

Do not allow arbitrary status changes if the business process does not permit them.

---

# 32. EXPLAIN "WHY NOT"

For non-obvious architectural decisions, document alternatives that were intentionally rejected.

Example:

```text
Baptism does not directly store only person_id.

Reason:
Current Person information can change, while the historical sacramental
record must preserve values recorded at the time of Baptism.
```

This prevents future developers from "simplifying" something that exists for an important reason.

---

# 33. DO NOT CREATE DEAD ABSTRACTIONS

If a class, interface, base class, helper, mixin, factory, strategy, adapter, or other abstraction has only one trivial implementation and no clear architectural reason:

question whether it is necessary.

The project is already complex.

Prefer direct and readable code over speculative abstractions.

Use:

KISS.

Use:

YAGNI.

Use SOLID where it improves maintainability, not as a reason to produce unnecessary layers.

---

# 34. EVERY NEW FILE MUST HAVE A CLEAR REASON TO EXIST

Before creating a new source file ask:

> Does separating this code make the project easier to understand?

Do not create extremely fragmented structures where a single feature requires opening ten files to understand a simple operation.

At the same time, do not create enormous files containing unrelated responsibilities.

Optimize for developer comprehension.

---

# 35. KEEP RELATED CODE CLOSE

Code that changes together should generally remain close together.

Prefer cohesive feature/domain organization.

Avoid forcing developers to jump unnecessarily between:

* models,
* schemas,
* helpers,
* managers,
* utils,
* factories,

for simple workflows.

If the existing architecture requires those layers, clearly document their roles.

---

# 36. "UTILS" MUST NOT BECOME A DUMPING GROUND

Do not place domain logic into generic:

`utils.py`

`helpers.py`

`common.py`

unless the functionality is genuinely generic.

If code represents a parish concept, keep it within the relevant domain/module.

---

# 37. NO MAGIC

Avoid:

* magic numbers,
* unexplained strings,
* hidden conventions,
* implicit dependencies,
* dynamically constructed behavior without documentation.

Important values must use:

* constants,
* enums,
* settings,
* typed configuration,

as appropriate.

---

# 38. PEP AND PYTHON QUALITY

If this is a Python project, follow applicable modern Python standards.

At minimum:

* PEP 8,
* PEP 257,
* PEP 484,
* PEP 526,
* modern typing,
* explicit return types,
* descriptive names,
* predictable exception handling.

Public functions and methods should generally include type hints.

Avoid `Any` unless genuinely necessary.

Avoid deeply nested logic.

Prefer early returns where they improve clarity.

Prefer small cohesive functions, but do not fragment simple logic into dozens of micro-functions.

---

# 39. FUNCTIONS SHOULD HAVE ONE CLEAR RESPONSIBILITY

If a function:

* validates,
* transforms,
* queries,
* persists,
* sends notifications,
* generates documents,

all at once, evaluate whether responsibilities should be separated.

However, do not split code mechanically.

The goal is:

> one understandable responsibility per unit of code.

---

# 40. NAME THINGS BY BUSINESS MEANING

Names should describe the domain.

Prefer:

`register_baptism()`

over:

`process_data()`

Prefer:

`find_current_family_membership()`

over:

`get_relation()`

Prefer:

`MassIntentionStatus`

over:

`TypeEnum`.

The code itself should act as documentation.

---

# 41. WHEN MODIFYING EXISTING CODE

Before modifying existing code:

1. understand what it currently does,
2. understand who calls it,
3. understand its side effects,
4. understand what business rule it represents.

Do not rewrite code simply because another style looks cleaner.

Preserve behavior unless a change is intentional.

If behavior changes, explicitly document:

* previous behavior,
* new behavior,
* reason for change,
* affected areas.

---

# 42. DO NOT DELETE "WEIRD" CODE WITHOUT UNDERSTANDING IT

If code looks strange, redundant, or overly defensive, first determine why it exists.

It may be protecting:

* backward compatibility,
* historical data,
* database integrity,
* edge cases,
* external integrations.

If the reason cannot be established, document the uncertainty before changing it.

---

# 43. SEARCH USAGE BEFORE CHANGING CORE CODE

Before renaming, removing, or significantly modifying:

* classes,
* methods,
* database fields,
* models,
* enums,
* shared utilities,

search the entire project for references.

Determine:

* direct callers,
* indirect dependencies,
* tests,
* API usage,
* database implications.

Never assume a method is unused just because its usage is not visible in the current file.

---

# 44. TESTS SHOULD EXPLAIN BUSINESS BEHAVIOR

Test names must clearly state expected behavior.

Prefer:

```python
def test_cannot_register_second_baptism_for_same_person():
```

over:

```python
def test_baptism_2():
```

For non-obvious tests, include Croatian explanation describing the business rule being protected.

Tests should help explain the system.

---

# 45. EACH IMPORTANT FEATURE NEEDS A SHORT FEATURE SUMMARY

For significant functionality maintain a concise Croatian summary containing:

### Svrha

What business problem does it solve?

### Ulaz

What information enters the process?

### Proces

What happens?

### Rezultat

What changes or is created?

### Ovisnosti

Which modules/models/services participate?

### Poslovna pravila

What rules must always hold?

### Rizici

What should developers be careful about?

This summary may live in the relevant `.cursor/` documentation rather than the source file when appropriate.

---

# 46. ARCHITECTURAL COMPLEXITY BUDGET

The project is already complex.

Treat complexity as a limited resource.

Every new:

* abstraction,
* model,
* service,
* repository,
* generic mechanism,
* event,
* background job,
* indirection,

must justify its existence.

When two designs solve the same requirement correctly:

> choose the one that is easier for the next developer to understand.

---

# 47. BEFORE IMPLEMENTING A NEW FEATURE

Before writing code, briefly determine:

1. Which module owns the feature?
2. Which existing models/services already support it?
3. Is a new model actually required?
4. Can the existing architecture support it without another abstraction?
5. What business rules need protection?
6. What needs to be documented?
7. Which tests prove correct behavior?

Then implement the smallest correct solution.

---

# 48. AFTER IMPLEMENTING A FEATURE

Perform a mandatory self-review.

Ask:

### Understandability

Can another developer understand this without asking the author?

### Documentation

Are all non-obvious parts explained in Croatian?

### Naming

Do names communicate business meaning?

### Architecture

Did we place the code in the correct module?

### Complexity

Did we add anything unnecessary?

### Side effects

Are side effects obvious?

### Database

Are constraints and transactional boundaries correct?

### Tests

Are important business rules covered?

### Cursor documentation

Did this change require updating `.cursor/` documentation?

If yes, update it.

---

# 49. WHEN EXPLAINING EXISTING CODE TO ME

When I ask:

* "What does this do?"
* "Explain this module."
* "Explain this class."
* "Explain this method."
* "Why is this here?"
* "How does this feature work?"

do NOT give me only a short technical summary.

Explain it in Croatian using this structure where appropriate:

### Što je ovo?

Explain the concept in simple terms.

### Čemu služi?

Explain its business/technical purpose.

### Kako radi?

Walk through execution.

### Što prima?

Explain inputs.

### Što vraća ili mijenja?

Explain output and side effects.

### S čime je povezano?

Show relevant dependencies.

### Gdje se koristi?

Explain callers/workflows.

### Na što treba paziti?

Explain important risks, assumptions, or edge cases.

### Jednostavno rečeno

Finish with a short plain-language explanation.

The goal is that I genuinely understand the code, not merely receive a description of its syntax.

---

# 50. WHEN I ASK FOR A CODE CHANGE

Whenever I ask you to modify or create functionality, your final response should briefly tell me in Croatian:

* što si promijenio,
* gdje si promijenio,
* zašto,
* kako sada radi,
* što je povezano s tom promjenom,
* postoji li nešto na što trebam paziti.

Do not overwhelm me with implementation noise.

Prioritize understanding.

---

# 51. NEVER HIDE COMPLEXITY BEHIND VAGUE LANGUAGE

Do not say things such as:

"Added some logic."

"Updated service."

"Refactored code."

Instead say precisely:

"Promijenjena je logika `BaptismService.register_baptism()` tako da se broj upisa u maticu dodjeljuje unutar iste transakcije kao i zapis krštenja. Time se sprječava da neuspjelo spremanje potroši broj iz matice."

Be concrete.

---

# 52. FINAL PRINCIPLE

This project's source code should be maintainable even if the original developer is unavailable.

The target is NOT maximum abstraction.

The target is:

* clear code,
* explicit domain meaning,
* strong typing,
* predictable structure,
* good database integrity,
* clear module ownership,
* Croatian explanations of all non-obvious logic,
* minimal unnecessary complexity.

Always optimize for:

> "Can I understand this code six months from now without having to rediscover why it was written this way?"

If not, improve the naming, documentation, architecture, or implementation before considering the task finished.
