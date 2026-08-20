# Faza 2

Ovaj folder sadrži funkcionalnosti koje nisu dio trenutačnog MVP-a.
Odvojen je od `pastoral/` jezgre kako razvoj MVP-a ne bi bio opterećen
nedovršenim ili prerano uvedenim modulima.

## Odgođeni moduli

### Međužupna suradnja

- sigurna razmjena zahtjeva i potvrda između župa
- statusi predmeta, kontrolne liste i trag postupanja
- dekanatski imenik i zajednički pregled zahtjeva

Razlog odgode: modul ima stvarnu vrijednost tek kada platformu koristi dovoljan
broj povezanih župa i kada su dogovorena pravila razmjene osobnih podataka.

### Operativno središte

- zajednički radni red većeg župnog ureda
- uredska pošta, odobrenja i komunikacije
- održavanje, prostori, službe i kontrolni rokovi

Razlog odgode: funkcionalnost je namijenjena većim župama s više svećenika,
zaposlenika ili tajništvom. Za jednostavan MVP stvara nepotreban dodatni tok.

## Granica prema MVP-u

MVP zadržava samo mali registar modula kako bi stare poveznice mogle prikazati
obavijest „Planirano za fazu 2”. Implementacija, demo podaci, predlošci i
JavaScript nalaze se u ovom folderu i ne učitavaju se dok je
`PASTORAL_PRODUCT_PHASE=1`.

Website je zaseban proizvod i nalazi se u susjednom folderu
`website_project/`; nije dio ovog paketa faze 2.
