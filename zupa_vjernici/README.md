# Župa i vjernici

Django aplikacija za: obitelji / ulice / posjete.

## Standardna struktura

- `zupa_vjernici/models.py` — ORM modeli domene
- `zupa_vjernici/admin.py` — Django admin
- `zupa_vjernici/urls.py` — URL-ovi ispod `/pages/`
- `zupa_vjernici/views.py` — HTTP viewovi
- `zupa_vjernici/templates/zupa_vjernici/` — predlošci stranica i partiala
- `zupa_vjernici/migrations/` — migracije

Projektni `templates/` drži samo zajednički shell (base, login, dashboard, greške, e-mail). Domena se uključuje preko `{% include %}` ili `{% extends %}` prema potrebi.
