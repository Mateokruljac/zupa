# Liturgija

Django aplikacija za: nakane / mise / zupni-listic i liturgijski kalendar.

## Vlasništvo

- raspored misa, misne nakane, župni listić
- liturgijski kalendar (LitCal / Romcal / HILP), API `/api/liturgical/*`
- management naredbe `liturgical_day`, `liturgical_audit`
- predlošci stranica i `partials/liturgical_day.html`

ORM modeli liturgijskog kalendara trenutno ostaju u `pastoral.models`
dok se ne izdvoji zasebna migracija.
