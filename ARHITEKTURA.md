# Arhitektura i onboarding

Ovaj dokument je početna karta projekta. Cilj strukture je da HTTP sloj samo
usmjerava zahtjev, a poslovna pravila ostanu u servisima koji se mogu zasebno
testirati.

## Tokovi zahtjeva

### Prijava

```text
pastoral/urls.py
  -> pastoral/view_modules/authentication.py
  -> pastoral/services/otp.py
  -> pastoral/tasks.py
  -> pastoral/services/mail.py
```

`authentication.py` upravlja HTTP odgovorima i porukama. Generiranje,
provjera, ograničenja i isporuka OTP-a pripadaju isključivo `otp.py`.
Celery task samo izvršava pozadinsko slanje, a `mail.py` sastavlja poruku.

### Administracijska stranica

```text
pastoral/urls.py
  -> pastoral/views.py
  -> pastoral/page_handlers.py
  -> pastoral/services/<domena>.py
  -> predložak u templates/pastoral/pages/
```

GET kontekst stranice gradi `page_handlers.py`, koristeći domenski servis.
`views.py` provjerava pristup, bira predložak i orkestrira zahtjev.

POST obrazac prolazi ovim putem:

```text
pastoral/views.py
  -> pastoral/actions.py
  -> pastoral/page_actions/dispatcher.py
  -> pastoral/page_actions/<domena>.py
  -> pastoral/services/data.py
```

Handler akcije prepoznaje samo vlastitu domenu. Izračune i složenije
usklađivanje relacijskih zapisa treba prepustiti servisu.

### JSON akcija

```text
pastoral/api_views.py
  -> pastoral/services/api_actions.py
  -> pastoral/services/api_action_handlers/<domena>.py
  -> pastoral/services/data.py
```

`api_actions.py` je kompatibilna fasada i registar stabilnih naziva akcija.
Nova domenska implementacija ide u `api_action_handlers`, ne u API view.

### Javne prijave

```text
pastoral/urls.py
  -> pastoral/view_modules/public_forms.py
  -> pastoral/services/public_forms.py
  -> pastoral/tasks.py
```

Javni view sprema prijavu prije slanja obavijesti. Neuspjelo slanje ne smije
izbrisati već zaprimljenu prijavu.

## Odgovornosti direktorija

- `pastoral/view_modules/` — samostalni HTTP tokovi poput prijave i javnih obrazaca.
- `pastoral/views.py` — zajednički shell, administracijske stranice i kompatibilni re-export viewova.
- `pastoral/page_handlers.py` — GET kontekst i odabir domenskog page servisa.
- `pastoral/page_actions/` — POST naredbe klasičnih Django obrazaca.
- `pastoral/services/` — poslovna pravila, upiti, transformacije i integracije.
- `pastoral/services/api_action_handlers/` — domenske mutacije stabilnog JSON API-ja.
- `pastoral/models.py` i `pastoral/registry_models.py` — podatkovni model.
- `control_plane/` — tenant, članstva, licence i tehnička administracija.
- `phase_two/` — kod koji nije dio aktivnog MVP proizvoda.
- `website_project/` — zasebna javna web-stranica i zaseban deployment.

## Gdje dodati novu funkcionalnost

Za novu administracijsku stranicu:

1. Dodati stabilni slug u `ADMIN_PAGES` i `PAGE_TEMPLATE_NAMES`.
2. Dodati naslov u `PAGE_META` i GET kontekst u domenski servis.
3. Registrirati navigaciju u `pastoral/services/permissions.py`.
4. Dodati predložak u `templates/pastoral/pages/`.
5. Ako postoji POST, dodati domenski handler u `page_actions/` i registrirati ga u dispatcher.
6. Dodati test URL-a, ovlasti, prikaza i svake mutacije.

Za novu JSON akciju:

1. Implementirati je u odgovarajućem `api_action_handlers` modulu.
2. Registrirati postojeće javno ime u `ACTION_HANDLERS`.
3. Jasno označiti mijenja li podatke ili je samo za čitanje.
4. Testirati isti naziv akcije, ulazne ključeve i oblik odgovora.

## Ugovori koji moraju ostati stabilni

- postojeći URL-ovi i redirecti;
- nazivi POST akcija i JSON akcija;
- camelCase ključevi koje koriste predlošci i JavaScript;
- spremljeni parish JSON i relacijski zapisi;
- redoslijed spremanja kod javnih prijava i sinkronizacije matičnih zapisa;
- hrvatski tekstovi i postojeće ponašanje sučelja.

Promjena bilo kojeg od ovih ugovora zahtijeva migraciju ili kompatibilni sloj
te ciljane regresijske testove.

## Lokalna provjera

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check
docker compose exec web python manage.py test pastoral.tests.test_route_smoke
docker compose exec web python manage.py test
```

Prvo treba pokrenuti testove promijenjene domene, a zatim cijeli paket. Pad koji
je postojao prije izmjene treba zabilježiti odvojeno; refaktor ga ne smije
prikriti niti usput mijenjati.
