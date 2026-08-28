# API action handleri

Ovaj paket sadrži dijeljene pomoćne funkcije za `/api/action/`.
`pastoral.services.api_actions` ostaje kompatibilna fasada i središnji registar
naziva akcija; domenske mutacije žive u Django appovima.

## Tok zahtjeva

1. `parish_action_api` provjeri JSON zahtjev.
2. `dispatch_action` pronađe handler prema postojećem nazivu akcije.
3. Handler primi `parish_data` i `action_payload`.
4. Handler vrati rječnik s ključem `ok`.
5. Dispatcher sprema podatke samo za mutacijske akcije.

## Moduli

- `shared.py` — identifikatori, datumi, normalizacija i pronalaženje zapisa.

Domenske akcije:

- `pregled.api_actions` — analitika
- `zupa_vjernici.api_actions` — obitelji, ulice, posjete
- `liturgija.api_actions` — nakane, mise, listić
- `sakramenti.api_actions` — sakramenti i priprava
- `financije.api_actions` — dugovanja, blagajna, računi
- `isprave.api_actions` — potvrde, matica
- `ured.api_actions` — zadaci, podsjetnici, prijave, korisnici, poruke

## Dodavanje nove akcije

1. Odaberi domenski Django app.
2. Koristi potpis `handler(parish_data: dict, action_payload: dict) -> dict`.
3. Registriraj u `ACTION_HANDLERS` tog app-a (pastoral fasada ih spaja).
4. Ako akcija ne smije spremati podatke, dodaj naziv u
   `READ_ONLY_ACTION_NAMES` u pastoral fasadi.
5. Dodaj ciljani regresijski test.
