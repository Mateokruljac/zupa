# Implementacijska analiza: zajednička crkvena evidencija i matične knjige

## 1. Svrha dokumenta

Ovaj dokument prilagođava dostavljeni implementacijski brief stvarnom stanju repozitorija. Ne predstavlja odobrenje za implementaciju svih faza odjednom. Njegova je svrha odrediti najmanju sigurnu nadogradnju koja:

- čuva postojeće URL-ove, ekrane i korisničke tijekove;
- ne prekida postojeće sakramentalne, obiteljske, financijske i dokumentacijske funkcije;
- postupno zamjenjuje osjetljive operativne JSON zapise relacijskom jezgrom;
- razdvaja osobu, kanonsku pripadnost, događaj i službeni upis;
- podržava latinsku i istočnu katoličku tradiciju bez dvije aplikacije;
- ostaje jednostavna svećeniku koji ne treba poznavati kanonski ni tehnički podatkovni model.

## 2. Sažetak postojećeg sustava

### 2.1. Tehnički okvir

- Aplikacija je Django 4.2 projekt s PostgreSQL bazom.
- Glavne aplikacije su `pastoral`, `control_plane` i `users`.
- `pastoral` sadrži korisničke ekrane, obrasce, servise, akcije stranica i većinu domenske logike.
- `control_plane` sadrži tenant članstva, licence, podatke o tenant bazama i nepromjenjivi control-plane audit.
- `users` sadrži prilagođeni korisnički model i stariju, grublju podjelu uloga.
- Postoje Celery i Redis, ali trenutačni matični tijekovi rade sinkrono.

### 2.2. Tenant model

Tenant je trenutačno župa (`pastoral.Parish`). Svaka župa ima jedinstveni `tenant_id`.

Aktivna župa ne dolazi iz parametra klijenta, nego iz točno jednog važećeg `ParishMembership` zapisa prijavljenog korisnika. `TenantContextMiddleware` postavlja provjereni kontekst zahtjeva, a `ParishDataService` iz njega dohvaća župu.

To je dobra osnova i treba je zadržati. Novi tenant model nije potreban.

Važno ograničenje: `TenantDatabase` opisuje moguću zasebnu bazu po župi, ali aplikacija trenutačno sve ORM upite izvršava kroz zadanu Django vezu. Za prvu fazu nove evidencije treba koristiti sadašnji provjereni `Parish` opseg, bez uvođenja database routera ili nove strategije izolacije.

### 2.3. Trenutačna pohrana operativnih podataka

Relacijski modeli u `pastoral` aplikaciji trenutačno postoje samo za:

- župu;
- OTP izazove;
- uvoz liturgijskog kalendara;
- pojedinačne globalne liturgijske zapise.

Gotovo svi svakodnevni župni podaci pohranjeni su u jednom `Parish.data` JSON dokumentu, uključujući:

- obitelji i njihove članove;
- krštenja;
- prvopričesnike;
- krizmanike;
- vjenčanja;
- pogrebe;
- pomazanja;
- matične knjige i generičke matične zapise;
- javne prijave;
- posjete, financije, događaje i druge module.

`ParishDataService.load()` kopira cijeli dokument, normalizira ga, a `save()` prepisuje cijeli JSON. To je prihvatljivo za prototip i male podatke, ali nije dovoljno sigurna jezgra za dugotrajne službene matice, konkurentno numeriranje, audit, zaključavanje zapisa, relacijsko povezivanje osoba i serversku paginaciju.

### 2.4. Osobe

Ne postoji jedinstveni relacijski model osobe.

Ista stvarna osoba može se pojaviti kao:

- član obitelji u `families[].members`;
- supružnik u `families[].husband` ili `families[].wife`;
- krizmanik u `confirmations[].candidates`;
- prvopričesnik u `firstCommunion[].candidates`;
- dijete, roditelj ili kum kao tekst u zapisu krštenja;
- jedan ili oba supružnika kao tekst u zapisu vjenčanja;
- pokojnik ili kontakt obitelji u zapisu pogreba.

OIB postoji samo na dijelu zapisa krizmanika i trenutačno je slobodno JSON polje. Ne postoji zajednička provjera, indeks, jedinstvenost, povijest ni siguran način prikaza.

Zaključak: jedinstvena osoba jest potrebna, ali automatsko spajanje postojećih zapisa samo po imenu nije sigurno.

### 2.5. Sakramenti i formacija

Postojeći moduli nisu samo matice. Oni istodobno vode operativnu pripravu i dio službene evidencije:

- `baptisms` sadrži termin, roditelje, kumove, slavitelja, status, matični broj i podatke o prilogu;
- `confirmations` i `firstCommunion` organizirani su po godinama i skupinama;
- `weddings` sadrži pripravu, dokumente, kontakt, svjedoke i slavitelja;
- `funerals` sadrži termin, groblje, kontakt obitelji i misu zadušnicu;
- `anointing` je prije svega operativni raspored posjeta.

To znači da se novi `SacramentalEvent` ne smije tretirati kao zamjena za cijeli postojeći modul. Operativni predmet priprave i službeni događaj moraju se moći povezati, ali nisu uvijek isti zapis ni isti životni ciklus.

### 2.6. Matične knjige

Postojeći ekran već ima dobar i korisniku razumljiv tijek:

1. odabir knjige;
2. odabir godine;
3. tablica zapisa;
4. detalji zapisa u modalu;
5. dodavanje knjige, godine i zapisa.

U pozadini su `registryBooks` i `registryEntries` JSON kolekcije. Za standardne vrste knjiga zapisi se ne spremaju kao `registryEntries`, nego izravno u `baptisms`, `weddings`, `funerals` ili `confirmations`. Servis `registry_books.py` zatim iz tih odvojenih struktura gradi zajednički prikaz.

Posljedica je da matični upis i događaj trenutačno nisu odvojeni. Matični broj nalazi se na događaju, knjiga nema stabilnu vezu na događaj, a statusi su slobodan tekst.

Pozitivno je što sustav već odbija brisanje cijele matične knjige. Međutim, pojedinačni sakramentalni zapisi trenutačno se mogu fizički ukloniti iz JSON polja.

### 2.7. Predlošci i dokumenti

Postoji jednostavan sustav JSON predložaka dokumenata i A4 ispisa/PDF-a. Može se ponovno upotrijebiti za početne potvrde i prikaz, ali trenutačno nema:

- verzioniranje objavljenih predložaka;
- prava po predlošku;
- trajnu evidenciju generiranog dokumenta;
- audit ispisa i izvoza;
- vezu dokumenta sa službenim matičnim upisom;
- stvarni model datoteka i privitaka.

Excel izvoz matičnih knjiga nije pronađen. CSV ne treba uvoditi jer je ranije odlučeno da se neće koristiti.

### 2.8. Autorizacija i audit

Postoji dobra osnovna zaštita stranica po modulu i ulozi. Ipak, ona nije dovoljna za službene matice:

- prava su uglavnom na razini cijelog ekrana, ne na razini sposobnosti poput potvrde, zaključavanja, ispravka ili izvoza;
- `permission_set` postoji na članstvu, ali ga pastoralni servis prava trenutačno ne koristi;
- JSON API za podatke i akcije provjerava prijavu, ali ne provjerava svaku domensku sposobnost istim pravilima kao stranice;
- control-plane audit pokriva upravljanje platformom, a ne promjene pastoralnih ili matičnih zapisa;
- ne postoji audit čitanja osjetljivih kanonskih bilješki, ispisa ni izvoza.

Novi matični modul zato treba vlastiti domenski audit, ali treba ponovno upotrijebiti obrazac nepromjenjivog audit događaja iz `control_plane` aplikacije.

## 3. Komponente koje treba ponovno upotrijebiti

| Postojeća komponenta | Način ponovne uporabe |
|---|---|
| `Parish` i `tenant_id` | Tenant opseg svih novih župnih podataka |
| `ParishMembership` | Izvor aktivne župe, uloge i budućih granularnih dozvola |
| `TenantContextMiddleware` | Jedini dopušteni izvor tenant konteksta zahtjeva |
| `ParishDataService` | Privremeni kompatibilni pristup starim JSON podacima, ne trajna jezgra novih matica |
| `pastoral_login_required` | Zaštita stranice, uz dodatne domenske provjere za mutacije |
| postojeći page action dispatcher | Ulazna točka za postojeće forme dok se ne uvedu fokusirani servisi naredbi |
| `registry_books.py` | Prezentacijski ugovor koji treba preusmjeriti na novi repozitorij bez promjene predloška u prvoj fazi |
| postojeći ekran matičnih knjiga | Sačuvati tok knjiga → godina → zapisi → modal |
| postojeći sakramentalni ekrani | Sačuvati operativne tijekove i postupno ih povezati s osobom/događajem |
| dokumentni predlošci i A4 ispis | Početna prezentacija potvrda, uz kasnije verzioniranje i audit |
| `ImmutableEventModel` obrazac | Smjernica za novi tenant-svjestan domenski audit |
| Django admin | Globalni referentni podaci, službeni predlošci i nadzor importa; ne svakodnevni rad svećenika |
| Celery | Tek za dokazano velike izvoze ili obavijesti; ne uvoditi ga u MVP bez potrebe |

## 4. Predloženi minimalni domenski model

Nazivi su radni i trebaju ostati opisni engleski Python identifikatori. Korisnički nazivi ostaju hrvatski i ovise o tradiciji.

### 4.1. Globalni referentni podaci

#### `ChurchSuiIuris`

- `id` UUID;
- `code` stabilan i jedinstven;
- `official_name`;
- `short_name`;
- `canonical_tradition`: `LATIN` ili `EASTERN`;
- `default_liturgical_tradition`, nullable;
- `is_active`;
- vremenske oznake.

#### `EcclesiasticalJurisdiction`

- `id` UUID;
- `code`;
- `official_name`;
- `jurisdiction_type`: biskupija, nadbiskupija, eparhija, arhieparhija ili drugo;
- `church_sui_iuris`;
- opcionalna nadređena jurisdikcija;
- `is_active`.

#### Proširenje `Parish`

Dodati nullable polja:

- `jurisdiction`;
- `church_sui_iuris`;
- `default_liturgical_tradition`.

Postojeće tekstualno `settings['diocese']` ne uklanjati u prvoj fazi. Ono ostaje kompatibilno polje dok se župa ručno ne poveže s provjerenom jurisdikcijom.

### 4.2. Osoba i pripadnost

#### `Person`

- `id` UUID;
- `parish` kao tenant opseg;
- `given_names`;
- `surname`;
- `birth_surname`;
- `sex`, nullable;
- `date_of_birth`, nullable;
- `place_of_birth`, nullable tekst ili buduća veza na mjesto;
- `father`, nullable self-FK;
- `mother`, nullable self-FK;
- `status`: aktivna, spojena, arhivirana;
- normalizirana polja za pretragu;
- vremenske oznake.

U prvoj fazi osoba pripada tenant opsegu župe. Ne uvoditi globalnu bazu svih vjernika između nepovezanih župa jer bi to stvorilo ozbiljan problem privatnosti i autorizacije.

OIB ne smije biti obvezan niti primarni ključ. Ako se uvede, preporuka je odvojiti:

- deterministički HMAC otisak za provjeru podudaranja unutar dopuštenog opsega;
- kriptiranu vrijednost samo ako je stvarno potrebno prikazati OIB;
- maskirani prikaz i strožu dozvolu za čitanje.

Ne uvoditi kriptiranje bez upravljanja ključevima, rotacije ključa i plana oporavka. Do tada je sigurnije OIB ne seliti u novu jezgru nego ga spremiti u običan novi stupac.

#### `ChurchEnrollment`

- `person`;
- `church_sui_iuris`;
- `valid_from`, nullable samo za povijesne/nepoznate zapise;
- `valid_until`, nullable;
- `enrollment_basis`;
- `decree_reference`;
- `previous_enrollment`, nullable;
- `status`: nepotvrđeno ili potvrđeno;
- autor i vrijeme evidencije.

Preklapajuća potvrđena razdoblja za istu osobu nisu dopuštena. Postojećim osobama ne treba izmišljati pripadnost; početno stanje može biti nepotvrđeno.

### 4.3. Događaj i sudionici

#### `SacramentalEvent`

- `id` UUID;
- `parish`;
- `event_type`;
- `event_date`;
- `place_name` i buduća opcionalna veza na mjesto;
- `celebrating_parish`, u MVP-u najčešće ista župa;
- `minister`, u prvoj fazi nullable veza na korisnika i tekstualni povijesni naziv;
- `liturgical_tradition`;
- `canonical_tradition`;
- `status`: draft, confirmed, locked, corrected, cancelled;
- `source`: manual, public_submission, legacy_import;
- vremenske oznake i autor.

#### `EventParticipant`

- `event`;
- `person`;
- `role`: recipient, father, mother, godparent, witness, spouse, minister, assistant;
- `display_order`;
- opcionalni povijesni tekst ako osoba još nije razriješena.

Tekstualni fallback potreban je za siguran uvoz starih zapisa bez automatskog stvaranja ili spajanja pogrešnih osoba. Novi ručni unosi trebaju preferirati vezu na osobu.

#### Tipizirani detalji

Za prvu vertikalnu cjelinu uvesti samo `BaptismDetails`. Ne stvarati odmah detaljne tablice svih sakramenata.

`BaptismDetails` treba imati samo podatke koji ne pripadaju zajedničkom događaju ni sudionicima, primjerice podatak o potvrdi kuma ili drugi potvrđeni specifični element obrasca.

Kršćansku inicijaciju (`ChristianInitiation` i `InitiationComponent`) treba projektirati u istoj migracijskoj seriji ili neposredno nakon provjere latinskog krštenja, ali korisnički tijek bizantske inicijacije ne smije se proglasiti gotovim bez stvarnog odobrenog obrasca Križevačke eparhije.

### 4.4. Matični predlošci, knjige i upisi

#### `RegisterTemplate`

- stabilni kod;
- vrsta knjige;
- tradicija i opcionalna Crkva sui iuris;
- razina vlasništva predloška: system, church, jurisdiction;
- status.

#### `RegisterTemplateVersion`

- predložak;
- broj verzije;
- status: draft, published, retired;
- `field_schema` za dodatna/prezentacijska polja;
- `validation_schema` za dopuštena deklarativna pravila;
- `terminology`;
- `print_configuration`;
- datum primjene;
- objavio i vrijeme objave.

Objavljena verzija ne smije se mijenjati. Za MVP nije potreban opći form builder. Dovoljne su kodom kontrolirane definicije latinskog krštenja i, nakon potvrde obrasca, bizantske inicijacije.

#### `RegisterBook`

- `parish`;
- `template_version`;
- naziv;
- volumen/svezak;
- `year_from` i `year_to`, nullable;
- lokacija;
- skrbnik;
- status: draft, active, locked, archived;
- napomena;
- vremenske oznake.

Godina se ne treba modelirati posebnom fizičkom tablicom samo radi prikaza. Postojeći UX dodavanja godine može koristiti mali `RegisterBookYear` samo ako godina ima vlastiti status, numeriranje ili zaključavanje. Budući da postojeći sustav izričito omogućuje prazne retroaktivne godine, preporuka je uvesti `RegisterBookYear` s:

- knjigom i godinom;
- statusom;
- posljednjim dodijeljenim rednim brojem;
- jedinstvenim ograničenjem knjiga + godina.

#### `RegisterEntry`

- `parish`;
- `register_book_year`;
- `event`;
- `template_version` prema kojoj je upis nastao;
- `entry_number` kao broj i opcionalni prikazni prefiks/sufiks;
- `page_number`, nullable;
- `entry_date`;
- `status`: draft, confirmed, locked, corrected, cancelled;
- `custom_values` samo za dopuštena dodatna polja;
- veza na prethodni upis kod kontroliranog ispravka;
- razlog ispravka;
- autor i vremenske oznake.

Jedinstvenost rednog broja mora biti osigurana baznim ograničenjem u opsegu godine knjige. Dodjela broja mora se izvesti u transakciji sa zaključavanjem odgovarajućeg `RegisterBookYear` retka.

#### `CanonicalAnnotation` i `ParishNotification`

Ove modele predvidjeti u shemi, ali njihovo korisničko sučelje ostaviti za kasniju fazu nakon potvrde stvarnih pravila i ovlasti.

#### `RegistryAuditEvent`

Neizbrisiv zapis s:

- župom;
- korisnikom;
- vrstom radnje;
- ciljnim modelom i identifikatorom;
- ishodom;
- sažetkom promijenjenih polja bez nepotrebnog kopiranja osjetljivih vrijednosti;
- korelacijskim identifikatorom;
- vremenom.

## 5. Što ne treba graditi u prvoj fazi

- dinamičko stvaranje SQL tablica ili stupaca;
- potpuno proizvoljan form builder;
- automatsko spajanje osoba po imenu i datumu;
- globalnu osobu dostupnu svim župama;
- novu autentikaciju ili novi tenant sustav;
- database-per-tenant routing;
- sve sakramente odjednom;
- OCR starih knjiga;
- automatske kanonske odluke;
- javnu genealogijsku tražilicu;
- konačne službene obrasce bez crkvenog odobrenja;
- novu biblioteku ili mikroservis bez dokazane potrebe.

## 6. Kompatibilnost i plan migracije

### 6.1. Temeljno pravilo

Ne provoditi jednokratnu migraciju koja odmah briše ili prepisuje `Parish.data`. Postojeći JSON trenutačno napaja nadzornu ploču, dugovanja, podsjetnike, dokumente, pretragu, operativno središte i više sakramentalnih ekrana.

### 6.2. Predloženi prijelaz

1. Dodati nove relacijske tablice kao prazne i neovisne o postojećim ekranima.
2. Dodati idempotentni analizator postojećih podataka koji samo izvještava:
   - broj zapisa po župi i vrsti;
   - prazne ili duplicirane legacy ID-eve;
   - moguće duplikate osoba;
   - nevaljane datume i matične brojeve;
   - statuse koji nemaju sigurno preslikavanje.
3. Uvesti `LegacyRecordLink` ili ekvivalentnu stabilnu mapu između JSON vrste/ID-a i novog relacijskog zapisa.
4. Napraviti idempotentni backfill krštenja bez brisanja izvora.
5. Ne spajati osobe samo po tekstualnom imenu. Kada nema sigurnog identifikatora, stvoriti zasebnu osobu ili nerazriješenog sudionika i označiti zapis za ljudsku provjeru.
6. Sve uvezene službene statuse postaviti na `legacy_imported`/`draft review`, osim kada postoji dovoljno pouzdan i potvrđen kriterij. Ne zaključavati ih automatski.
7. Uvesti servisni sloj koji može dati postojeći dictionary ugovor predlošcima i potrošačima, ali čita iz relacijske jezgre.
8. Po župi uključivati novi izvor podataka kontroliranom zastavicom tek nakon usporedbe broja i sadržaja zapisa.
9. Nakon prelaska jednog modula, prilagoditi sve njegove potrošače: ekran krštenja, matične knjige, potvrde, dashboard, dugovanja, podsjetnike i pretragu.
10. Legacy JSON kopiju zadržati nepromijenjenu kroz najmanje jedno stabilno izdanje i ukloniti je tek zasebnom, odobrenom migracijom.

### 6.3. Pisanje tijekom prijelaza

Preferirani cilj je jedan izvor istine, relacijska jezgra. Privremeno dvostruko pisanje dopušteno je samo unutar jedne baze i jedne `transaction.atomic()` cjeline, kroz jedan kompatibilni servis, s auditom i testom neuspjeha. Ne dopustiti da predložak, view i API zasebno održavaju dvije kopije.

Ako svi potrošači krštenja mogu biti prebačeni u istoj maloj fazi, bolje je izbjeći dvostruko pisanje i nakon provjerenog backfilla relacijsku jezgru odmah učiniti izvorom istine samo za krštenja.

### 6.4. Povratak na staro

Rollback prve vertikalne cjeline izvodi se isključivanjem feature flaga za novu relacijsku evidenciju. Novi retci se ne brišu. Legacy JSON ostaje dostupan za čitanje dok se ne potvrdi stabilnost.

## 7. Integracija s tenant modelom i autorizacijom

### 7.1. Tenant opseg

Svaki tenant-vlasnički model mora imati eksplicitni `parish` strani ključ, čak i kada se župa može izvesti kroz druge veze. To omogućuje jasna ograničenja, indekse, audit i obranu od pogrešno složenog upita.

Servisi trebaju primati provjereni `Parish` ili `TenantContext`; nikada ne prihvaćati `parish_id` iz obrasca kao autoritet.

Svi dohvatni i mutacijski upiti moraju filtrirati po aktivnoj župi. Dohvat zapisa samo po UUID-u nije dovoljan.

### 7.2. Sposobnosti

Postojeće `ParishMembership.permission_set` polje može podržati granularne sposobnosti bez novog sustava uloga. Predložene sposobnosti:

- `registry.view`;
- `registry.create_book`;
- `registry.create_draft`;
- `registry.edit_draft`;
- `registry.confirm_entry`;
- `registry.lock_entry`;
- `registry.correct_entry`;
- `registry.view_sensitive_annotations`;
- `registry.export`;
- `registry.manage_templates`;
- `registry.view_audit`.

Zadane mape po ulozi ne treba zaključati dok korisnik ne potvrdi tko u stvarnoj župi smije potvrditi, zaključati i ispraviti upis.

Stranice, POST akcije i JSON API moraju koristiti isti centralni servis provjere sposobnosti. Samo skrivanje gumba nije autorizacija.

### 7.3. Django admin

Django admin treba služiti za:

- globalne Crkve sui iuris i jurisdikcije;
- pregled i objavu predložaka uz odgovarajuće osoblje;
- nadzor migracijskih izvještaja;
- read-only pregled audita;
- upravljanje referentnim podacima.

Svakodnevni unos matičnih zapisa ostaje u postojećem pastoralnom frontendu.

## 8. Predloženi UX

### 8.1. Zadržati postojeću mentalnu mapu

Početni ekran matičnih knjiga ostaje:

**Knjiga → godina → zapisi → detalji**

Ne prikazivati korisniku tablice, verzije sheme, event participante ni tehničke statuse.

### 8.2. Novi zapis krštenja

Predloženi jednostavni tijek:

1. **Pronađite osobu** – pretraga po imenu, prezimenu i datumu rođenja; mogućnost „Dodaj novu osobu”.
2. **Osnovni podaci krštenja** – datum, mjesto, roditelji, kumovi i slavitelj.
3. **Matični upis** – knjiga i godina već su odabrani; redni broj sustav predlaže, korisnik ga potvrđuje.
4. **Pregled i spremanje** – spremi nacrt ili, uz ovlast, potvrdi upis.

Za uobičajenu latinsku župu ne prikazivati Crkvu sui iuris i liturgijsku tradiciju na vrhu obrasca. Zadane vrijednosti preuzeti sa župe. Ispod poveznice „Posebne okolnosti” prikazati ih samo kada je osoba ili slavlje druge tradicije.

Za istočnu župu isti ekran koristi odgovarajuće nazive i može objediniti krštenje, mirovanje i pričest u jednom vođenom unosu. To se aktivira predloškom, ne zasebnom aplikacijom.

### 8.3. Upozorenja

Razlikovati:

- informaciju;
- upozorenje koje ovlašteni korisnik može potvrditi;
- blokirajuću pogrešku.

Primjer mogućeg duplikata osobe treba biti upozorenje s izborom, a ne automatsko spajanje. Neobičan obred slavlja ne smije automatski mijenjati kanonsku pripadnost.

### 8.4. Zaključani zapis

Zaključani zapis prikazuje se read-only. Akcija „Ispravi zapis” otvara novi kontrolirani tijek koji traži razlog i prikazuje što će ostati zabilježeno. Ne nuditi obični „Uredi” ni „Obriši”.

## 9. Faze implementacije prilagođene ovom repozitoriju

### Faza 0 – završena analiza

- mapirana postojeća arhitektura;
- potvrđena župa kao tenant;
- potvrđena JSON operativna jezgra;
- identificirani svi glavni potrošači podataka krštenja i matica;
- definiran prijelaz bez brisanja podataka.

### Faza 1A – referentna i sigurnosna osnova

- modeli `ChurchSuiIuris` i `EcclesiasticalJurisdiction`;
- nullable veze na `Parish`;
- `Person` i `ChurchEnrollment`;
- tenant-svjestan queryset/servis;
- `RegistryAuditEvent`;
- centralne sposobnosti bez promjene postojećeg UI-ja;
- Django admin za referentne podatke.

### Faza 1B – najmanja vertikalna cjelina: latinsko krštenje

- `SacramentalEvent`, `EventParticipant` i `BaptismDetails`;
- `RegisterTemplate`, `RegisterTemplateVersion`, `RegisterBook`, `RegisterBookYear` i `RegisterEntry`;
- jedan kontrolirani latinski predložak krštenja;
- analizator i idempotentni backfill postojećih `baptisms` zapisa;
- kompatibilni read model za postojeći ekran krštenja, matice i potvrde;
- stvaranje nacrta, potvrđivanje i sigurno numeriranje;
- bez zaključavanja dok se ne potvrde ovlasti i postupak ispravka;
- feature flag po župi.

Ovo je najmanja cjelina koja stvarno provjerava osobu, događaj, sudionike, knjigu, upis, tenant, audit i postojeći UX.

### Faza 2 – kršćanska inicijacija i istočna tradicija

- stvarni obrazac i terminologija potvrđeni od Križevačke eparhije;
- `ChristianInitiation` i komponente;
- objedinjeni unos krštenja, mirovanja i pričesti;
- pravila koja ne mijenjaju automatski pripadnost osobe;
- drugi objavljeni predložak.

### Faza 3 – bilješke, obavijesti i dokumenti

- strukturirane kanonske bilješke;
- obavijesti drugoj župi ili kuriji;
- prava za osjetljive bilješke;
- veze na dokumente kada postoji stvarni model datoteka;
- audit ispisa i generiranja potvrda.

### Faza 4 – ostale evidencije jednu po jednu

Preporučeni redoslijed nakon potvrde obrazaca:

1. potvrda/mirovanje i prva pričest;
2. vjenčanja;
3. umrli i sprovodi;
4. ostale službene ili interne knjige.

Pomazanje ne treba automatski tretirati kao matičnu knjigu; trenutačno je operativni pastoralni raspored i treba zasebnu odluku o opsegu trajne evidencije.

### Faza 5 – Excel, potvrde i optimizacija

- `.xlsx` izvoz s aktivnim filterima i ovlastima;
- audit izvoza;
- serverska paginacija i indeksiranje;
- odobreni službeni ispisi;
- background obrada samo za stvarno velike izvoze.

## 10. Plan provjera

Iako se implementacija testova ne radi u ovoj analitičkoj fazi, svaka buduća faza treba imati razmjerne provjere.

### Domenska pravila

- događaj druge tradicije ne mijenja `ChurchEnrollment`;
- osoba i događaj uvijek ostaju u tenant opsegu;
- objavljena verzija predloška je nepromjenjiva;
- jedinstven redni broj u godini knjige;
- zaključani upis nije moguće izravno urediti ili obrisati;
- ispravak stvara audit i vezu na prethodno stanje;
- custom vrijednosti prihvaćaju samo definirana polja i tipove.

### Integracija

- postojeće krštenje može se uvesti bez gubitka podataka;
- ponovljeni backfill ne stvara duplikate;
- dva istodobna zahtjeva ne dobivaju isti redni broj;
- dokumenti i pretraga pronalaze zapis nakon prelaska na relacijsku jezgru;
- korisnik župe A ne može dohvatiti UUID zapisa župe B;
- POST i API provjeravaju istu sposobnost;
- isključivanje feature flaga vraća stari read path bez brisanja novih podataka.

### Regresija

- postojeći URL-ovi i navigacija;
- OTP i tenant članstvo;
- krštenja, matične knjige i potvrde;
- dashboard, dugovanja i podsjetnici koji koriste krštenja;
- javne prijave i njihov kontrolirani uvoz;
- Django admin.

## 11. Rizici

### Visoki rizik

1. **Jedan JSON dokument je trenutačni izvor istine za mnogo modula.** Nagli cutover može stvoriti nedosljedne dashboarde i dokumente.
2. **Ne postoji jedinstvena osoba.** Automatska deduplikacija može povezati pogrešne ljude.
3. **Statusi su slobodan tekst.** Nije sigurno automatski proglasiti postojeći zapis potvrđenim ili zaključanim.
4. **OIB nema siguran životni ciklus.** Običan novi stupac bez plana ključeva i pristupa povećao bi GDPR rizik.
5. **API sposobnosti su pregrube.** Novi osjetljivi endpointi ne smiju kopirati samo postojeću provjeru prijave.

### Srednji rizik

1. Predlošci dokumenata nemaju verzioniranje ni audit.
2. Ne postoji stvarni model dokumenata/privitaka.
3. `TenantDatabase` može sugerirati izolaciju koja još nije provedena kroz ORM routing.
4. Postojeće brisanje sakramentalnog zapisa nije kompatibilno sa zaključanim službenim upisom.
5. Struktura postojećih obiteljskih članova nije dovoljno potpuna za pouzdan automatski `Person` backfill.

## 12. Otvorena pitanja koja zahtijevaju potvrdu

### Obvezno prije Faze 1B

1. Koji je aktualni službeni obrazac latinske matice krštenih koji koristi prva ciljna župa?
2. Koja su polja obvezna, a koja samo lokalno korisna?
3. Numerira li se redni broj po knjizi, volumenu, kalendarskoj godini ili drugačije?
4. Tko smije potvrditi, zaključati i ispraviti upis?
5. Treba li prvi MVP obuhvatiti samo nove upise ili i retroaktivni unos starih knjiga?
6. Je li OIB uopće potreban za matice ili samo za pojedine prijave i provjeru identiteta?
7. Smije li župni suradnik vidjeti pune osjetljive bilješke i OIB?
8. Koji se postojeći statusi smatraju samo operativnima, a koji službenima?

### Obvezno prije istočne inicijacije

1. Aktualni prazan obrazac i anonimizirani primjer Križevačke eparhije.
2. Točna terminologija za sučelje i ispis.
3. Pravila upisa krštenja, mirovanja i pričesti istoga dana.
4. Postupak kada osoba pripada drugoj Crkvi sui iuris.
5. Naknadne bilješke i obavijesti koje treba generirati.

## 13. Točan opseg prve implementacijske faze

Preporuka je da sljedeći odobreni zadatak bude samo **Faza 1A**, bez prebacivanja postojećih ekrana:

1. dodati referentne modele Crkve sui iuris i jurisdikcije;
2. dodati nullable veze na župu;
3. dodati tenant-svjestan model osobe i povijesti pripadnosti;
4. dodati nepromjenjivi domenski audit;
5. dodati centralni servis sposobnosti za buduće matične akcije;
6. dodati Django admin za te modele;
7. dodati read-only management naredbu koja analizira postojeće osobe, krštenja i kolizije bez promjene podataka;
8. ne mijenjati postojeće korisničke stranice ni JSON ugovor.

Nakon pregleda rezultata analizatora i potvrde stvarnog latinskog obrasca može započeti Faza 1B.

## 14. Završna arhitektonska odluka

Platforma ostaje jedna Django aplikacija i jedan korisnički proizvod. Razlike između latinske i istočne tradicije rješavaju se referentnim podacima, pravilima, terminologijom i verzioniranim predlošcima.

Trajna jezgra glasi:

**tenant-svjesna osoba + povijest pripadnosti Crkvi sui iuris + zajednički događaj i sudionici + odvojeni službeni matični upis + verzionirani predlošci + nepromjenjivi audit.**

Postojeći JSON sustav ne treba prepisati odjednom. Treba ga zamjenjivati po jednoj provjerljivoj vertikalnoj cjelini, počevši s krštenjem, uz kompatibilni adapter i mogućnost sigurnog povratka na stari read path.
