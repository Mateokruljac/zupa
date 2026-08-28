# Pastoral — župna administracija

Django aplikacija za vođenje župnog ureda: vjernici, liturgija, sakramenti,
financije, isprave i uredski poslovi. Stranice se pretežno renderiraju na
serveru, a mali interni JSON API podržava OTP prijavu, liturgijski kalendar i
interaktivne liturgijske akcije.

Zadani razvojni tenant je **Župa Blažene Djevice Marije**, Slavonski Brod.

## Lokalno pokretanje

Za razvoj je dovoljan Python; lokalne postavke koriste SQLite, lokalnu
memoriju za cache i izvršavaju Celery zadatke sinkrono.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_pastoral
python manage.py runserver
```

`manage.py`, WSGI i ASGI u razvoju zadano koriste `zupa.settings.local`.
Mailhog i Redis potrebni su samo ako lokalnim varijablama uključite stvarni
SMTP, Redis cache ili asinkroni Celery.

| Što | URL |
|-----|-----|
| Prijava | http://localhost:8000/login/ |
| Nadzorna ploča | http://localhost:8000/app/ |
| Moduli | http://localhost:8000/pages/nakane/ itd. |
| Javni obrasci | http://localhost:8000/public/ |
| Django admin | http://localhost:8000/admin/ |

### Prijava (OTP)

1. Unesite e-mail i ulogu te zatražite kod.
2. U razvojnom načinu server prikazuje generirani šesteroznamenkasti kod.
3. Unesite kod za ulaz u aplikaciju.

Uloge župnik, vikar i upravitelj imaju različite dozvole definirane u
`pastoral/services/permissions.py`.

## Arhitektura

Projekt je podijeljen po poslovnim domenama:

```text
pregled/         nadzorna ploča
zupa_vjernici/  osobe, obitelji, ulice i zajednice
liturgija/       misne nakane, raspored misa i župni listić
sakramenti/      sakramentalne evidencije
financije/       blagajna, računi i izvještaji
isprave/         dokumenti i predlošci
ured/            postavke i uredski procesi
pastoral/        zajednički shell, autentikacija, API i kompatibilni servisni sloj
control_plane/   tenant i licencni kontekst
users/           korisnički model
zupa/            URL i settings konfiguracija projekta
```

Domenski zapisi spremaju se u tipizirane ORM modele. Model `Parish` i
`ParishDataService` ostaju agregacijska i kompatibilna granica za dijelove
sučelja koji rade nad jedinstvenim snapshotom župe.

## Demo korisnici

Naredba `seed_pastoral` ponovno učitava demo podatke i postavlja ove račune:

| E-mail | Uloga |
|--------|-------|
| ured@zupa-bdm-sb.hr | župnik |
| vikar@zupa-bdm-sb.hr | vikar |
| upravitelj@zupa-bdm-sb.hr | upravitelj |

Lozinka za Django admin je `pastoral-demo`.

> `seed_pastoral` je destruktivna demo naredba: postojeće podatke zadanog
> tenanta zamjenjuje početnim skupom.

## Docker razvojno okruženje

`docker-compose.yml` pokreće web, PostgreSQL, Redis, Celery i Mailhog. Prije
pokretanja izradite lokalni `.env` te odaberite settings modul i vjerodajnice
za bazu. Za PostgreSQL koristite `DJANGO_SETTINGS_MODULE=zupa.settings.production`
i obavezno postavite barem `SECRET_KEY`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`
i `DB_PASS`.

```bash
docker compose up -d --build
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py seed_pastoral
```

Mailhog sučelje dostupno je na http://localhost:8025/.

## Provjere

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Liturgijski kalendar

Romcal `croatia` radi lokalno. Zadani provider `hybrid` koristi Romcal za
glavno slavlje i rang, a postojeći LitCal/HILP sloj za dopunu liturgijskog
vremena i čitanja. `LITURGICAL_PRIMARY_PROVIDER` podržava vrijednosti
`hybrid`, `romcal` i `litcal`.

```bash
python manage.py test liturgija.tests.test_liturgical_romcal
python manage.py liturgical_day 2026-08-03
python manage.py liturgical_day 2026-08-03 --provider romcal --json
python manage.py liturgical_audit 2026 --month 8
```

Opcija `liturgical_day --with-hilp` dohvaća hrvatska čitanja i može
zahtijevati mrežu. Bez nje Romcal provjera radi lokalno.

Dijagnostički endpointi nakon prijave:

- `/api/liturgical/romcal/day/2026-08-03/`
- `/api/liturgical/compare/2026-08-03/`
- `/api/liturgical/v1/day/2026-08-03/`

Razlika između providera nije nužno pogreška: mjesečni audit posebno izdvaja
razlike u naslovu, rangu i boji, neprevedene zapise, više dopuštenih slavlja
te datume za koje jedan izvor nema podatke.
