"""
JSON mutacije financija nad parish dictom (`/api/action/` ugovor).

Svaki handler prima `data` (camelCase parish JSON) i `action_payload`,
vraća `{'ok': True/False, ...}`. Ne zove ORM: spremanje radi dispatcher
(`operational_store`) nakon uspjeha. Isti `create_cashbook_entry` /
`upsert_invoice` / `mark_invoice_paid` koristi i HTML POST
(`financije.page_actions`).

Lukno i stipend sakramenta nisu ovdje — `mark_debt_paid` delegira na
`debt_mutations`. Ručni `parishDebts` jesu.

Kodovi grešaka (`label_required`, `not_found`) ostaju engleski jer ih
čita postojeći klijent, ne predložak.
"""
from __future__ import annotations

from datetime import date

from pastoral.services.api_action_handlers.shared import (
    generate_record_identifier,
    normalize_date_value,
)
from financije.ledgers import normalize_ledger
from pastoral.services.dates import today_iso
from financije.services.debt_mutations import mark_debt_paid as mark_debt_paid_record


def upsert_parish_debt(data: dict, action_payload: dict) -> dict:
    """
    Stvara ili ažurira ručnu stavku `parishDebts`.

    Ako payload ima `id`, traži postojeći red i `update` polja; inače
    umeće novi zapis na početak liste. Labela je obavezna. Plaćeno bez
    datuma dobiva `today_iso`. Zadani smjer je `payable`.

    Args:
        data: Parish dict; ključ `parishDebts` se stvara po potrebi.
        action_payload: Polja stavke; `id` označava izmjenu.

    Returns:
        `ok` i `item`, ili `ok: False` s `label_required` / `not_found`.

    Side effects:
        Mutira `data['parishDebts']`.
    """
    payload = {
        'direction': action_payload.get('direction') or 'payable',
        'label': (action_payload.get('label') or '').strip(),
        'category': action_payload.get('category') or 'ostalo',
        'year': int(action_payload.get('year') or date.today().year),
        'amount': float(action_payload.get('amount') or 0),
        'dueDate': normalize_date_value(
            action_payload.get('due_date') or action_payload.get('dueDate')
        ),
        'contact': (action_payload.get('contact') or '').strip(),
        'notes': (action_payload.get('notes') or '').strip(),
        'paid': bool(action_payload.get('paid')),
        'paidAt': normalize_date_value(
            action_payload.get('paid_at') or action_payload.get('paidAt')
        ),
    }
    if not payload['label']:
        return {'ok': False, 'error': 'label_required'}
    if payload['paid'] and not payload['paidAt']:
        payload['paidAt'] = today_iso()
    debt_id = action_payload.get('id')
    if debt_id:
        debt_record = next(
            (
                debt
                for debt in data.get('parishDebts', [])
                if debt.get('id') == debt_id
            ),
            None,
        )
        if not debt_record:
            return {'ok': False, 'error': 'not_found'}
        debt_record.update(payload)
        return {'ok': True, 'item': debt_record}
    item = {'id': generate_record_identifier('pd'), **payload}
    data.setdefault('parishDebts', []).insert(0, item)
    return {'ok': True, 'item': item}


def delete_parish_debt(data: dict, action_payload: dict) -> dict:
    """
    Uklanja ručni dug po `id`. Ne postojeći id je uspjeh (idempotentno).

    Ne dira lukno ni sakramente — samo listu `parishDebts`.

    Args:
        data: Parish dict.
        action_payload: Mora sadržavati `id`.

    Returns:
        Uvijek `{'ok': True}` nakon filtriranja liste.
    """
    debt_id = action_payload.get('id')
    data['parishDebts'] = [
        debt
        for debt in data.get('parishDebts', [])
        if debt.get('id') != debt_id
    ]
    return {'ok': True}


def mark_debt_paid(data: dict, action_payload: dict) -> dict:
    """
    API omotač oko `debt_mutations.mark_debt_paid`.

    `source` mora biti objekt koji je collector duga stavio u redak
    (`type` + identifikatori). Bez pronađenog zapisa vraća `not_found`.

    Args:
        data: Parish dict.
        action_payload: `source` dict.

    Returns:
        `{'ok': True}` ili `{'ok': False, 'error': 'not_found'}`.
    """
    source = action_payload.get('source') or {}
    if not mark_debt_paid_record(data, source):
        return {'ok': False, 'error': 'not_found'}
    return {'ok': True}


def upsert_invoice(data: dict, action_payload: dict) -> dict:
    """
    Stvara ili ažurira red u `invoices`.

    Polja se uzimaju iz `fields` ili cijelog payload-a. Novi račun
    dobiva `direction: incoming` ako klijent ne pošalje drugačije u
    `fields` nakon splata (`**fields` može prebrisati smjer).

    Args:
        data: Parish dict.
        action_payload: `id` za izmjenu; `fields` ili ravna polja.

    Returns:
        `ok` i `item`, ili `not_found`.
    """
    fields = dict(action_payload.get('fields') or action_payload)
    invoice_id = action_payload.get('id')
    if invoice_id:
        invoice_record = next(
            (
                invoice
                for invoice in data.get('invoices', [])
                if invoice.get('id') == invoice_id
            ),
            None,
        )
        if not invoice_record:
            return {'ok': False, 'error': 'not_found'}
        invoice_record.update(fields)
        return {'ok': True, 'item': invoice_record}
    item = {
        'id': generate_record_identifier('inv'),
        'direction': 'incoming',
        **fields,
    }
    data.setdefault('invoices', []).append(item)
    return {'ok': True, 'item': item}


def mark_invoice_paid(data: dict, action_payload: dict) -> dict:
    """
    Označava ulazni račun kao u cijelosti plaćen.

    `paidAmount` postaje `total` ili, ako total nema, `amount`.
    Status je `placen`. Ne knjiži automatski izlaz u blagajnu.

    Args:
        data: Parish dict.
        action_payload: `id` računa (`public_identifier` u UI-ju).

    Returns:
        `ok` i ažurirani `item`, ili `not_found`.
    """
    invoice_record = next(
        (
            invoice
            for invoice in data.get('invoices', [])
            if invoice.get('id') == action_payload.get('id')
        ),
        None,
    )
    if not invoice_record:
        return {'ok': False, 'error': 'not_found'}
    invoice_record['paidAmount'] = (
        invoice_record.get('total') or invoice_record.get('amount')
    )
    invoice_record['paidAt'] = today_iso()
    invoice_record['status'] = 'placen'
    return {'ok': True, 'item': invoice_record}


def create_cashbook_entry(data: dict, action_payload: dict) -> dict:
    """
    Dodaje red blagajne, plus opcionalne automatske pratitelje.

    `auto_entries` služi kad jedan unos treba drugi red (npr. par knjiga).
    Knjiga se normalizira kategorijom da misni prilog ne ostane u crkvenoj
    knjizi. Novi retci idu na početak liste (najnovije gore).

    Args:
        data: Parish dict.
        action_payload: `fields` glavnog retka; `auto_entries` lista dictova.

    Returns:
        `ok` i glavni `item` (pratitelji su u `data['cashbook']`, nisu u odgovoru).
    """
    fields = dict(action_payload.get('fields') or action_payload)
    fields['ledger'] = normalize_ledger(fields.get('ledger'), fields.get('category'))
    item = {'id': generate_record_identifier('cb'), **fields}
    data.setdefault('cashbook', []).insert(0, item)
    for extra_entry in action_payload.get('auto_entries') or []:
        extra = dict(extra_entry)
        extra['ledger'] = normalize_ledger(extra.get('ledger'), extra.get('category'))
        data['cashbook'].insert(
            0,
            {'id': generate_record_identifier('cb'), **extra},
        )
    return {'ok': True, 'item': item}
