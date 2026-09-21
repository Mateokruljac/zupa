# Liturgija

Django aplikacija za nakane, mise, župni listić i liturgijski kalendar.

## Kalendar

- uvoz: lokalni Romcal (`croatia`, locale `la`) + katalog
  `liturgija/config/liturgical_days.json`
- prikaz i API: retci `LiturgicalCalendarEntry`
- HILP: čitanja i poveznica na puni tekst
- naredba `liturgical_day`
- predložak `partials/liturgical_day.html`
