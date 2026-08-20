# Javne župne web-stranice

Ovo je samostalan Django projekt za javne web-stranice župa. Nije dio
administrativne aplikacije e-Župa i pokreće se kao zaseban proces, sa zasebnom
bazom, administratorskim računima, sesijama, CSRF kolačićima i medijskim
datotekama.

## Sigurnosna granica

- Projekt nema ovisnost o aplikacijama `pastoral`, `control_plane` ili `users`.
- Ne pristupa bazi e-Župe.
- Javni posjetitelj nema pristup administratorskim rutama e-Župe.
- Objavljuje samo sadržaj spremljen u polju `published_snapshot`.
- Buduća integracija mora gurati unaprijed odobren javni snapshot prema ovom
  projektu. Web-stranica ne smije povlačiti internu bazu e-Župe.
- Poveznice na javne prijave mogu se poslati u snapshotu kao vanjski URL-ovi;
  sami obrasci ostaju ograničeni servis e-Župe.

## Lokalno pokretanje

```powershell
cd website_project
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
$env:WEBSITE_DEBUG = "True"
python manage.py runserver 8001
```

Ili kao potpuno odvojen Docker deployment:

```powershell
cd website_project
docker compose up --build
```

Administracija je na `http://localhost:8001/admin/`, a javna stranica na
`http://localhost:8001/<poddomena>/`.

## Stari podaci

Izvorne migracije i testovi koji su ovisili o zajedničkoj bazi sačuvani su u
mapama `legacy_core_migrations` i `legacy_tests`. Ne učitavaju se u samostalni
projekt. Stare tablice nisu izbrisane iz baze e-Župe; njihov kontrolirani izvoz
u novu bazu treba napraviti kao zaseban migracijski postupak prije produkcije.
