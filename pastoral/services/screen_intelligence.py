"""Operativni sažetak postojećih ekrana, izveden isključivo iz unesenih podataka."""
from __future__ import annotations

from datetime import date, timedelta

from pastoral.services.dates import parse_iso_date


SKIP_PAGES = frozenset({'dashboard', 'operativno-srediste', 'dekanat'})


def _metric(label: str, value, hint: str = '', tone: str = 'neutral') -> dict:
    return {'label': label, 'value': value, 'hint': hint, 'tone': tone}


def _action(title: str, body: str, page: str, query: str = '', tone: str = 'info') -> dict:
    return {'title': title, 'body': body, 'page': page, 'query': query, 'tone': tone}


def _base(title: str, purpose: str, icon: str, metrics: list[dict], action: dict, *, checklist=None) -> dict:
    return {
        'eyebrow': 'Operativni fokus ovog ekrana',
        'title': title,
        'purpose': purpose,
        'icon': icon,
        'metrics': metrics[:4],
        'action': action,
        'checklist': checklist or [],
    }


def _family_cockpit(data: dict) -> dict:
    today = date.today()
    year = today.year
    families = data.get('families', [])
    missing_contact = [row for row in families if not row.get('phone') and not row.get('email')]
    never_visited = [row for row in families if not row.get('lastVisit')]
    visits_due = []
    unpaid = []
    for family in families:
        last = parse_iso_date(family.get('lastVisit'))
        notes = (family.get('pastoralNotes') or '').lower()
        if ('posjetiti' in notes or 'pričest' in notes) and (not last or (today - last).days > 28):
            visits_due.append(family)
        contribution = next((row for row in family.get('contributions', []) if row.get('year') == year), None)
        if contribution and not contribution.get('luknoPaid'):
            unpaid.append(family)
    focus = (visits_due or never_visited or missing_contact or families or [{}])[0]
    focus_id = focus.get('id', '')
    return _base(
        'Karton mora pokazati odnos, ne samo adresu i uplatu',
        'Najprije provjerite pastoralnu skrb i kvalitetu kontakta; financijski podatak je samo jedan dio kartona obitelji.',
        '⌂',
        [
            _metric('Obitelji', len(families), 'ukupno u evidenciji'),
            _metric('Pastoralni posjet', len(visits_due), 'traži procjenu', 'warning' if visits_due else 'success'),
            _metric('Bez kontakta', len(missing_contact), 'telefon ili e-mail', 'warning' if missing_contact else 'success'),
            _metric(f'Lukno {year}', len(unpaid), 'nije označeno plaćenim', 'neutral'),
        ],
        _action(
            f"Otvorite karton obitelji {focus.get('surname', '')}" if focus else 'Otvorite karton obitelji',
            'Provjerite bilješku, zadnji posjet, kontaktne preferencije i sljedeću pastoralnu radnju.',
            'obitelji', f'family={focus_id}' if focus_id else '',
            'warning' if visits_due else 'info',
        ),
    )


def _streets_cockpit(data: dict) -> dict:
    streets = data.get('streets', [])
    families = data.get('families', [])
    assigned = [row for row in families if row.get('streetId')]
    unassigned = [row for row in families if not row.get('streetId')]
    zones = {row.get('zone') for row in streets if row.get('zone')}
    empty_streets = [street for street in streets if not any(f.get('streetId') == street.get('id') for f in families)]
    focus = (unassigned or empty_streets or [{}])[0]
    if unassigned:
        action = _action(
            f"Povežite obitelj {focus.get('surname', '')} s ulicom",
            'Bez teritorijalne veze nema pouzdane rute blagoslova, posjeta ni pastoralne pokrivenosti.',
            'obitelji', f"family={focus.get('id', '')}", 'warning',
        )
    else:
        action = _action('Pregledajte pokrivenost po kvartovima', 'Usporedite broj obitelji i zadnje posjete po teritoriju.', 'posjete')
    return _base(
        'Teritorij župe treba biti spreman za obilazak',
        'Ulica nije samo adresa: ona određuje pastoralnu zonu, rutu posjeta i odgovornu osobu.',
        '⌖',
        [
            _metric('Ulice', len(streets), 'u teritoriju župe'),
            _metric('Kvartovi / zone', len(zones), 'pastoralne cjeline'),
            _metric('Povezane obitelji', len(assigned), 'spremno za rutu', 'success'),
            _metric('Bez ulice', len(unassigned), 'treba povezati', 'warning' if unassigned else 'success'),
        ],
        action,
    )


def _visits_cockpit(data: dict) -> dict:
    today = date.today()
    visits = data.get('visits', [])
    open_rows = [row for row in visits if not row.get('done')]
    overdue = [row for row in open_rows if parse_iso_date(row.get('scheduled')) and parse_iso_date(row.get('scheduled')) < today]
    no_report = [row for row in visits if row.get('done') and not (row.get('report') or '').strip()]
    communion = [row for row in open_rows if row.get('type') == 'kucna-pricest']
    focus = (overdue or communion or open_rows or [{}])[0]
    return _base(
        'Posjet završava tek kada je poznat sljedeći korak',
        'Rasporedite posjete po hitnosti i teritoriju, a nakon posjeta zabilježite samo nužan pastoralni ishod.',
        '◎',
        [
            _metric('Otvoreno', len(open_rows), 'čeka posjet'),
            _metric('Prekoračeno', len(overdue), 'termin je prošao', 'danger' if overdue else 'success'),
            _metric('Kućna pričest', len(communion), 'redovita skrb'),
            _metric('Bez izvještaja', len(no_report), 'obavljen posjet', 'warning' if no_report else 'success'),
        ],
        _action(
            focus.get('purpose') or f"Posjet: {focus.get('person', 'odredite prioritet')}",
            'Potvrdite termin, svećenika, adresu i što treba učiniti nakon posjeta.',
            'posjete', f"visit={focus.get('id', '')}" if focus.get('id') else '',
            'danger' if overdue else 'info',
        ),
    )


SACRAMENT_META = {
    'krsenja': ('baptisms', 'baptismDate', 'childName', 'Krštenje', '✦'),
    'vjencanja': ('weddings', 'weddingDate', 'couple', 'Vjenčanje', '♥'),
    'pogrebi': ('funerals', 'funeralDate', 'deceased', 'Pogreb', '✝'),
    'pomazanje': ('anointing', 'scheduled', 'person', 'Pomazanje', '🕯'),
}


def _record_ready(page: str, row: dict) -> bool:
    if page == 'krsenja':
        return bool(row.get('baptismDate') and row.get('celebrant') and row.get('godparentCertReceived'))
    if page == 'vjencanja':
        return bool(row.get('weddingDate') and row.get('celebrant') and row.get('documentsOk'))
    if page == 'pogrebi':
        return bool(row.get('funeralDate') and row.get('celebrant') and row.get('familyContact'))
    if page == 'pomazanje':
        return bool(row.get('scheduled') and row.get('priest') and row.get('contact'))
    return False


def _sacrament_cockpit(data: dict, page: str) -> dict:
    key, date_key, name_key, label, icon = SACRAMENT_META[page]
    today = date.today()
    rows = data.get(key, [])
    ready = [row for row in rows if _record_ready(page, row)]
    missing = [row for row in rows if not _record_ready(page, row)]
    overdue = [
        row for row in rows
        if parse_iso_date(row.get(date_key)) and parse_iso_date(row.get(date_key)) < today
        and row.get('status') not in {'obavljeno', 'upisano', 'dovršeno'} and not row.get('done')
    ]
    unregistered = []
    if page == 'krsenja':
        unregistered = [row for row in rows if parse_iso_date(row.get(date_key)) and parse_iso_date(row.get(date_key)) < today and not row.get('registryNo')]
    focus = (overdue or missing or unregistered or rows or [{}])[0]
    query = f"q={focus.get(name_key, '')}" if focus.get(name_key) else ''
    checklist = [
        {'label': 'Osoba i kontakt', 'done': bool(focus.get(name_key) and (focus.get('parents') or focus.get('contact') or focus.get('familyContact')))},
        {'label': 'Datum i mjesto', 'done': bool(focus.get(date_key))},
        {'label': 'Dokumenti', 'done': _record_ready(page, focus)},
        {'label': 'Celebrant / svećenik', 'done': bool(focus.get('celebrant') or focus.get('priest'))},
    ] if focus else []
    return _base(
        f'{label} se vodi kao predmet, ne samo kao red u tablici',
        'Prije slavlja moraju biti vidljivi dokumenti, odgovorna osoba i termin; nakon slavlja upis i izdavanje potvrde.',
        icon,
        [
            _metric('Predmeti', len(rows), 'u evidenciji'),
            _metric('Spremno', len(ready), 'osnovni podaci potpuni', 'success'),
            _metric('Nedostaje', len(missing), 'dokument, termin ili celebrant', 'warning' if missing else 'success'),
            _metric('Iza roka', len(overdue), 'nije zaključeno', 'danger' if overdue else 'success'),
        ],
        _action(
            f"Provjerite: {focus.get(name_key, label)}",
            'Otvorite predmet, dopunite checklistu i nakon slavlja evidentirajte matični korak.',
            page, query, 'danger' if overdue else 'warning' if missing else 'info',
        ),
        checklist=checklist,
    )


def _formation_cockpit(data: dict, page: str) -> dict:
    today_year = date.today().year
    if page == 'krizma':
        groups = data.get('confirmations', [])
        group = next((row for row in groups if row.get('year') == today_year), groups[0] if groups else {})
        candidates = group.get('candidates', [])
        missing = [row for row in candidates if not row.get('baptized') or not row.get('sponsor')]
        ready = [row for row in candidates if row.get('status') == 'potvrđen']
        label, icon = 'Krizmena priprava', '✠'
        missing_label = 'bez krštenja ili kuma'
    else:
        groups = data.get('firstCommunion', [])
        group = next((row for row in groups if row.get('year') == today_year), groups[0] if groups else {})
        candidates = group.get('candidates', [])
        missing = [row for row in candidates if not row.get('parents') or not row.get('school')]
        ready = [row for row in candidates if row.get('paid')]
        label, icon = 'Prvopričesnička priprava', '✞'
        missing_label = 'bez roditelja ili škole'
    focus = (missing or candidates or [{}])[0]
    ceremony = group.get('ceremonyDate') or ''
    return _base(
        f'{label}: napredak skupine mora biti vidljiv prije slavlja',
        'Važniji su nedostajući podaci, priprava i komunikacija s roditeljima nego sam ukupan broj kandidata.',
        icon,
        [
            _metric('Kandidati', len(candidates), f"godina {group.get('year', today_year)}"),
            _metric('Provjereno', len(ready), 'trenutni status'),
            _metric('Nepotpuno', len(missing), missing_label, 'warning' if missing else 'success'),
            _metric('Datum slavlja', ceremony[5:] if ceremony else '—', 'termin skupine', 'success' if ceremony else 'warning'),
        ],
        _action(
            f"Provjerite kandidata {focus.get('name', '')}" if focus.get('name') else 'Odredite sljedeći korak skupine',
            'Dopunite podatke, zabilježite pripravu i pripremite ciljanu obavijest roditeljima.',
            page, f"q={focus.get('name', '')}" if focus.get('name') else '',
            'warning' if missing else 'info',
        ),
    )


def _liturgy_cockpit(data: dict, page: str) -> dict:
    today = date.today().isoformat()
    intentions = data.get('intentions', [])
    schedule = data.get('massSchedule', [])
    if page == 'nakane':
        unpaid = [row for row in intentions if not row.get('paid') and float(row.get('stipend') or 0) > 0]
        past = [row for row in intentions if (row.get('date') or '9999') < today]
        no_time = [row for row in intentions if not row.get('massTime')]
        focus = (unpaid or no_time or intentions or [{}])[0]
        return _base(
            'Nakana mora imati termin, trag priloga i potvrdu izvršenja',
            'Sustav treba spriječiti dvostruki termin i jasno odvojiti naručitelja, nakanu, prilog i izvršenje.',
            '☩',
            [_metric('Ukupno', len(intentions), 'u evidenciji'), _metric('Danas', sum(1 for row in intentions if row.get('date') == today), 'za izvršenje'), _metric('Neplaćeno', len(unpaid), 'evidencija priloga', 'warning' if unpaid else 'success'), _metric('Prošli termini', len(past), 'provjeriti izvršenje', 'warning' if past else 'success')],
            _action(f"Provjerite nakanu: {focus.get('intentionFor', '')}", 'Potvrdite termin, uplatu i je li nakana izvršena.', 'nakane', f"date={focus.get('date', '')}" if focus.get('date') else '', 'warning' if unpaid else 'info'),
        )
    missing_priest = [row for row in schedule if not row.get('celebrant')]
    return _base(
        'Raspored mise mora biti izvediv, ne samo objavljen',
        'Svaki termin treba celebranta, lokaciju i vezu s nakanama; iznimka ne smije tiho pregaziti stalni raspored.',
        '◉',
        [_metric('Stalni termini', len(schedule), 'tjedni raspored'), _metric('Bez celebranta', len(missing_priest), 'treba dodijeliti', 'warning' if missing_priest else 'success'), _metric('Iznimke', len(data.get('massExceptions', [])), 'posebni datumi'), _metric('Nakane', len(intentions), 'povezane s terminima')],
        _action('Dodijelite celebranta' if missing_priest else 'Provjerite sljedeću iznimku rasporeda', 'Prije objave provjerite preklapanja, lokaciju i nakane.', 'mise', tone='warning' if missing_priest else 'info'),
    )


def _office_cockpit(data: dict, page: str) -> dict:
    today = date.today()
    if page == 'kalendar':
        tasks = data.get('tasks', [])
        open_rows = [row for row in tasks if not row.get('done')]
        overdue = [row for row in open_rows if parse_iso_date(row.get('due')) and parse_iso_date(row.get('due')) < today]
        ownerless = [row for row in open_rows if not row.get('owner')]
        next_week = [row for row in data.get('events', []) if parse_iso_date(row.get('date')) and today <= parse_iso_date(row.get('date')) <= today + timedelta(days=7)]
        focus = (overdue or ownerless or open_rows or [{}])[0]
        return _base('Svaka obveza mora imati vlasnika i rok', 'Kalendar objedinjuje liturgiju, događaje, zadatke i resurse; unos bez odgovorne osobe nije operativan.', '▦', [_metric('Otvoreni zadaci', len(open_rows), 'u radnom redu'), _metric('Prekoračeno', len(overdue), 'rok je prošao', 'danger' if overdue else 'success'), _metric('Bez vlasnika', len(ownerless), 'nije dodijeljeno', 'warning' if ownerless else 'success'), _metric('Događaji 7 dana', len(next_week), 'prostori i ljudi')], _action(f"Dodijelite: {focus.get('title', 'sljedeći zadatak')}", 'Odredite vlasnika, rok i što znači dovršeno.', 'kalendar', tone='danger' if overdue else 'warning' if ownerless else 'info'))
    if page == 'podsjetnici':
        from pastoral.services.reminders import collect_reminders
        reminders = collect_reminders(data)
        high = [row for row in reminders if row.get('priority') == 'visoka']
        focus = (high or reminders or [{}])[0]
        href = focus.get('href', '')
        target, _, query = href.partition('?')
        return _base('Podsjetnik treba završiti odlukom ili radnjom', 'Inbox mora razlikovati hitno, važno i informativno te voditi izravno na predmet koji se rješava.', '!', [_metric('Ukupno', len(reminders), 'aktivni podsjetnici'), _metric('Visoki prioritet', len(high), 'riješiti prvo', 'danger' if high else 'success'), _metric('Financije', sum(1 for row in reminders if row.get('category') in {'racun','dug','lukno','nakana'}), 'novčane obveze'), _metric('Pastoralno', sum(1 for row in reminders if row.get('category') in {'posjet','sakrament','pogreb'}), 'osobe i sakramenti')], _action(focus.get('title', 'Otvorite prvi podsjetnik'), focus.get('sub', 'Odredite sljedeći korak.'), target or 'podsjetnici', query, 'danger' if high else 'info'))
    if page == 'javne-prijave':
        rows = data.get('publicSubmissions', [])
        new = [row for row in rows if row.get('status') == 'nova']
        old = [row for row in new if parse_iso_date(row.get('submittedAt')) and (today - parse_iso_date(row.get('submittedAt'))).days > 2]
        return _base('Javna prijava je ulaz u predmet, ne gotov zapis', 'Prije uvoza provjerite identitet, duplikat, privolu, nadležnost župe i nedostajuće dokumente.', '▤', [_metric('Nove', len(new), 'čeka trijažu', 'warning' if new else 'success'), _metric('Starije od 2 dana', len(old), 'prekoračen odgovor', 'danger' if old else 'success'), _metric('Ukupno', len(rows), 'zaprimljene prijave'), _metric('Obrađeno', len(rows)-len(new), 'preuzeto u evidenciju')], _action('Obradite najstariju prijavu' if new else 'Provjerite javne obrasce', 'Prvo provjerite postoji li osoba ili predmet već u župi.', 'javne-prijave', 'status=nova' if new else '', 'danger' if old else 'warning' if new else 'info'))
    if page == 'vijeca':
        pastoral = data.get('pastoralCouncil', {})
        economic = data.get('economicCouncil', {})
        members = (pastoral.get('members') or []) + (economic.get('members') or [])
        unconfirmed = [row for row in members if not row.get('confirmed')]
        dates = [parse_iso_date(pastoral.get('nextMeeting')), parse_iso_date(economic.get('nextReview'))]
        overdue = [value for value in dates if value and value < today]
        return _base('Vijeće mora proizvoditi odluke, vlasnike i rokove', 'Popis članova nije dovoljan: sastanak treba dnevni red, zapisnik, odluke i praćenje izvršenja.', '◉', [_metric('Članovi', len(members), 'ŽPV i ŽEV'), _metric('Nepotvrđeni', len(unconfirmed), 'mandat ili potvrda', 'warning' if unconfirmed else 'success'), _metric('Prošli termini', len(overdue), 'treba ažurirati', 'danger' if overdue else 'success'), _metric('Aktivna vijeća', 2, 'pastoralno i ekonomsko')], _action('Evidentirajte odluke posljednjeg sastanka', 'Svakoj odluci dodijelite osobu i rok; dokument ostaje uz sjednicu.', 'kalendar', tone='danger' if overdue else 'info'))
    return {}


def _records_cockpit(data: dict, page: str) -> dict:
    today = date.today()
    books = data.get('registryBooks', [])
    if page == 'maticne-knjige':
        stale = [row for row in books if not parse_iso_date(row.get('lastEntry')) or (today - parse_iso_date(row.get('lastEntry'))).days > 365]
        incomplete = [row for row in books if not row.get('lastNo') or not row.get('custodian') or not row.get('location')]
        focus = (stale or incomplete or books or [{}])[0]
        return _base('Matica se usklađuje i anotira; ne briše se kao običan zapis', 'Za svaku knjigu moraju biti poznati skrbnik, lokacija, zadnji broj i datum posljednjeg usklađenja.', '▥', [_metric('Knjige', len(books), 'u župnom arhivu'), _metric('Za usklađenje', len(stale), 'starije od godine', 'warning' if stale else 'success'), _metric('Nepotpuni metapodaci', len(incomplete), 'lokacija, skrbnik ili broj', 'warning' if incomplete else 'success'), _metric('Fizička lokacija', sum(1 for row in books if row.get('location')), 'evidentirana')], _action(f"Provjerite: {focus.get('title', 'matična knjiga')}", 'Usporedite zadnji fizički upis i digitalnu evidenciju te zapišite tko je provjerio.', 'maticne-knjige', f"book={focus.get('id', '')}" if focus.get('id') else '', 'warning' if stale or incomplete else 'info'))
    bindings = data.get('docBindings', [])
    if page == 'dokumenti':
        return _base('Serijski dokument vrijedi tek kada je izvor podataka provjeren', 'Prije ispisa provjerite mapiranje stupaca, predložak, broj redova i svrhu izdavanja.', '▤', [_metric('Povezivanja', len(bindings), 'spremljene CSV veze'), _metric('Matice', len(books), 'dostupni izvori'), _metric('Predlošci', 'više', 'prema katalogu'), _metric('Audit ispisa', 'nije', 'treba implementirati', 'warning')], _action('Provjerite spremljena mapiranja', 'Zastarjelo mapiranje može proizvesti pogrešan dokument za cijelu skupinu.', 'dokumenti', tone='warning' if bindings else 'info'))
    return _base('Isprava mora imati izvor, svrhu i trag izdavanja', 'Podaci se preuzimaju iz kartona ili matice; ručni unos treba biti iznimka i jasno označen.', '▤', [_metric('Matične knjige', len(books), 'izvori podataka'), _metric('Spremljena mapiranja', len(bindings), 'serijski dokumenti'), _metric('Trag izdavanja', 'nije', 'potreban backend', 'warning'), _metric('Predlošci', 'katalog', 'kontrolirane verzije')], _action('Odaberite osobu ili zapis matice', 'Prije ispisa provjerite identitet, svrhu i ovlaštenje primatelja.', page, tone='info'))


def _finance_cockpit(data: dict, page: str) -> dict:
    today = date.today()
    invoices = data.get('invoices', [])
    debts = data.get('parishDebts', [])
    cashbook = data.get('cashbook', [])
    unpaid_invoices = [row for row in invoices if row.get('direction') != 'outgoing' and row.get('status') not in {'placen', 'storno'}]
    overdue_invoices = [row for row in unpaid_invoices if parse_iso_date(row.get('dueDate')) and parse_iso_date(row.get('dueDate')) < today]
    unpaid_debts = [row for row in debts if not row.get('paid')]
    incomplete_cash = [row for row in cashbook if not row.get('category') or not row.get('reportCode') or not row.get('paymentMethod')]
    if page == 'racuni':
        return _base('Račun treba vlasnika, rok, dokument i vezu s isplatom', 'Prioritet je spriječiti zakašnjenje i dvostruko plaćanje te sačuvati izvorni dokument.', '▤', [_metric('Otvoreni računi', len(unpaid_invoices), 'čeka plaćanje'), _metric('Dospjeli', len(overdue_invoices), 'rok je prošao', 'danger' if overdue_invoices else 'success'), _metric('Ukupno', len(invoices), 'u evidenciji'), _metric('Dokument', 'nije vezan', 'treba sigurnu pohranu', 'warning')], _action('Platite ili obrazložite dospjeli račun' if overdue_invoices else 'Provjerite sljedeći rok plaćanja', 'Nakon plaćanja povežite račun s blagajničkim ili bankovnim unosom.', 'racuni', tone='danger' if overdue_invoices else 'info'))
    if page == 'dugovanja':
        return _base('Obveza mora završiti uplatom ili dokumentiranim oslobođenjem', 'Odvojite dug župe, potraživanje i pastoralnu napomenu; financijski status ne smije biti pastoralna ocjena osobe.', '€', [_metric('Otvorene obveze', len(unpaid_debts), 'nije plaćeno'), _metric('Dospjele', sum(1 for row in unpaid_debts if parse_iso_date(row.get('dueDate')) and parse_iso_date(row.get('dueDate')) < today), 'rok je prošao', 'danger'), _metric('Računi', len(unpaid_invoices), 'dobavljači'), _metric('Lukno', 'odvojeno', 'u kartonu obitelji')], _action('Provjerite najstariju otvorenu obvezu', 'Potvrdite iznos, rok, odgovornu osobu i izvor dokumenta.', 'dugovanja', tone='warning'))
    if page == 'blagajna':
        return _base('Blagajnički dnevnik mora biti potpun prije zaključivanja', 'Svaki unos treba kategoriju, način plaćanja, izvještajnu oznaku i dokaz.', '€', [_metric('Unosi', len(cashbook), 'u evidenciji'), _metric('Nepotpuno', len(incomplete_cash), 'nedostaje klasifikacija', 'warning' if incomplete_cash else 'success'), _metric('Plavi dnevnik', sum(1 for row in cashbook if row.get('ledger') == 'plavi'), 'redovni promet'), _metric('Crveni dnevnik', sum(1 for row in cashbook if row.get('ledger') == 'crveni'), 'namjenski promet')], _action('Dopunite nepotpuni unos' if incomplete_cash else 'Uskladite dnevnik sa stanjem', 'Prije zaključavanja usporedite gotovinu, žiro račun i dokumente.', 'blagajna', tone='warning' if incomplete_cash else 'info'))
    return _base('Izvješće je rezultat provjerenih evidencija', 'Prije predaje treba uskladiti blagajnu, račune, obveze i odluke ŽEV-a.', '▥', [_metric('Otvoreni računi', len(unpaid_invoices), 'utječu na izvještaj'), _metric('Otvorene obveze', len(unpaid_debts), 'treba objasniti'), _metric('Nepotpuna blagajna', len(incomplete_cash), 'blokira zaključivanje', 'warning' if incomplete_cash else 'success'), _metric('ŽEV pregled', data.get('economicCouncil', {}).get('nextReview', '—'), 'sljedeći termin')], _action('Pokrenite kontrolu prije predaje', 'Nijedan izvještaj ne smije biti označen spremnim ako pomoćne evidencije nisu usklađene.', 'financijska-izvjestaja', tone='warning' if incomplete_cash else 'info'))


def build_screen_cockpit(data: dict, page: str, settings_data: dict | None = None) -> dict | None:
    if not page or page in SKIP_PAGES:
        return None
    if page == 'obitelji':
        return _family_cockpit(data)
    if page == 'ulice':
        return _streets_cockpit(data)
    if page == 'posjete':
        return _visits_cockpit(data)
    if page in SACRAMENT_META:
        return _sacrament_cockpit(data, page)
    if page in {'krizma', 'prva-pricest'}:
        return _formation_cockpit(data, page)
    if page in {'nakane', 'mise'}:
        return _liturgy_cockpit(data, page)
    if page in {'kalendar', 'podsjetnici', 'javne-prijave', 'vijeca'}:
        return _office_cockpit(data, page)
    if page in {'maticne-knjige', 'formulari', 'potvrde', 'dokumenti'}:
        return _records_cockpit(data, page)
    if page in {'dugovanja', 'racuni', 'blagajna', 'financijska-izvjestaja'}:
        return _finance_cockpit(data, page)
    if page == 'zupni-listic':
        issues = data.get('zupniListicIssues', [])
        announcements = data.get('announcements', [])
        return _base('Listić se priprema iz provjerenih izvora i zaključava prije objave', 'Nakane, raspored i obavijesti trebaju se povući iz sustava; ručno kopiranje povećava rizik pogreške.', '▤', [_metric('Spremljena izdanja', len(issues), 'povijest verzija'), _metric('Obavijesti', len(announcements), 'dostupno za uvrštavanje'), _metric('Nakane', len(data.get('intentions', [])), 'izvor tablice'), _metric('Odobrenje', 'nije formalno', 'treba workflow', 'warning')], _action('Pripremite sljedeće izdanje iz živih podataka', 'Prije objave provjerite nakane, raspored, liturgijski dan i odobrenje župnika.', 'zupni-listic'))
    if page == 'postavke':
        settings_data = settings_data or {}
        missing = [key for key in ('name', 'city', 'diocese', 'pastor', 'phone', 'email') if not settings_data.get(key)]
        controls = data.get('complianceControls', [])
        due = [row for row in controls if row.get('status') not in {'completed', 'ready'}]
        return _base('Postavke su sigurnosna i organizacijska granica župe', 'Ovdje trebaju biti identitet župe, korisnički pristupi, rokovi čuvanja, sigurnosne kopije i integracije.', '⌁', [_metric('Nedostajuća polja', len(missing), 'osnovni identitet', 'warning' if missing else 'success'), _metric('Sigurnosne kontrole', len(due), 'otvoreno u radnom redu', 'warning' if due else 'success'), _metric('Više župa', 'spremno za model', 'ovlasti još nisu konačne'), _metric('Backup test', 'u radnom redu', 'dokaz obnove')], _action('Pregledajte pristupe i sigurnosne kontrole', 'Posebno provjerite osobe koje više ne rade u župi i uređaje s pristupom podacima.', 'operativno-srediste', 'view=compliance', 'warning'))
    return None
