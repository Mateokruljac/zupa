# Pastoral — župna administracija

Django aplikacija za župnu administraciju. Podaci se čuvaju u bazi (model `Parish`), logika je u Pythonu — **bez REST API-ja** i bez localStorage demo baze.

Zadano: **Župa Blažene Djevice Marije**, Slavonski Brod.

## Pokretanje

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install Django==4.2.5 whitenoise django-debug-toolbar django-admin-interface django-colorfield pillow
python manage.py migrate --settings=config.settings.local
python manage.py seed_pastoral --settings=config.settings.local
python manage.py runserver --settings=config.settings.local
```

| Što | URL |
|-----|-----|
| Prijava | http://localhost:8000/login/ |
| Nadzorna ploča | http://localhost:8000/app/ |
| Moduli | http://localhost:8000/pages/nakane/ itd. |
| Javni obrasci | http://localhost:8000/public/ |
| Django admin | http://localhost:8000/admin/ |

### Prijava (OTP)

1. Unesite e-mail i ulogu → **Prikaži kod za prijavu**
2. Server generira 6-znamenkasti kod (prikazuje se na ekranu u demu)
3. Unesite kod → ulaz u aplikaciju

Uloge: župnik, vikar, upravitelj — svaka ima pristup različitim modulima (vidi `pastoral/services/permissions.py`).

## Arhitektura

```
pastoral/
  models.py          Parish (JSON podaci župe), OtpChallenge
  services/
    data.py          Učitavanje/spremanje podataka, KPI, podsjetnici
    api_actions.py   Sve CRUD mutacije (/api/action/ — za župni listić)
    streets.py       Ulice i obitelji po adresi
    cashbook.py      Blagajna — agregacija i kontekst
    invoices_page.py Ulazni računi
    finance_reports.py Financijska izvješća
    permissions.py   Navigacija i dozvole po ulozi
  page_handlers.py   Kontekst za svaku stranicu (server-side)
  actions.py         POST akcije na stranicama (forme)
  views.py           Django viewovi
templates/pastoral/  Server-side HTML (base, dashboard, stranice)
static/js/           Samo UI: tema, liturgijski kalendar, župni listić editor
```

Podaci župe u bazi (JSON u modelu `Parish`). Stranice se renderiraju u Pythonu; POST forme za CRUD. JavaScript ostaje samo za temu, liturgijski widget i interaktivni sastavljač župnog listića (`PastoralApi.action` → Python).

## Demo korisnici

Nakon `seed_pastoral`:

| E-mail | Uloga |
|--------|-------|
| ured@zupa-bdm-sb.hr | župnik |
| vikar@zupa-bdm-sb.hr | vikar |
| upravitelj@zupa-bdm-sb.hr | upravitelj |

Lozinka (za Django admin): `pastoral-demo`

## SQLite / PostgreSQL

Bez `DB_NAME` u `.env` koristi se SQLite. Za produkciju postavite PostgreSQL varijable i pokrenite `docker compose up`.
