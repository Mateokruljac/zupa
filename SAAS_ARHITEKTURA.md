# SaaS arhitektura aplikacije Pastoral

Datum: 3. kolovoza 2026.  
Status: ciljana arhitektura i provedbeni standard  
Odluka: ADR-001 — bridge SaaS, zajednički control plane i zasebna baza po župi

## 1. Izvršna odluka

Pastoral će se razvijati kao SaaS s jednom verzijom aplikacije i centralnim upravljanjem. Župni poslovni podaci neće biti smješteni u zajedničke tablice svih župa.

Ciljani model:

- jedna zajednička, stateless Django aplikacija;
- jedna centralna control-plane baza;
- jedna zasebna PostgreSQL baza za svaku župu;
- zasebno ograničen prostor dokumenata za svaku župu;
- zajednički identitet korisnika, ali članstvo i ovlasti po župi;
- ručno evidentirana uplata i ručno odobrena ili obnovljena licenca;
- mogućnost dedicated deploymenta za posebno zahtjevnog korisnika, uz isti kod i operativni sustav.

To je bridge arhitektura: dijele se aplikacijski i operativni sloj, a osjetljivi podatkovni sloj izolira se po tenantu. AWS razlikuje silo, pool i bridge modele te navodi da i zasebna baza može biti silo komponenta SaaS-a kada identitet, onboarding, upravljanje i operacije ostanu objedinjeni. Microsoft posebno opisuje zajedničku aplikaciju sa zasebnom bazom svakog tenanta kao uobičajen horizontalno particioniran model.

Izvori:

- [AWS SaaS Lens — Silo, Pool and Bridge Models](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html)
- [AWS SaaS Lens — Bridge Model](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/bridge-model.html)
- [Azure — Tenancy Models](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models)
- [Azure — Multitenant Storage and Data](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)

## 2. Usporedba modela

| Model | Izolacija | Operativna složenost | Odluka |
|---|---:|---:|---|
| zajedničke tablice i `parish_id` | srednja | niska | odbijeno za poslovne podatke |
| schema po župi | visoka | srednja | nije primarna granica |
| baza po župi | vrlo visoka | srednja | zadani model |
| cijela instanca po župi | najviša | vrlo visoka | opcionalni dedicated tier |

### 2.1. Zašto ne samo `parish_id`

Jedan propušten tenant filtar, pogrešna administratorska akcija ili export može zahvatiti više župa. PostgreSQL Row-Level Security može biti dodatni sloj, ali nije dovoljna jedina granica: vlasnik tablice, superuser i `BYPASSRLS` uloge mogu ga zaobići, a backup i referencijalne operacije traže posebnu pažnju.

Izvor: [PostgreSQL — Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html).

### 2.2. Zašto ne `django-tenants`

[django-tenants](https://django-tenants.readthedocs.io/en/stable/use.html) je kvalitetan primjer tenant middlewarea, domenskog mapiranja i fleet migracija, ali koristi jednu PostgreSQL bazu sa schemom po tenantu. Time svi tenant podaci ostaju u istoj fizičkoj bazi i backupu. Njegove obrasce možemo proučiti, ali neće biti sigurnosni temelj Pastorala.

### 2.3. Zašto ne puna instanca kao zadana vrijednost

Puna instanca po župi otežava zakrpe, monitoring, certifikate, backup, migracije i sprječavanje version drifta. AWS full-silo i Azure deployment-stamp smjernice taj model smatraju valjanim SaaS-om samo uz zajednički, automatizirani onboarding i operacije. Zato ostaje iznimka za ugovoreni dedicated deployment.

## 3. Tenant i organizacijska hijerarhija

Župa je tenant i primarna sigurnosna granica.

Biskupija je organizacijska cjelina koja može grupirati župe, administrirati licence i primati formalno predane izvještaje. Pripadnost biskupiji sama po sebi ne daje pristup župnim kartonima, sakramentima, bilješkama ili financijama.

`User` je globalni identitet fizičke osobe. Uloga mora biti na članstvu jer ista osoba može imati različitu službu u različitim župama.

~~~text
User
  └── ParishMembership
        ├── parish
        ├── role
        ├── permission_set
        ├── valid_from / valid_until
        ├── status
        └── approved_by / revoked_by
~~~

AWS SaaS identitet definira kao spoj korisničkog i tenant konteksta. Tenant kontekst mora pratiti autorizaciju, podatke, cache, zadatke, logove i metrike.

Izvor: [AWS SaaS Lens — SaaS Identity](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-identity.html).

## 4. Ciljna logička arhitektura

~~~mermaid
flowchart TB
    U["Korisnik"] --> EDGE["TLS reverse proxy / WAF"]
    EDGE --> APP["Zajednička Django aplikacija"]
    APP --> CP["Control plane"]
    APP --> AUTHZ["Tenant-aware autorizacija"]
    APP --> JOBS["Celery · tenant-aware zadaci"]
    CP --> CDB["Centralna control-plane baza"]
    AUTHZ --> ROUTER["Fail-closed database router"]
    ROUTER --> DB1["PostgreSQL · župa A"]
    ROUTER --> DB2["PostgreSQL · župa B"]
    ROUTER --> DB3["PostgreSQL · župa C"]
    APP --> OBJ["Tenant-izolirani dokumenti"]
    APP --> CACHE["Redis · tenant-prefiksirani ključevi"]
    APP --> AUDIT["Append-only audit / SIEM"]
    CP --> SECRETS["Secrets manager / KMS"]
~~~

### 4.1. Control plane

Centralna baza sadrži samo upravljačke podatke:

- korisnike i autentikatore;
- biskupije i tenant katalog župa;
- domene i članstva;
- platformne uloge i permission setove;
- katalog tenant baza bez čitljivih lozinki;
- licence, ručne uplate i entitlements;
- provisioning i migration jobove;
- platformni audit i minimalnu telemetriju.

Microsoft control plane definira kao odvojeni sloj za tenant katalog, onboarding, placement, provisioning, održavanje i telemetriju.

Izvori:

- [Azure — Control Plane Considerations](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/control-planes)
- [Azure — Control Plane Approaches](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/control-planes)

### 4.2. Tenant data plane

Svaka župa dobiva PostgreSQL bazu s istom verzijom sheme. U njoj su osobe, obitelji, pastoralna skrb, sakramenti, matice, nakane, zadaci, financije, dokumenti i lokalni audit.

Ne smiju postojati Django FK/M2M veze između centralne i tenant baze. Django ih službeno ne podržava. Reference na centralnog korisnika spremaju stabilni UUID, a provjerava ih servisni sloj.

Izvor: [Django — Multiple Databases](https://docs.djangoproject.com/en/5.2/topics/db/multi-db/).

### 4.3. Dokumenti

- dokument uvijek ima tenant UUID u metapodacima;
- storage path ne dolazi iz korisničkog inputa;
- download URL je kratkotrajan i nastaje tek nakon autorizacije;
- koristi se zaseban bucket ili stroga tenant particija;
- poželjan je zaseban enkripcijski ključ po župi;
- obvezni su malware scan, type i size provjera;
- auditira se upload, čitanje, export i brisanje;
- dokumenti se ne poslužuju s aplikacijske origin domene.

## 5. Tenant context i database router

Tenant se ne smije vjerovati iz skrivenog polja, proizvoljnog headera, query parametra, ID-a objekta ili localStoragea.

Siguran tok:

1. korisnik se autentificira;
2. server učitava aktivna `ParishMembership` članstva;
3. korisnik bira aktivnu župu ili se koristi jedina dostupna;
4. server sprema provjereni tenant UUID u server-side session;
5. svaki zahtjev ponovno provjerava aktivno članstvo;
6. license servis provjerava licencu;
7. tenant context postavlja se u `ContextVar`;
8. database router odabire tenant bazu;
9. context se čisti u `finally` bloku.

Subdomena može biti UX signal, ali se mora presjeći s članstvom. Hostname nije autorizacija.

OWASP preporučuje tenant kontekst iz autentificiranog identiteta te tenant-aware queryje, cache ključeve, storage paths i logove.

Izvor: [OWASP — Multi Tenant Security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html).

Router mora raditi fail-closed:

- control modeli idu samo na centralnu bazu;
- tenant model bez konteksta izaziva sigurnosnu iznimku;
- nema fallbacka tenant queryja na `default`;
- nepoznata ili neaktivna tenant baza izaziva iznimku;
- međubazne relacije su zabranjene;
- migracije se dopuštaju samo odgovarajućoj vrsti baze;
- web proces ne koristi DB superusera;
- raw SQL zahtijeva eksplicitnu bazu i security review.

## 6. Transakcije i asinkroni rad

Poslovna transakcija ograničena je na jednu tenant bazu. Ne projektira se atomski commit između control i tenant baze.

Za međubazne procese koriste se lokalna transakcija, outbox zapis, idempotentni handler, idempotency key, ograničeni retry, dead-letter queue i kompenzacijska radnja.

Svaki Celery tenant zadatak nosi `tenant_id`, `actor_id`, `correlation_id` i `idempotency_key`. Worker ponovno provjerava tenant u control planeu i nikada ne vjeruje connection stringu iz poruke.

## 7. Ručno upravljana licenca

U kodu se neće koristiti payment-gateway pretplata. Poslovni pojmovi su:

- `LicenseGrant` — pravo korištenja u razdoblju;
- `ManualPayment` — evidentirana bankovna uplata;
- `LicenseEntitlement` — ugovorene funkcionalnosti;
- `LicenseDecision` — aktivacija, obnova, suspenzija ili prekid.

Uplata i licenca nisu isti zapis. Uplata je financijska činjenica, a licenca administrativna odluka. Jedna uplata može pokriti više razdoblja ili više župa.

Microsoft razlikuje privremene rollout feature flags od trajnih license entitlementa.

Izvor: [Azure — Deployment and Configuration](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/deployment-configuration).

### 7.1. `LicenseGrant`

- UUID i tenant UUID;
- status;
- `valid_from`, `valid_until`, `grace_until`;
- plan i terms version;
- opcionalni seat limit;
- odobrio/tko/kada;
- suspenzija, razlog i odgovorna osoba;
- timestamps i optimistic-lock verzija.

### 7.2. `ManualPayment`

- UUID i tenant UUID;
- iznos, valuta i datum valute;
- platitelj i bankovna referenca;
- hash ili zaštićena referenca dokaza;
- pokriveno razdoblje;
- status `recorded / verified / rejected / reversed`;
- evidentirao i provjerio;
- bilješka bez nepotrebnih osobnih podataka.

U produkciji osoba koja evidentira uplatu ne potvrđuje vlastiti unos.

### 7.3. Stanja i pristup

~~~text
PENDING → ACTIVE → GRACE → EXPIRED
             └────→ SUSPENDED → ACTIVE ili TERMINATED
EXPIRED ──nova potvrđena licenca──→ ACTIVE
~~~

| Stanje | Prijava | Čitanje | Izmjene | Export |
|---|---:|---:|---:|---:|
| `PENDING` | da | onboarding | ne | ne |
| `ACTIVE` | da | da | da | prema ovlasti |
| `GRACE` | da | da | da uz upozorenje | prema ovlasti |
| `EXPIRED` | da | read-only | ne | kontrolirano |
| `SUSPENDED_SECURITY` | ograničeno | ne | ne | ne |
| `TERMINATED` | ne | ne | ne | samo offboarding |

Kašnjenje uplate nakon grace perioda stavlja župu u read-only, ne briše niti skriva njezine podatke. Sigurnosna suspenzija zaseban je i stroži status.

### 7.4. Ručna obnova

1. administrator evidentira uplatu;
2. druga osoba provjerava izvod/reference;
3. sustav predlaže novo razdoblje bez preklapanja;
4. ovlaštena osoba potvrđuje `LicenseDecision`;
5. nastaje nova nepromjenjiva licencna odluka;
6. tenant dobiva obavijest;
7. sve se zapisuje u append-only audit.

Ne brišu se stare uplate i ne prepisuju stara razdoblja bez povijesti. Opis bankovne transakcije nikada sam ne aktivira licencu.

## 8. Onboarding i offboarding

Onboarding:

1. tenant zapis i nepromjenjivi UUID;
2. deployment stamp/region;
3. zasebna PostgreSQL baza i najmanje privilegirani račun;
4. secret u secrets manageru;
5. tenant migracije;
6. storage particija i ključ;
7. početna licenca;
8. poziv administratora župe;
9. najmanje dva snažna autentikatora;
10. smoke i izolacijski test;
11. aktivacija i audit.

Onboarding je idempotentan i ne smije ostaviti polukreiranu aktivnu župu.

Tenant lifecycle odvojen je od licence:

~~~text
PROVISIONING → ACTIVE → SUSPENDED → OFFBOARDING → ARCHIVED → DELETED
~~~

Offboarding uključuje retention/legal-hold provjeru, kontrolirani export, opoziv članstava i sesija, uklanjanje zadataka, arhivski backup, opoziv ključeva i dokaz brisanja kada rok dopušta.

## 9. Tajne, cache i audit

`TenantDatabase` sprema tenant UUID, interni alias, provider/stamp, database resource ID, `secret_ref`, status, schema verziju i status migracije/backupa. Ne sprema lozinku ni connection string.

OWASP preporučuje centralizirano upravljanje, audit i rotaciju tajni te zabranu hardkodiranih i zajedničkih vjerodajnica.

Izvor: [OWASP — Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).

Cache ključ:

~~~text
pastoral:{environment}:{tenant_uuid}:{namespace}:{version}:{key}
~~~

Svaki log sadrži tenant UUID ili `control-plane`, actor UUID, correlation ID, event code i outcome. Ne sadrži OTP, session/token, connection string, pastoralnu bilješku, zdravstveni detalj ili dokument.

Izvor: [OWASP — Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

## 10. Django admin i support access

Frontend služi radu unutar aktivne župe. Django admin služi control planeu, onboarding procesu, licencama, migracijama i tehničkim kontrolama.

Platform administrator nema automatski neograničen pregled tenant poslovnih podataka. Support access zahtijeva tenant, razlog/ticket, vremensko ograničenje, step-up autentikaciju, audit i po mogućnosti odobrenje druge osobe. Tiho impersoniranje nije dopušteno.

## 11. Fleet migracije

Django `migrate` radi nad jednom bazom odjednom. Tenant migration orchestrator mora:

1. provjeriti kompatibilnost koda i sheme;
2. odabrati canary tenant baze;
3. napraviti restore point;
4. migrirati;
5. pokrenuti health/integrity provjere;
6. nastaviti u valovima;
7. zaustaviti rollout na kritičnoj grešci;
8. zapisati rezultat po tenantu;
9. koristiti expand-contract za destruktivne promjene.

Aplikacija tijekom rolling deploymenta treba tolerirati trenutačnu i prethodnu schema verziju.

## 12. Backup i observability

Za svaku župu potrebni su šifrirani backup, PITR gdje je dostupan, zadnji status, periodični restore u izolirano okruženje, integrity/smoke test, definirani RPO/RTO i odvojene backup ovlasti.

Database-per-tenant omogućuje vraćanje jedne župe bez vraćanja drugih.

Operativni dashboard mora imati globalni i tenant prikaz: pogreške, latency, queue backlog, DB veze, storage, backup, schema verziju, exporte i resursni trošak.

Izvor: [AWS SaaS Lens — General Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/general-design-principles.html).

## 13. Testna strategija

Obvezni A/B izolacijski testovi:

- korisnik A ne može odabrati B;
- URL ID objekta B nije dostupan A;
- A ne može mutirati, pretražiti ili exportati B;
- tenant queryset bez konteksta pada;
- Celery i cache A ne mogu otvoriti B;
- dokument A nije dostupan B;
- support access bez formalnog granta pada;
- opozvano članstvo odmah gubi pristup;
- istekla licenca daje očekivani read-only način.

Operativni testovi obuhvaćaju nastavak prekinutog onboardinga, izoliran neuspjeh migracije, restore jedne župe, rotaciju jedne vjerodajnice, noisy-neighbor load i potpuni offboarding.

Zaštita se projektira od početka uz minimalan skup podataka i najrestriktivniji zadani pristup.

Izvor: [European Commission — Data protection by design and by default](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/obligations/what-does-data-protection-design-and-default-mean_en).

## 14. Migracija postojećeg projekta

Sadašnji kod ima centralni `Parish`, veliki `Parish.data` JSON i `ParishDataService()` koji implicitno bira `PARISH_DEFAULT_SLUG`. To ostaje za demo, ali ne smije postati produkcijski tenant mehanizam.

### Faza 0 — odluke i ograde

- bez stvarnih podataka;
- ukloniti demo superuser nakon prezentacije;
- klasificirati svaki model kao control ili tenant;
- odabrati hosting, region i secrets manager;
- definirati broj župa, RPO/RTO i retention.

### Faza 1 — control-plane modeli

- stabilni Parish UUID i lifecycle status;
- `Diocese` i `ParishMembership`;
- uloga se seli s `User` na članstvo;
- `LicenseGrant`, `ManualPayment`, `LicenseEntitlement`, `LicenseDecision`;
- `TenantDatabase` katalog;
- append-only control-plane audit;
- postojeći frontend i JSON nastavljaju raditi.

### Faza 2 — tenant context u shadow načinu

- resolver, `ContextVar`, middleware i fail-closed router;
- prvo samo evidentirati mjesta bez konteksta;
- servisi dobivaju eksplicitni tenant;
- produkcija nema implicitni default tenant;
- svi postojeći testovi ostaju zeleni.

### Faza 3 — dvije razvojne tenant baze

- dvije testne PostgreSQL baze;
- tenant migration naredba;
- A/B izolacijski testovi;
- tenant-aware Celery, cache i storage prototip.

### Faza 4 — prvi vertikalni modul

Prvi kandidat su misne nakane:

- relacijski tenant model;
- validacijski import iz JSON-a;
- usporedni read-only izvještaj;
- kontrolirani cutover;
- bez dugotrajnog dual-writea;
- rollback putem backupa i starog read patha.

### Faza 5 — inkrementalna ekstrakcija

1. kalendar i zadaci;
2. osobe, obitelji i adrese;
3. posjeti i pastoralna skrb;
4. sakramentalni predmeti;
5. dokumenti i matice;
6. financije;
7. međužupni predmeti.

Na kraju `Parish.data` ostaje samo arhivski import snapshot, a demo JSON postaje fixture.

## 15. Produkcijski deployment

Početno:

- jedan EU deployment stamp;
- najmanje dvije web replike;
- produkcijski WSGI/ASGI, ne `runserver`;
- odvojeni workeri;
- managed PostgreSQL s odvojenim tenant bazama;
- connection pooler i limiti;
- privatni Redis i object storage;
- secrets manager/KMS;
- centralni monitoring i append-only audit;
- Infrastructure as Code;
- staging bez kopije stvarnih podataka.

Kod rasta tenant katalog dodjeljuje župe deployment stampovima.

Izvor: [Azure — Deployment Stamps](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp).

## 16. No-go odluke

- nema zajedničkih poslovnih tablica svih župa uz oslanjanje samo na tenant filtar;
- nema tenant ID-a kojem se vjeruje iz browsera;
- nema fallbacka na default tenant;
- nema DB lozinki u katalogu, kodu ili logu;
- nema cross-database FK/M2M;
- nema posebnog koda ili brancha po župi;
- nema automatske licence iz neprovjerenog bankovnog opisa;
- nema hard deletea uplata, licenci, matica i audita;
- nema tihog platform-admin pregleda tenant podataka;
- nema stvarnih podataka prije izolacijskih testova i P0 kontrola iz `SECURITY_PLAN.md`.

## 17. Kriteriji prihvata prve SaaS faze

- tenant, članstvo, licenca i uplata imaju modele i migracije;
- demo frontend radi bez regresije;
- korisnik može imati različite uloge u dvije župe;
- neaktivno članstvo blokira tenant;
- licencna access matrica ima testove;
- ručna uplata i obnova imaju dual control i audit;
- connection katalog nema čitljivu vjerodajnicu;
- postoje negativni cross-tenant testovi;
- cijeli testni paket prolazi.

## 18. Otvorene poslovne odluke

Preporučene zadane vrijednosti su u zagradama:

1. očekivani broj župa u 1., 3. i 5. godini (planirati 100+, bez rewritea prema 1.000+);
2. nositelj licence: župa ili biskupija (župa, uz opcionalnog platitelja);
3. trajanje licence (12 mjeseci);
4. grace period (30 dana);
5. nakon grace perioda (read-only);
6. jedna uplata za više župa (da, zasebni grants);
7. tko evidentira i tko potvrđuje uplatu (dvije privilegije);
8. hosting provider i EU regija;
9. RPO, RTO i retention;
10. kontinuirani opseg biskupijskog pristupa;
11. dedicated deployment kao ponuda ili samo iznimka.

## 19. Neposredni sljedeći razvojni paket

Nakon potvrde arhitekture implementira se samo Faza 1, bez trenutnog prebacivanja produkcijskog database routera:

1. `control_plane` Django aplikacija;
2. Parish UUID/lifecycle migracija bez gubitka dema;
3. Diocese i ParishMembership;
4. licenca, ručna uplata, entitlement i odluke;
5. TenantDatabase sa `secret_ref` vrijednošću;
6. admin workflow ručne obnove;
7. append-only audit;
8. testovi članstva, licence i dual controla;
9. adapter koji `ParishDataService` dobiva eksplicitnu aktivnu župu;
10. dokumentirana naredba za uklanjanje demo superuser ovlasti.

Ovaj paket postavlja SaaS temelj bez rizičnog istodobnog preseljenja sadašnjih funkcionalnosti.

## 20. Referentni Django kostur

Ovo je ilustracija granica, ne kod za izravno kopiranje u produkciju.

### 20.1. Tenant context

~~~python
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID
    database_alias: str
    membership_id: UUID
    actor_id: UUID


active_tenant = ContextVar("active_tenant", default=None)


def require_tenant() -> TenantContext:
    context = active_tenant.get()
    if context is None:
        raise TenantContextMissing("Tenant operation without verified context")
    return context
~~~

Middleware nakon Django authentication middlewarea:

~~~python
class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        context = resolve_verified_tenant_context(request)
        token = active_tenant.set(context)
        request.tenant = context
        try:
            return self.get_response(request)
        finally:
            active_tenant.reset(token)
~~~

`resolve_verified_tenant_context()` smije vratiti kontekst tek nakon provjere korisnika, članstva, tenant lifecyclea i licence. Public i control-plane rute imaju eksplicitno označen način bez tenant konteksta; tenant rute ne smiju tiho nastaviti bez njega.

### 20.2. Fail-closed router

~~~python
class TenantDatabaseRouter:
    CONTROL_APPS = {"users", "control_plane", "admin", "auth", "sessions"}
    TENANT_APPS = {"tenant_core", "pastoral", "sacraments", "liturgy", "finance", "office"}

    def db_for_read(self, model, **hints):
        return self._database_for_model(model)

    def db_for_write(self, model, **hints):
        return self._database_for_model(model)

    def _database_for_model(self, model):
        app = model._meta.app_label
        if app in self.CONTROL_APPS:
            return "default"
        if app in self.TENANT_APPS:
            return require_tenant().database_alias
        raise UnclassifiedModelError(app)

    def allow_relation(self, obj1, obj2, **hints):
        return obj1._state.db == obj2._state.db

    def allow_migrate(self, db, app_label, **hints):
        if app_label in self.CONTROL_APPS:
            return db == "default"
        if app_label in self.TENANT_APPS:
            return db.startswith("tenant_")
        return False
~~~

Nepoznata aplikacija završava odbijanjem. To prisiljava razvojni tim da svaki novi model svjesno klasificira.

### 20.3. Registry konekcija

Django službeno očekuje baze u `DATABASES`. Zato se ne dodaje proizvoljan connection string iz requesta. Svaki deployment stamp ima ograničen skup tenanata, a trusted registry materijalizira njihove alias konfiguracije iz tenant kataloga i secrets managera pri startupu ili kontroliranom refreshu.

Pravila:

- alias je izveden iz UUID-a, ne iz slug-a;
- config dolazi samo iz control planea;
- secret se dohvaća identitetom procesa;
- registry odbija tenant iz drugog stampa;
- refresh je atomaran i auditiran;
- onboarding aktivira tenant tek kada ga svi potrebni procesi mogu razriješiti;
- connection pool i maksimalan broj konekcija ograničeni su po stampu i tenant bazi.

Time se ne oslanjamo na nekontrolirano mijenjanje `settings.DATABASES` usred zahtjeva.

### 20.4. License decision servis

~~~python
class LicenseAccess(str, Enum):
    FULL = "full"
    READ_ONLY = "read_only"
    ONBOARDING_ONLY = "onboarding_only"
    DENIED = "denied"


def evaluate_license(grant, now) -> LicenseAccess:
    if grant.security_suspended or grant.status == "terminated":
        return LicenseAccess.DENIED
    if grant.status == "pending":
        return LicenseAccess.ONBOARDING_ONLY
    if grant.valid_from <= now <= grant.valid_until:
        return LicenseAccess.FULL
    if grant.valid_until < now <= grant.grace_until:
        return LicenseAccess.FULL
    return LicenseAccess.READ_ONLY
~~~

Mutacijski endpoint ne provjerava samo login nego zahtijeva `FULL`. Query endpoint dopušta `FULL` ili `READ_ONLY` prema klasifikaciji resursa. Sigurnosna suspenzija uvijek ima prednost pred komercijalnim grace periodom.

### 20.5. Tenant-aware servis

Sadašnji obrazac:

~~~python
service = ParishDataService()  # implicitni default tenant
~~~

Prijelazni obrazac:

~~~python
service = ParishDataService(parish=request.tenant.parish)
~~~

Ciljani obrazac nakon relacijske ekstrakcije:

~~~python
service = MassIntentionService(
    tenant=require_tenant(),
    actor=request.user,
    authorizer=authorizer,
)
~~~

Servis autorizira radnju prije učitavanja podatka i ORM automatski koristi tenant alias kroz router. Controller ne prosljeđuje proizvoljni database alias.
