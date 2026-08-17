# API action handleri

Ovaj paket sadrži poslovne mutacije koje se pozivaju kroz `/api/action/`.
`pastoral.services.api_actions` ostaje kompatibilna fasada i središnji registar
naziva akcija.

## Tok zahtjeva

1. `parish_action_api` provjeri JSON zahtjev.
2. `dispatch_action` pronađe handler prema postojećem nazivu akcije.
3. Handler primi `parish_data` i `action_payload`.
4. Handler vrati rječnik s ključem `ok`.
5. Dispatcher sprema podatke samo za mutacijske akcije.

## Moduli

- `shared.py` — identifikatori, datumi, normalizacija i pronalaženje zapisa.
- `intentions.py` — misne nakane i njihov status plaćanja.
- `families.py` — obitelji, članovi, doprinosi, supružnici i rodbina.
- `streets.py` — ulice i kvartovi.

Preostale domene privremeno su u kompatibilnoj fasadi i izdvajaju se postupno.

## Dodavanje nove akcije

1. Odaberi postojeći domenski modul ili napravi novi modul jasnog naziva.
2. Koristi potpis `handler(parish_data: dict, action_payload: dict) -> dict`.
3. Koristi pune domenske nazive; nemoj uvoditi kratice ili jednoslovne varijable.
4. Sačuvaj postojeće camelCase ključeve spremljenih podataka i JSON odgovora.
5. Dodaj handler u `ACTION_HANDLERS` u `api_actions.py`.
6. Ako akcija ne smije spremati podatke, dodaj njezin naziv u
   `READ_ONLY_ACTION_NAMES`.
7. Ako prima postavke župe, dodaj naziv u `SETTINGS_AWARE_ACTION_NAMES` i koristi
   potpis s trećim parametrom `parish_settings`.
8. Dodaj ciljani regresijski test i pokreni cijeli Django testni paket.

Handler treba imati jednu odgovornost. Orkestracija ostaje u dispatcheru, a
domenska pravila i izmjene podataka ostaju u odgovarajućem modulu.
