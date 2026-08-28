# Odgođeni zahtjev: sigurnost javnih obrazaca

## Cilj

Prije produkcijskog otvaranja javnih obrazaca potrebno je provesti zaseban sigurnosni paket. Obrasci su javno dostupna ulazna točka u sustav i moraju biti zaštićeni bez narušavanja jednostavnosti korištenja za vjernike.

## Funkcionalni zahtjevi

- Uskladiti javne obrasce s light/dark načinom i vizualnim identitetom odabranog predloška župe.
- Dodati jasnu, obveznu privolu za obradu podataka s poveznicom na pravila privatnosti.
- Prikazati razumljive potvrde uspjeha i pogreške bez otkrivanja internih tehničkih detalja.
- Spriječiti višestruko slanje obrasca ponovnim klikom.
- Zadržati unesene nesenzitivne vrijednosti nakon validacijske pogreške.
- Osigurati potpuno responzivan i pristupačan prikaz tipkovnicom i čitačem ekrana.

## Zaštita od zloupotrebe

- Ograničiti broj zahtjeva po IP adresi, tenant župi i vrsti obrasca.
- Dodati nevidljivi honeypot i provjeru minimalnog realnog vremena ispunjavanja.
- Predvidjeti opcionalni CAPTCHA/Turnstile sloj koji se uključuje tek pri povišenom riziku.
- Ograničiti veličinu zahtjeva, duljinu svakog polja i dopuštene tipove eventualnih privitaka.
- Normalizirati i validirati sve vrijednosti isključivo na poslužitelju.
- CSRF zaštitu zadržati obveznom za pregledničke POST zahtjeve.
- Onemogućiti enumeration, detaljne poruke o internim korisnicima i nekontrolirane redirect URL-ove.

## Privatnost i podaci

- U aplikacijske, proxy i error logove ne zapisivati sadržaj osjetljivih polja.
- Audit mora sadržavati samo identifikator predaje, župu, vrstu obrasca, vrijeme, ishod i tehnički minimum potreban za istragu.
- Definirati rok čuvanja za svaku vrstu prijave te kontrolirano brisanje ili anonimizaciju.
- Ograničiti pregled prijava tenant članstvom i ulogama; zabraniti pristup između župa.
- Šifrirati prijenos TLS-om, a osjetljive podatke i sigurnosne kopije zaštititi prema projektu `SECURITY_PLAN.md`.
- U izvozu, e-mailu i obavijestima prikazivati samo podatke nužne primatelju.

## Testovi prihvata

- Tenant A ne može dohvatiti, pogoditi identifikator niti izvesti prijavu tenanta B.
- Rate limit, honeypot i vremenska provjera odbijaju automatizirane zahtjeve bez gubitka legitimnih predaja.
- Neispravan unos ne uzrokuje `500` niti otkriva stack trace ili interne identifikatore.
- Osjetljive vrijednosti nisu prisutne u audit i aplikacijskim logovima.
- CSRF, session i permission provjere ostaju aktivne u svim okruženjima osim jasno izoliranih testova.
- Light/dark, mobilni prikaz, tipkovnica i čitač ekrana prolaze provjeru za sve javne obrasce.
- Sigurnosni testovi pokrivaju uspješan unos, odbijanje, prekoračenje limita i pokušaj pristupa drugoj župi.

## Redoslijed implementacije

1. Poslužiteljska validacija, tenant ovlasti i redakcija logova.
2. Rate limiting, honeypot i zaštita od ponovnog slanja.
3. Privola, rokovi čuvanja i audit događaji.
4. Pristupačan light/dark dizajn i poruke stanja.
5. Automatizirani sigurnosni i end-to-end testovi.
6. Produkcijska konfiguracija proxyja, TLS-a, nadzora i alarma.

Ovaj dokument je zahtjev za sljedeću zasebnu implementacijsku cjelinu; trenutačno nije potvrda da su navedene kontrole već ugrađene.
