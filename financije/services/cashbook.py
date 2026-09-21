"""
Blagajna župe — zbrojevi po službenim knjigama računa.

Čita legacy dict `cashbook` (camelCase retci koje `operational_store`
sastavlja iz `CashbookEntry`). Ne piše u bazu. Ekran blagajne i financijski
pregled ovise o istim zbrojevima; ako se ovdje promijeni pojam „ulaz”,
saldo župe na oba mjesta postaje netočan.

Ne pripada ovdje: dugovanja, računi, niti izbor knjige u smislu ORM-a
(`financije.ledgers` je izvor kodova knjiga).
"""
from __future__ import annotations

from datetime import date

from financije.ledgers import (
    LEDGER_CRKVENI,
    LEDGERS,
    PARISH_BALANCE_LEDGER,
    entry_ledger,
    normalize_ledger,
)


def _year_entries(data: dict, year: int) -> list[dict]:
    """
    Izdvaja retke blagajne čiji ISO datum počinje zadanom godinom.

    Filtrira se prefiksom stringa (`YYYY`), ne parsiranjem datuma, jer
    legacy retci čuvaju `date` kao tekst. Neispravan ili prazan datum
    ispadne iz godine.

    Args:
        data: Parish.data-kompatibilan dict s ključem `cashbook`.
        year: Kalendarska godina retka.

    Returns:
        Lista originalnih dictova, bez kopiranja.
    """
    prefix = str(year)
    return [
        entry
        for entry in data.get('cashbook', [])
        if (entry.get('date') or '').startswith(prefix)
    ]


def summarize_entries(rows: list[dict]) -> dict:
    """
    Zbraja ulaze i izlaze te raspoređuje iznose po kategoriji.

    `type == 'ulaz'` je primitak; sve ostalo tretira se kao izdatak.
    Prazna kategorija pada u `ostalo`. Koriste je stranica blagajne
    i `summarize_year`.

    Args:
        rows: Već odabrani retci jedne knjige i (obično) jedne godine.

    Returns:
        Dict s `in_sum`, `out_sum`, `balance` (ulaz minus izlaz),
        `by_category` (`in`/`out` po nazivu kategorije) i `count`.
    """
    in_sum = sum(float(entry.get('amount') or 0) for entry in rows if entry.get('type') == 'ulaz')
    out_sum = sum(float(entry.get('amount') or 0) for entry in rows if entry.get('type') != 'ulaz')
    by_category: dict[str, dict] = {}
    for entry in rows:
        category = entry.get('category') or 'ostalo'
        if category not in by_category:
            by_category[category] = {'in': 0.0, 'out': 0.0}
        amount = float(entry.get('amount') or 0)
        if entry.get('type') == 'ulaz':
            by_category[category]['in'] += amount
        else:
            by_category[category]['out'] += amount
    return {
        'in_sum': in_sum,
        'out_sum': out_sum,
        'balance': in_sum - out_sum,
        'by_category': by_category,
        'count': len(rows),
    }


def filter_ledger(rows: list[dict], ledger: str) -> list[dict]:
    """
    Ostavlja samo retke jedne službene knjige računa.

    Kod knjige normalizira `normalize_ledger` (aliasi i prazan ledger).
    Usporedba ide preko `entry_ledger`, ne sirovog polja, da stari retci
    bez `ledger` i dalje spadaju u crkvenu knjigu kad kategorija to kaže.

    Args:
        rows: Retci blagajne.
        ledger: Traženi kod knjige (npr. crkveni saldo).

    Returns:
        Podskup `rows` koji pripada toj knjizi.
    """
    wanted = normalize_ledger(ledger)
    return [entry for entry in rows if entry_ledger(entry) == wanted]


def summarize_year(
    data: dict,
    year: int,
    ledger: str = PARISH_BALANCE_LEDGER,
) -> dict:
    """
    Godišnji saldo jedne knjige — ulaz za financijski pregled.

    Default knjiga je župni saldo (`PARISH_BALANCE_LEDGER`), ne nužno
    knjiga koju korisnik gleda na ekranu blagajne.

    Args:
        data: Legacy parish dict s `cashbook`.
        year: Godina retka.
        ledger: Kod knjige; zadano knjiga župnog salda.

    Returns:
        Isti oblik kao `summarize_entries`.
    """
    return summarize_entries(filter_ledger(_year_entries(data, year), ledger))


def cashbook_page_context(data: dict, request) -> dict:
    """
    Kontekst predloška stranice blagajne.

    Čita `year` i `ledger` iz query stringa; neispravna godina pada na
    tekuću. Zadana knjiga na ekranu je crkvena (`LEDGER_CRKVENI`).
    Godine u izborniku grade se iz postojećih datuma, plus odabrana
    godina ako u podacima još nema redaka. `donate=1` otvara dijalog
    donacije bez zasebnog POST-a.

    Poziva je `financije.page_contexts`. Ne mijenja `data`.

    Args:
        data: Učitani parish dict (ključevi blagajne u camelCase).
        request: Django request s GET filterima.

    Returns:
        Ključevi `cashbook_*` za predložak, uključujući retke, sažetak
        i popis knjiga iz `LEDGERS`.
    """
    today = date.today()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year
    ledger = normalize_ledger(request.GET.get('ledger') or LEDGER_CRKVENI)

    year_rows = _year_entries(data, year)
    year_rows.sort(key=lambda entry: entry.get('date') or '', reverse=True)
    rows = filter_ledger(year_rows, ledger)

    years = sorted(
        {
            (entry.get('date') or '')[:4]
            for entry in data.get('cashbook', [])
            if entry.get('date')
        },
        reverse=True,
    )
    if str(year) not in years:
        years = [str(year)] + years

    current_book = next(book for book in LEDGERS if book['id'] == ledger)
    return {
        'cashbook_year': year,
        'cashbook_ledger': ledger,
        'cashbook_book': current_book,
        'cashbook_books': LEDGERS,
        'cashbook_rows': rows,
        'cashbook_summary': summarize_entries(rows),
        'cashbook_years': [int(year_value) for year_value in years[:6] if year_value.isdigit()],
        'open_donation_dialog': request.GET.get('donate') == '1',
    }
