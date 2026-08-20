# Cjenovni model i infrastrukturni troškovnik

Datum procjene: 3. kolovoza 2026.

> Ovaj dokument je radna poslovna procjena, a ne računovodstveni ili porezni savjet. Svi iznosi prihoda trebaju se promatrati bez PDV-a, poreza i drugih davanja. Stvarne cijene infrastrukture provjeravaju se prije produkcijskog ugovaranja.

## Sažeta preporuka

- Puna vrijednost dovršene platforme opravdava cijenu od **500 EUR godišnje po župi**.
- Cijena od 500 EUR znači 41,67 EUR mjesečno i uključuje razvoj, sigurnost, backup, održavanje, standardnu podršku i mogućnost javne web-stranice.
- **200 EUR nije dobra trajna puna cijena** ako uključuje osobnu podršku, migracije, sigurnosnu odgovornost i web-stranicu.
- Iznos od 200 EUR može biti vremenski ograničena pilot-cijena ili solidarna cijena za male župe.
- Preporučena javna cijena: **500 EUR godišnje plus PDV, ako je primjenjiv**.
- Preporučena cijena za prve referentne župe: 200–300 EUR u prvoj godini, uz unaprijed poznatu kasniju cijenu.
- Jednokratno početno postavljanje treba naplaćivati odvojeno.

## Zašto 500 EUR nije objektivno previsoko

Godišnja cijena od 500 EUR iznosi:

- 41,67 EUR mjesečno;
- približno 1,37 EUR dnevno;
- manje od cijene jednog do dva sata stručnog administrativnog ili informatičkog rada mjesečno.

Platforma ne pruža samo hosting. U cijenu ulaze:

- razvoj i kontinuirane nadogradnje;
- sigurnosne zakrpe i nadzor;
- tenant izolacija i upravljanje pristupima;
- backup i povrat podataka;
- audit zapisi;
- održavanje pastoralnih i financijskih procesa;
- podrška korisnicima;
- javna web-stranica nije dio e-Župe i ugovara se kao zaseban proizvod;
- odgovornost za dugoročno funkcioniranje sustava.

Mogući problem nije objektivna vrijednost nego početna percepcija: nova platforma još nema reference, a manje župe mogu imati malen slobodan budžet. Taj se problem rješava ulaznom cijenom, demonstracijom uštede vremena i preporukama, a ne trajnim podcjenjivanjem proizvoda.

## Predloženi komercijalni model

### Standardna ponuda

| Stavka | Predloženi iznos |
|---|---:|
| Godišnja licenca za jednu župu | 500 EUR |
| Početno postavljanje i edukacija | 200–300 EUR jednokratno |
| Standardna javna web-stranica | nije uključena; zaseban proizvod |
| Standardna poddomena | uključena |
| Vlastita domena | po stvarnom trošku |
| Uredna standardna migracija | uključena do ugovorenog opsega |
| Neuredni podaci i ručno čišćenje | posebna ponuda |
| Poseban dizajn ili razvoj | posebna ponuda |
| SMS i druge usluge po potrošnji | prema stvarnoj potrošnji |

### Model za lakši ulazak na tržište

Za prvih 10–15 župa:

- prva godina: 200–300 EUR;
- druga godina: 350–400 EUR;
- nakon toga puna cijena: 500 EUR;
- prijelaz cijene mora biti naveden prije početka korištenja;
- zauzvrat se traži strukturirani feedback i, ako su zadovoljni, preporuka ili referenca.

Druga mogućnost je trajni popust za jasno definirane male župe, ali kriterij treba biti objektivan, primjerice broj aktivnih kućanstava ili prihodovni razred. Popuste ne treba dogovarati proizvoljno za svaku župu.

## Što mora biti uključeno u godišnju licencu

- korištenje svih standardnih pastoralnih modula;
- standardni broj korisnika bez naplate po korisniku;
- sigurnosne i funkcionalne nadogradnje;
- redovne sigurnosne kopije;
- povrat podataka prema definiranoj politici;
- standardna podrška e-poštom unutar radnog vremena;
- monitoring dostupnosti;
- javna stranica na standardnom predlošku;
- objava rasporeda misa, obavijesti i kalendara;
- standardni izvještaji i izvoz podataka;
- izlaz korisnika i predaja njegovih podataka u dogovorenom formatu.

## Što ne smije biti neograničeno uključeno

- ručni unos sadržaja umjesto korisnika;
- neograničena telefonska podrška;
- čišćenje proizvoljno neurednih Excel datoteka;
- izrada potpuno posebnog dizajna web-stranice;
- razvoj funkcionalnosti samo za jednu župu;
- video-arhiva i vrlo velika količina fotografija;
- SMS poruke i drugi vanjski servisi s troškom po korištenju;
- hitne intervencije izvan ugovorenog vremena;
- terenski dolasci i dodatne edukacije.

## Ciljana arhitektura s malim troškom

Odvojena baza za svaku župu ne znači odvojeni virtualni server za svaku župu.

Preporučeni model:

1. zajednički stateless Django aplikacijski sloj;
2. središnja control-plane baza;
3. PostgreSQL cluster koji sadrži zasebnu bazu i zasebne ovlasti za svaku župu;
4. zajednički worker i cache uz obvezni tenant namespace;
5. privatna, šifrirana pohrana osjetljivih dokumenata;
6. odvojeni neizmjenjivi backup kod drugog pružatelja;
7. statički generirane javne web-stranice iza CDN-a;
8. dodavanje novog infrastrukturnog stampa kada se dosegne unaprijed određeni kapacitet.

Time se zadržava sigurnosna izolacija, ali se aplikacijski serveri, baza, monitoring i operativni rad dijele između više župa.

## Okvirni infrastrukturni troškovi

Iznosi su sigurnosne radne procjene, ne ponude dobavljača. Uključuju rezervu za promjenu cijena i ne treba ih računati prema najjeftinijem oglašenom VPS-u.

### Pilot: 1–10 župa

| Skupina troška | Mjesečno |
|---|---:|
| Aplikacija i background worker | 15–35 EUR |
| PostgreSQL i dodatni disk | 20–40 EUR |
| Privatni dokumenti i backup | 5–20 EUR |
| Monitoring, e-pošta i pomoćni servisi | 5–20 EUR |
| Ukupno | 45–115 EUR |

Godišnje: približno 540–1.380 EUR. Kod samo pet župa trošak po župi je visok jer se osnovna infrastruktura dijeli na malen broj korisnika. Pilot zato nije razdoblje visoke zarade.

### Početni rast: približno 25 župa

| Skupina troška | Mjesečno |
|---|---:|
| Dva aplikacijska procesa ili čvora | 30–70 EUR |
| PostgreSQL, replika i diskovi | 40–90 EUR |
| Storage i odvojeni backup | 10–30 EUR |
| Monitoring, e-pošta i pomoćni servisi | 15–35 EUR |
| Ukupno | 95–225 EUR |

Godišnje: približno 1.140–2.700 EUR, odnosno približno 46–108 EUR infrastrukture po župi.

### Stabilan rast: približno 50 župa

| Skupina troška | Mjesečno |
|---|---:|
| Aplikacijski čvorovi i workeri | 50–110 EUR |
| PostgreSQL cluster i replika | 70–150 EUR |
| Storage, backup i arhiva | 20–50 EUR |
| Monitoring, e-pošta, DNS i pomoćni servisi | 20–50 EUR |
| Ukupno | 160–360 EUR |

Godišnje: približno 1.920–4.320 EUR, odnosno približno 38–86 EUR infrastrukture po župi.

### Razvijena usluga: približno 100 župa

| Skupina troška | Mjesečno |
|---|---:|
| Više aplikacijskih čvorova i workera | 90–180 EUR |
| Više PostgreSQL stampova i replika | 140–300 EUR |
| Storage, backup i arhiva | 35–90 EUR |
| Monitoring, e-pošta, sigurnost i pomoćni servisi | 35–100 EUR |
| Ukupno | 300–670 EUR |

Godišnje: približno 3.600–8.040 EUR, odnosno približno 36–80 EUR infrastrukture po župi.

## Prihod prema broju župa

Iznosi su prije PDV-a, poreza, troška rada, prodaje i podrške.

| Župa | 200 EUR/god. | 350 EUR/god. | 500 EUR/god. |
|---:|---:|---:|---:|
| 10 | 2.000 EUR | 3.500 EUR | 5.000 EUR |
| 25 | 5.000 EUR | 8.750 EUR | 12.500 EUR |
| 50 | 10.000 EUR | 17.500 EUR | 25.000 EUR |
| 100 | 20.000 EUR | 35.000 EUR | 50.000 EUR |
| 250 | 50.000 EUR | 87.500 EUR | 125.000 EUR |

## Zašto je podrška ključni trošak

Ako infrastruktura pri stabilnom rastu košta 50–80 EUR po župi godišnje, kod licence od 200 EUR ostaje samo 120–150 EUR prije:

- korisničke podrške;
- razvoja i testiranja;
- administracije i prodaje;
- sigurnosnih provjera;
- poreza i davanja;
- neplaniranih incidenata;
- vremena potrebnog za obnovu licenci i naplatu.

Jedan ili dva dulja poziva, migracija podataka ili incident mogu potrošiti cijelu godišnju razliku. Zato 200 EUR može funkcionirati samo ako je onboarding standardiziran, korisnici su gotovo samostalni, podrška je ograničena i postoji dovoljan broj župa.

Kod cijene od 500 EUR ostaje prostor za kvalitetnu podršku i sigurnost bez potrebe da se štedi na backupu, nadzoru ili testiranju.

## Kada je 200 EUR održivo

Iznos od 200 EUR može biti održiv u jednom od sljedećih slučajeva:

- vremenski ograničena pilot-cijena;
- solidarna cijena koju djelomično pokrivaju veće župe ili biskupija;
- samooslužni osnovni paket bez migracije i individualne podrške;
- velik broj župa ugovoren centralno preko biskupije;
- javna web-stranica, dodatna podrška i posebne usluge naplaćuju se odvojeno.

Kao trajna all-inclusive cijena za mali broj pojedinačno ugovorenih župa, 200 EUR predstavlja velik poslovni rizik.

## Preporučena odluka

1. Ne spuštati trajnu punu vrijednost proizvoda na 200 EUR.
2. Postaviti službenu godišnju cijenu na 500 EUR.
3. Prvim župama ponuditi jasno označenu pilot-cijenu od 200–300 EUR.
4. Omogućiti plaćanje godišnje licence u dvije rate ako je župi lakše, bez pretvaranja licence u mjesečnu pretplatu.
5. Za male župe definirati transparentan solidarni popust.
6. Za biskupije ponuditi količinsku cijenu jer centralni ugovor smanjuje prodajni i administrativni trošak.
7. Svakih šest mjeseci računati stvarni trošak po župi: infrastruktura, storage, backup, podrška, incidenti i razvoj.

## Signali da cijenu treba korigirati

Cijenu ili uvjete treba mijenjati ako se dogodi jedno od sljedećeg:

- prosječna podrška prelazi dva sata godišnje po župi;
- infrastruktura prijeđe 15–20% godišnjeg prihoda;
- migracije redovito zahtijevaju ručni rad;
- župe pohranjuju velike količine fotografija, videa ili skenova;
- sigurnosni i regulatorni zahtjevi zahtijevaju dodatne komercijalne servise;
- velika većina zainteresiranih župa odustaje isključivo zbog cijene;
- platforma pouzdano štedi znatno više vremena nego što trenutna cijena izražava.

## Izvori za aktualne infrastrukturne procjene

- Hetzner službena objava promjena cijena: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Cloudflare R2 cijene: https://www.cloudflare.com/products/r2/
- Backblaze B2 cijene: https://www.backblaze.com/cloud-storage/pricing
