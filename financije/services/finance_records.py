"""
Pretvorba financijskih ORM redova ↔ legacy API dict.

`operational_store` učitava `CashbookEntry`, `ParishDebt` i `Invoice`
u camelCase liste koje UI i servisi (`cashbook`, `debts`, `invoices_page`)
još očekuju. Obrnuti smjer (`*_field_defaults_from_legacy`) puni ORM
polja pri spremanju. `payload` se namjerno prazni: tipizirani stupci
su izvor istine.

Ako se ovdje raspadne mapiranje iznosa ili smjera računa, ekran i baza
pokazuju različite brojke. Novac ide kroz `Decimal` prema bazi i `float`
prema starom UI ugovoru.
"""
from __future__ import annotations

import copy
from datetime import date
from decimal import Decimal, InvalidOperation

from financije.ledgers import LEDGER_CRKVENI, normalize_ledger
from financije.models import CashbookEntry, Invoice, ParishDebt


def _parse_iso_date(value) -> date | None:
    """Čita prvih deset znakova kao ISO datum; prazno ili smeće je None."""
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _decimal_amount(value) -> Decimal:
    """
    Pretvara UI iznos u Decimal za ORM.

    Neispravan unos postaje 0, ne iznimka — spremanje ne smije pasti
    zbog praznog polja dok forma još šalje stringove.
    """
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _iso_or_empty(value: date | None) -> str:
    """ISO datum za JSON/UI, prazan string ako datum nije zadan."""
    return value.isoformat() if value else ''


def cashbook_as_legacy_record(entry: CashbookEntry) -> dict:
    """
    Pretvara red blagajne u dict ekrana blagajne.

    `ledger` se normalizira da stari retci bez koda knjige padnu u
    crkvenu knjigu prema kategoriji. `id` je `public_identifier`, ne PK.

    Args:
        entry: ORM red `CashbookEntry`.

    Returns:
        CamelCase dict za `data['cashbook']`.
    """
    return {
        'id': entry.public_identifier,
        'date': _iso_or_empty(entry.entry_date),
        'type': entry.entry_type or 'ulaz',
        'category': entry.category or '',
        'ledger': normalize_ledger(entry.ledger, entry.category),
        'description': entry.description or '',
        'amount': float(entry.amount or 0),
        'paymentMethod': entry.payment_method or '',
        'reportCode': entry.report_code or '',
    }


def cashbook_field_defaults_from_legacy(record: dict) -> dict:
    """
    Polja ORM-a iz jednog UI retka blagajne, za `update` / `save_new`.

    Zadana knjiga je crkvena ako UI nije poslao `ledger`.

    Args:
        record: CamelCase dict s ekrana ili API-ja.

    Returns:
        Kwargs usklađeni s `CashbookEntry` (uključujući prazan `payload`).
    """
    return {
        'entry_date': _parse_iso_date(record.get('date')),
        'entry_type': str(record.get('type') or 'ulaz'),
        'category': str(record.get('category') or ''),
        'ledger': normalize_ledger(
            record.get('ledger') or LEDGER_CRKVENI,
            record.get('category'),
        ),
        'description': str(record.get('description') or ''),
        'amount': _decimal_amount(record.get('amount')),
        'payment_method': str(record.get('paymentMethod') or ''),
        'report_code': str(record.get('reportCode') or ''),
        'payload': {},
    }


def parish_debt_as_legacy_record(debt: ParishDebt) -> dict:
    """
    Pretvara `ParishDebt` u dict liste `parishDebts`.

    `paid` je legacy ime za `is_paid`. Koristi `collect_payables` /
    dio `collect_receivables` za ručne stavke.

    Args:
        debt: ORM red ručnog duga.

    Returns:
        CamelCase dict.
    """
    return {
        'id': debt.public_identifier,
        'direction': debt.direction or 'payable',
        'year': debt.year,
        'category': debt.category or '',
        'label': debt.label or '',
        'amount': float(debt.amount or 0),
        'paid': bool(debt.is_paid),
        'contact': debt.contact or '',
        'dueDate': _iso_or_empty(debt.due_date),
        'notes': debt.notes or '',
    }


def parish_debt_field_defaults_from_legacy(record: dict) -> dict:
    """
    Polja ORM-a iz UI retka ručnog duga.

    Godina koja nije cijeli broj postaje None, ne 0.

    Args:
        record: CamelCase dict.

    Returns:
        Kwargs za `ParishDebt`.
    """
    year_raw = record.get('year')
    try:
        year_value = int(year_raw) if year_raw not in (None, '') else None
    except (TypeError, ValueError):
        year_value = None
    return {
        'direction': str(record.get('direction') or 'payable'),
        'year': year_value,
        'category': str(record.get('category') or ''),
        'label': str(record.get('label') or ''),
        'amount': _decimal_amount(record.get('amount')),
        'is_paid': bool(record.get('paid')),
        'contact': str(record.get('contact') or ''),
        'due_date': _parse_iso_date(record.get('dueDate')),
        'notes': str(record.get('notes') or ''),
        'payload': {},
    }


def invoice_as_legacy_record(invoice: Invoice) -> dict:
    """
    Pretvara `Invoice` u dict ekrana računa.

    Jedan ORM stupac `payer_name` puni i `supplierName` i `payerName`
    jer ulazni i izlazni UI koriste različite ključeve za istu stranu.
    Ako status nije spremljen, izvodi se iz smjera i omjera plaćeno/total.

    Args:
        invoice: ORM red računa.

    Returns:
        CamelCase dict za `data['invoices']`.
    """
    linked_source = copy.deepcopy(invoice.linked_source or {})
    direction = invoice.direction or (
        'outgoing' if linked_source else 'incoming'
    )
    total = float(invoice.total or 0)
    paid_amount = float(invoice.paid_amount or 0)
    status = invoice.status or (
        'placen'
        if paid_amount >= total and total > 0
        else ('primljen' if direction == 'incoming' else 'izdan')
    )
    return {
        'id': invoice.public_identifier,
        'number': invoice.number or '',
        'issueDate': _iso_or_empty(invoice.issue_date),
        'dueDate': _iso_or_empty(invoice.due_date),
        # Jedan ORM stupac čuva naziv druge strane za oba smjera računa.
        # Zadržavamo oba legacy ključa dok izlazni i ulazni UI imaju različite
        # nazive za isti podatak.
        'supplierName': invoice.payer_name or '',
        'payerName': invoice.payer_name or '',
        'payerAddress': invoice.payer_address or '',
        'payerOib': invoice.payer_oib or '',
        'category': invoice.category or '',
        'description': invoice.description or '',
        'amount': float(invoice.amount or 0),
        'vatRate': float(invoice.vat_rate or 0),
        'total': total,
        'status': status,
        'paidAmount': paid_amount,
        'paidAt': _iso_or_empty(invoice.paid_at),
        'linkedSource': linked_source,
        'notes': invoice.notes or '',
        'direction': direction,
    }


def invoice_field_defaults_from_legacy(record: dict) -> dict:
    """
    Polja ORM-a iz UI retka računa.

    `supplierName` ima prednost pred `payerName` pri punjenju `payer_name`.
    `linkedSource` koji nije dict odbacuje se (prazan dict), da JSONField
    ne dobije listu ili string.

    Args:
        record: CamelCase dict.

    Returns:
        Kwargs za `Invoice`.
    """
    linked_source = record.get('linkedSource')
    if not isinstance(linked_source, dict):
        linked_source = {}
    return {
        'number': str(record.get('number') or ''),
        'issue_date': _parse_iso_date(record.get('issueDate')),
        'due_date': _parse_iso_date(record.get('dueDate')),
        'payer_name': str(
            record.get('supplierName') or record.get('payerName') or ''
        ),
        'payer_address': str(record.get('payerAddress') or ''),
        'payer_oib': str(record.get('payerOib') or ''),
        'category': str(record.get('category') or ''),
        'description': str(record.get('description') or ''),
        'amount': _decimal_amount(record.get('amount')),
        'vat_rate': _decimal_amount(record.get('vatRate')),
        'total': _decimal_amount(record.get('total')),
        'status': str(record.get('status') or ''),
        'paid_amount': _decimal_amount(record.get('paidAmount')),
        'paid_at': _parse_iso_date(record.get('paidAt')),
        'linked_source': copy.deepcopy(linked_source),
        'notes': str(record.get('notes') or ''),
        'direction': str(record.get('direction') or ''),
        'payload': {},
    }
