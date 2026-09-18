# Pravila održavanja projekta e-Župa

## Arhitektura podataka

- Obvezujući dokument: `MDs/DB_ARCHITECTURE_PROPOSAL.md`.
- Zajedničke osnove SCD/FACT: `core/models.py` (`SCD1`, `SCD2`, `SCD2A`, `FCTA`, `FCTB`, `SCDD`, `SCDR`).
- Novi modeli nasljeđuju tu osnovu; ne duplicirati polja verzija ili hash.

## Opseg i sigurnost

- Sve izmjene moraju ostati unutar ovog repozitorija.
- Refaktoriranje mora sačuvati postojeće ponašanje, spremljene podatke, URL-ove i ključeve koje koriste predlošci ili JavaScript.
- Promjena podatkovnog ugovora radi se samo uz zasebnu migraciju i testove.

## Čitljivost koda

- Koristi pune, opisne engleske nazive varijabli, funkcija, metoda i parametara.
- Ne koristi kratice poput `svc`, `ctx`, `cfg`, `conf`, `fam`, `row`, `q`, `n`, `t` ili `s`.
- Naziv treba opisivati domenski pojam ili odgovornost, u stilu jasnih Laravel i Filament servisa, akcija i resursa.
- Funkcije trebaju imati jednu jasnu odgovornost. Velike handlere razdvoji u manje servisne funkcije.
- Handleri i view funkcije trebaju orkestrirati rad, a poslovni izračuni trebaju biti u servisima koji se mogu zasebno testirati.
- Hrvatski nazivi ostaju u korisničkom sučelju i domenskim vrijednostima. Python identifikatori ostaju dosljedno na engleskom.

## Provjera

- Za svaki refaktor pokreni ciljane testove i cijeli postojeći testni paket.
- Ne popravljaj nepovezane korisničke izmjene i ne prepisuj ih.
