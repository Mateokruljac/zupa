# Pastoral — župna administracija

Django aplikacija za vođenje župnog ureda: vjernici, liturgija, sakramenti,
financije, isprave i uredski poslovi. Stranice se pretežno renderiraju na
serveru, a mali interni JSON API podržava OTP prijavu, liturgijski kalendar i
interaktivne liturgijske akcije.

Zadani razvojni tenant je **Župa Blažene Djevice Marije**, Slavonski Brod.

## Lokalno pokretanje

Lokalne postavke koriste PostgreSQL (isti kontejner `db` kao u
`docker-compose.yml`: baza/korisnik/lozinka `zupa`, port 5432). Cache i
Celery mogu ostati sinkroni; Mailhog i Redis trebaju se ako šaljete mail
ili pokrećete worker.

```bash
docker compose up -d db
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_pastoral
python manage.py runserver
```

`manage.py`, WSGI i ASGI u razvoju zadano koriste `zupa.settings.local`.
Izvan Dockera Django spaja se na `127.0.0.1:5432`.

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

`docker-compose.yml` pokreće web, PostgreSQL, Redis, Celery worker, Celery beat i Mailhog. Prije
pokretanja izradite lokalni `.env` te odaberite settings modul i vjerodajnice
za bazu (`DB_NAME`, `DB_USER`, `DB_PASS`; zadano je `zupa` / `zupa` / `zupa`).
Lokalni i produkcijski settings koriste PostgreSQL.

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

Romcal `croatia` radi lokalno (latinski locale). Pri uvozu godine hrvatski
naziv i liturgijska boja dolaze iz `liturgija/config/liturgical_days.json`
(ključ je latinski naziv slavlja). HILP i dalje dopunjuje čitanja.

Aktivni prikaz i API (`/api/liturgical/day/`, `/year/`, `/month/`) čitaju
retke `LiturgicalCalendarEntry` nakon uvoza u adminu.
