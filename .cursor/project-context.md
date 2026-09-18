# e-Župa — existing project context

Parish office application (Django 4.2+/5.x, PostgreSQL in production, SQLite locally). UI language is Croatian; Python identifiers are English. Custom user: `pastoral.User` (`AUTH_USER_MODEL`, table `users_user`). Tenant is one `Parish` per office. Default PK: UUID.

## Apps

| App | Owns |
|---|---|
| `pastoral` | Shell, auth, OTP, `Parish`, `Diocese`, `ParishMembership` |
| `zupa_vjernici` | Person, church enrollment, street, household, visits |
| `sakramenti` | Sacramental events, participants, details, formation |
| `isprave` | Register books/entries, templates, certificates |
| `liturgija` | Mass schedule, intentions, bulletin, liturgical calendar |
| `financije` | Cashbook, invoices, debts, lukno default |
| `ured` | Calendar, tasks, councils, public submissions, office directory |
| `pregled` | Dashboard (no domain tables) |

## Persistence shape

Operational data is already mostly ORM, but many tables still carry a legacy `payload` JSON and camelCase projection for the UI (`pastoral.services.operational_store`). `Parish.data` is cleared on save and must not be treated as source of truth. `Parish.settings` remains a JSON bag for parish profile.

Canonical identity (`Person`, `SacramentalEvent`, `RegisterEntry`) already exists and is **not fully wired** into household members, public forms, or finance.

## Conventions

- Table names often still `pastoral_*` after app splits.
- Business uniqueness is usually `(parish, public_identifier)`.
- Money: `DecimalField`. Timezone: `Europe/Zagreb`.
- Do not invent a new module for a table that already has an owner app.
