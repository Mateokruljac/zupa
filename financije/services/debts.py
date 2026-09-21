"""
Agregacija dugovanja za ekran i pregled — logika iz debts-engine.js.

Ne čuva vlastitu tablicu „svih dugova”. Sastavlja retke iz obiteljskog
lukna, misnih nakana, stipenda sakramenata, skupina pričesti/krizme i
ručnih `parishDebts`. Zato `mark_debt_paid` mora znati `source.type`.

`receivable` = tko duguje župi; `payable` = što župa duguje.
Pozivatelji: `debts_page_context`, `finance_reports_context`,
`pregled.services.analytics`, template tag `cat_meta`.
"""
from __future__ import annotations

from datetime import date
from typing import Any

RECEIVABLE_CATEGORIES = [
    {'id': 'lukno', 'label': 'Lukno', 'color': '#5c2e3a'},
    {'id': 'nakane', 'label': 'Misne nakane', 'color': '#3d5a80'},
    {'id': 'krsenje', 'label': 'Krštenja', 'color': '#2d6a4f'},
    {'id': 'prva-pricest', 'label': 'Prva pričest', 'color': '#7c5c2e'},
    {'id': 'krizma', 'label': 'Krizma', 'color': '#6b4c9a'},
    {'id': 'vjencanje', 'label': 'Vjenčanja', 'color': '#9b2c5c'},
    {'id': 'pogreb', 'label': 'Pogrebi', 'color': '#4a4a4a'},
    {'id': 'ostalo', 'label': 'Ostalo', 'color': '#6d6760'},
]

PAYABLE_CATEGORIES = [
    {'id': 'režije', 'label': 'Režije', 'color': '#3d5a80'},
    {'id': 'dobavljaci', 'label': 'Dobavljači', 'color': '#b45309'},
    {'id': 'dz', 'label': 'Biskupija / DŽ', 'color': '#5c2e3a'},
    {'id': 'ostalo', 'label': 'Ostalo', 'color': '#6d6760'},
]


def _year_from_iso(iso: str | None) -> int:
    """Godina iz ISO datuma; neispravan ili kratak string pada na tekuću godinu."""
    if not iso or len(iso) < 4:
        return date.today().year
    try:
        return int(iso[:4])
    except ValueError:
        return date.today().year


def cat_meta(cat_id: str, direction: str) -> dict:
    """
    Boja i hrvatski naziv kategorije duga za predložak i pretragu.

    `payable` koristi `PAYABLE_CATEGORIES`, inače potraživanja.
    Nepoznat `cat_id` vraća sam id kao labelu, sivu boju — UI ne puca.

    Args:
        cat_id: Kod kategorije (`lukno`, `režije`, …).
        direction: `payable` ili `receivable`.

    Returns:
        Dict s `id`, `label`, `color`.
    """
    cats = PAYABLE_CATEGORIES if direction == 'payable' else RECEIVABLE_CATEGORIES
    for c in cats:
        if c['id'] == cat_id:
            return c
    return {'id': cat_id, 'label': cat_id, 'color': '#6d6760'}


def _push(rows: list, item: dict | None) -> None:
    """Dodaje stavku samo ako postoji i iznos je strogo veći od nule."""
    if not item or float(item.get('amount') or 0) <= 0:
        return
    rows.append(item)


def collect_receivables(data: dict, *, only_unpaid: bool = True) -> list[dict]:
    """
    Sastavlja potraživanja prema župi iz više izvora u parish dictu.

    Izvori: lukno po godini obitelji (iznos iz retka ili `luknoDefaultAmount`),
    stipend nakane, vjenčanja/pogrebi/krštenja, skupna pristojba pričesti i
    krizme, te `parishDebts` sa smjerom `receivable`. Stavka bez iznosa se
    ne prikazuje. `only_unpaid=False` na ekranu dugovanja uključuje i
    plaćene retke radi filtera statusa.

    Svaki redak ima `source` za `mark_debt_paid` i opcionalni `link_page`
    za skok u modul. Identifikatori su složeni (`lukno_{obitelj}_{godina}`),
    nisu ORM PK.

    Args:
        data: Legacy parish dict (`families`, `intentions`, sakramenti, …).
        only_unpaid: True = samo neplaćeno (pregled, brojači).

    Returns:
        Sortirani retci (`sort_debt_rows`).
    """
    rows: list[dict] = []
    def_lukno = data.get('luknoDefaultAmount', 150)

    for fam in data.get('families', []):
        for c in fam.get('contributions', []):
            amt = float(c.get('luknoAmount') or def_lukno)
            paid = bool(c.get('luknoPaid'))
            if only_unpaid and paid:
                continue
            if not only_unpaid and not paid and amt <= 0:
                continue
            _push(rows, {
                'id': f"lukno_{fam['id']}_{c['year']}",
                'direction': 'receivable',
                'category': 'lukno',
                'year': int(c['year']),
                'amount': amt,
                'label': f"Lukno {c['year']} — {fam.get('surname', '')}",
                'sublabel': fam.get('address', ''),
                'contact': fam.get('phone') or fam.get('surname', ''),
                'dueDate': c.get('luknoPaidAt') or '',
                'paid': paid,
                'familyId': fam.get('id'),
                'link_page': 'obitelji',
                'link_query': f"family={fam.get('id', '')}",
                'source': {'type': 'contribution', 'familyId': fam.get('id'), 'year': c['year']},
            })

    for n in data.get('intentions', []):
        amt = float(n.get('stipend') or 0)
        if amt <= 0:
            continue
        paid = bool(n.get('paid'))
        if only_unpaid and paid:
            continue
        _push(rows, {
            'id': f"nakana_{n['id']}",
            'direction': 'receivable',
            'category': 'nakane',
            'year': _year_from_iso(n.get('date')),
            'amount': amt,
            'label': n.get('intentionFor') or 'Nakana',
            'sublabel': f"{n.get('date', '')} · misa {n.get('massTime', '')}",
            'contact': '',
            'dueDate': n.get('date', ''),
            'paid': paid,
            'link_page': 'nakane',
            'link_query': f"date={n.get('date', '')}",
            'source': {'type': 'intention', 'id': n['id']},
        })

    def sacrament(list_key, category, label_fn, date_fn):
        """Isti obrazac stipenda za vjenčanje, sprovod i krštenje u parish dictu."""
        for r in data.get(list_key, []):
            amt = float(r.get('stipend') or 0)
            if amt <= 0:
                continue
            paid = bool(r.get('stipendPaid'))
            if only_unpaid and paid:
                continue
            dt = date_fn(r)
            _push(rows, {
                'id': f"{category}_{r['id']}",
                'direction': 'receivable',
                'category': category,
                'year': _year_from_iso(dt),
                'amount': amt,
                'label': label_fn(r),
                'sublabel': dt or '',
                'contact': r.get('parents') or r.get('familyContact') or r.get('couple', ''),
                'dueDate': dt,
                'paid': paid,
                'link_page': None,
                'link_query': '',
                'source': {'type': list_key, 'id': r['id']},
            })

    sacrament('weddings', 'vjencanje', lambda w: w.get('couple', ''), lambda w: w.get('weddingDate', ''))
    sacrament('funerals', 'pogreb', lambda f: f.get('deceased', ''), lambda f: f.get('funeralDate', ''))
    sacrament('baptisms', 'krsenje', lambda b: b.get('childName', ''), lambda b: b.get('baptismDate', ''))

    for g in data.get('firstCommunion', []):
        amt = float(g.get('groupFee') or 0)
        if amt <= 0:
            continue
        paid = bool(g.get('groupFeePaid'))
        if only_unpaid and paid:
            continue
        _push(rows, {
            'id': f"pricest_{g['id']}",
            'direction': 'receivable',
            'category': 'prva-pricest',
            'year': int(g.get('year') or _year_from_iso(g.get('ceremonyDate'))),
            'amount': amt,
            'label': g.get('groupName') or 'Skupina prve pričesti',
            'sublabel': g.get('ceremonyDate', ''),
            'contact': '',
            'dueDate': g.get('ceremonyDate', ''),
            'paid': paid,
            'link_page': 'prva-pricest',
            'link_query': '',
            'source': {'type': 'firstCommunion', 'id': g['id']},
        })

    for g in data.get('confirmations', []):
        amt = float(g.get('groupFee') or 0)
        if amt <= 0:
            continue
        paid = bool(g.get('groupFeePaid'))
        if only_unpaid and paid:
            continue
        _push(rows, {
            'id': f"krizma_{g['id']}",
            'direction': 'receivable',
            'category': 'krizma',
            'year': int(g.get('year') or _year_from_iso(g.get('ceremonyDate'))),
            'amount': amt,
            'label': f"Krizma {g.get('year', '')}",
            'sublabel': f"{len(g.get('candidates') or [])} kandidata",
            'contact': '',
            'dueDate': g.get('ceremonyDate', ''),
            'paid': paid,
            'link_page': 'krizma',
            'link_query': f"year={g.get('year', '')}",
            'source': {'type': 'confirmations', 'id': g['id']},
        })

    for d in data.get('parishDebts', []):
        if (d.get('direction') or 'receivable') != 'receivable':
            continue
        amt = float(d.get('amount') or 0)
        if amt <= 0:
            continue
        paid = bool(d.get('paid'))
        if only_unpaid and paid:
            continue
        _push(rows, {
            'id': f"misc_{d['id']}",
            'direction': 'receivable',
            'category': d.get('category') or 'ostalo',
            'year': int(d.get('year') or _year_from_iso(d.get('dueDate'))),
            'amount': amt,
            'label': d.get('label') or 'Stavka',
            'sublabel': d.get('notes', ''),
            'contact': d.get('contact', ''),
            'dueDate': d.get('dueDate', ''),
            'paid': paid,
            'link_page': None,
            'link_query': '',
            'source': {'type': 'parishDebts', 'id': d['id']},
        })

    return sort_debt_rows(rows)


def collect_payables(data: dict, *, only_unpaid: bool = True) -> list[dict]:
    """
    Obveze župe — samo ručni `parishDebts` sa smjerom `payable`.

    Režije i DŽ nisu izvedeni iz računa: ulazni račun živi na drugom
    ekranu. Zadani smjer praznog polja je `payable` (stari unos).

    Args:
        data: Parish dict s `parishDebts`.
        only_unpaid: True = samo neplaćeno.

    Returns:
        Sortirani retci obveza.
    """
    rows: list[dict] = []
    for d in data.get('parishDebts', []):
        if (d.get('direction') or 'payable') != 'payable':
            continue
        amt = float(d.get('amount') or 0)
        if amt <= 0:
            continue
        paid = bool(d.get('paid'))
        if only_unpaid and paid:
            continue
        _push(rows, {
            'id': f"pay_{d['id']}",
            'direction': 'payable',
            'category': d.get('category') or 'ostalo',
            'year': int(d.get('year') or _year_from_iso(d.get('dueDate'))),
            'amount': amt,
            'label': d.get('label') or 'Obveza',
            'sublabel': d.get('notes', ''),
            'contact': d.get('contact', ''),
            'dueDate': d.get('dueDate', ''),
            'paid': paid,
            'link_page': None,
            'link_query': '',
            'source': {'type': 'parishDebts', 'id': d['id']},
        })
    return sort_debt_rows(rows)


def sort_debt_rows(rows: list[dict]) -> list[dict]:
    """
    Redoslijed tablice: neplaćeno prije plaćenog, zatim novija godina,
    zatim kasniji datum dospijeća.

    Više uzastopnih `sorted` (stabilno) da prioritet statusa pobijedi
    godinu. Ne sortira na mjestu originalne liste ako je već nova.
    """
    rows = sorted(rows, key=lambda r: r.get('dueDate') or '', reverse=True)
    rows = sorted(rows, key=lambda r: -int(r.get('year') or 0))
    rows = sorted(rows, key=lambda r: r.get('paid', False))
    return rows


def collect_debts(data: dict, *, direction: str | None = None, only_unpaid: bool = True) -> list[dict]:
    """
    Potraživanja, obveze ili oboje, za analitiku nadzorne ploče.

    Bez `direction` spaja oba smjera i ponovno sortira. `pregled` koristi
    ovu funkciju umjesto da zove dva collectora.

    Args:
        data: Parish dict.
        direction: `receivable`, `payable` ili None za oboje.
        only_unpaid: Proslijeđuje se collectorima.

    Returns:
        Lista redaka duga.
    """
    receivable = collect_receivables(data, only_unpaid=only_unpaid)
    payable = collect_payables(data, only_unpaid=only_unpaid)
    if direction == 'receivable':
        return receivable
    if direction == 'payable':
        return payable
    return sort_debt_rows(receivable + payable)


def years_from_debts(rows: list[dict]) -> list[int]:
    """
    Godine za filter na ekranu dugovanja.

    Uvijek uključuje tekuću i prošlu godinu, čak i ako nema stavki,
    da se lukno nove godine može odabrati prije prvog unosa.
    """
    years = {r['year'] for r in rows if r.get('year')}
    cur = date.today().year
    years.add(cur)
    years.add(cur - 1)
    return sorted(years, reverse=True)


def filter_debts(rows: list[dict], filters: dict) -> list[dict]:
    """
    Filtrira već sastavljene retke (kategorija, godina, status, tekst).

    Status `unpaid` je zadani prikaz. Pretraga gleda naziv, kontakt,
    podnaslov i hrvatski naziv kategorije (`cat_meta`), ne sirovi id.

    Args:
        rows: Izlaz `collect_*`.
        filters: `category`, `year`, `status`, `q`; `all` isključuje filter.

    Returns:
        Nova lista; `rows` se ne mutira osim što se kopira na početku.
    """
    out = list(rows)
    cat = filters.get('category') or 'all'
    if cat != 'all':
        out = [r for r in out if r.get('category') == cat]
    year = filters.get('year') or 'all'
    if year != 'all':
        try:
            y = int(year)
            out = [r for r in out if r.get('year') == y]
        except ValueError:
            pass
    status = filters.get('status') or 'unpaid'
    if status == 'unpaid':
        out = [r for r in out if not r.get('paid')]
    elif status == 'paid':
        out = [r for r in out if r.get('paid')]
    q = (filters.get('q') or '').strip().lower()
    if q:
        def matches(r):
            meta = cat_meta(r.get('category', ''), r.get('direction', 'receivable'))
            hay = ' '.join([
                r.get('label', ''),
                r.get('contact', ''),
                r.get('sublabel', ''),
                meta.get('label', ''),
            ]).lower()
            return q in hay
        out = [r for r in out if matches(r)]
    return out


def summarize(rows: list[dict], direction: str) -> dict:
    """
    Sažetak trenutno prikazanih redaka (nakon filtera).

    Zbroj i broj neplaćenih idu u kartice; `by_category` puni sve
    poznate kategorije tog smjera nulama da predložak ima stabilan red.
    Plaćeni retci ulaze samo u `paid_count`.

    Args:
        rows: Filtrirana lista.
        direction: Bira katalog kategorija.

    Returns:
        `total_unpaid`, `unpaid_count`, `paid_count`, `by_category`.
    """
    unpaid = [r for r in rows if not r.get('paid')]
    total_unpaid = sum(float(r.get('amount') or 0) for r in unpaid)
    cats = PAYABLE_CATEGORIES if direction == 'payable' else RECEIVABLE_CATEGORIES
    by_category: dict[str, dict] = {c['id']: {'count': 0, 'sum': 0.0} for c in cats}
    for r in unpaid:
        cid = r.get('category') or 'ostalo'
        if cid not in by_category:
            by_category[cid] = {'count': 0, 'sum': 0.0}
        by_category[cid]['count'] += 1
        by_category[cid]['sum'] += float(r.get('amount') or 0)
    return {
        'total_unpaid': total_unpaid,
        'unpaid_count': len(unpaid),
        'paid_count': sum(1 for r in rows if r.get('paid')),
        'by_category': by_category,
    }


def debts_page_context(data: dict, request) -> dict:
    """
    Kontekst predloška stranice dugovanja.

    GET `view`: `prema-zupi` (potraživanja) ili `zupa-duguje` (obveze).
    Učitava sve retke smjera (`only_unpaid=False`) pa filtrira, da se
    plaćeno može uključiti izbornikom. Brojači na tabovima uvijek broje
    samo neplaćeno, neovisno o filteru tablice.

    Poziva je `financije.page_contexts`. Ne mijenja `data`.

    Args:
        data: Parish dict.
        request: GET `view`, `cat`, `year`, `status`, `q`.

    Returns:
        Ključevi `debts_*` za predložak.
    """
    view = request.GET.get('view', 'prema-zupi')
    if view not in ('prema-zupi', 'zupa-duguje'):
        view = 'prema-zupi'
    direction = 'payable' if view == 'zupa-duguje' else 'receivable'
    filters = {
        'category': request.GET.get('cat', 'all'),
        'year': request.GET.get('year', 'all'),
        'status': request.GET.get('status', 'unpaid'),
        'q': request.GET.get('q', ''),
    }
    all_rows = collect_payables(data, only_unpaid=False) if direction == 'payable' else collect_receivables(data, only_unpaid=False)
    filtered = filter_debts(all_rows, filters)
    summary = summarize(filtered, direction)
    cats = PAYABLE_CATEGORIES if direction == 'payable' else RECEIVABLE_CATEGORIES
    receivable_cnt = len(collect_receivables(data, only_unpaid=True))
    payable_cnt = len(collect_payables(data, only_unpaid=True))
    return {
        'debts_view': view,
        'debts_direction': direction,
        'debts_filters': filters,
        'debts_rows': filtered,
        'debts_all_rows': all_rows,
        'debts_years': years_from_debts(all_rows),
        'debts_summary': summary,
        'debts_categories': cats,
        'debts_receivable_count': receivable_cnt,
        'debts_payable_count': payable_cnt,
    }
