"""POST akcije za dugovanja, blagajnu i račune."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from financije.ledgers import LEDGER_CRKVENI, LEDGER_GRADNJA, LEDGER_KOLEKTE, ledger_label, normalize_ledger
from financije.api_actions import (
    create_cashbook_entry,
    mark_invoice_paid,
    upsert_invoice,
)
from financije.forms import CashbookEntryForm, DonationForm, InvoiceForm, ParishDebtForm
from financije.services.debt_mutations import (
    add_parish_debt,
    mark_debt_paid,
    parse_debt_source,
)
from pastoral.services.api_actions import normalize_parish_data

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


def _save_debt_change(
    parish_data_service: ParishDataService,
    parish_data: dict,
    debt_source: dict | None,
) -> None:
    if debt_source and debt_source.get('type') == 'parishDebts':
        parish_data_service.save_financial(parish_data)
    else:
        # Potraživanja mogu pripadati obitelji, nakani ili sakramentu.
        parish_data_service.save(parish_data)


def handle_finance_action(
    request,
    page_slug: str,
    action_name: str,
    parish_data: dict,
    parish_data_service: ParishDataService,
) -> bool:
    if action_name == 'mark_debt_paid':
        debt_source = parse_debt_source(request.POST.get('source', ''))
        if mark_debt_paid(parish_data, debt_source):
            _save_debt_change(
                parish_data_service,
                parish_data,
                debt_source,
            )
            messages.success(request, 'Označeno kao plaćeno.')
        else:
            messages.error(request, 'Stavka nije pronađena.')
        return True

    if action_name == 'add_parish_debt' and page_slug == 'dugovanja':
        parish_debt_form = ParishDebtForm(request.POST)
        if parish_debt_form.is_valid():
            cleaned_data = parish_debt_form.cleaned_data
            add_parish_debt(
                parish_data,
                {**cleaned_data, 'direction': 'payable'},
            )
            parish_data_service.save_financial(parish_data)
            messages.success(request, 'Dugovanje dodano.')
        else:
            messages.error(request, 'Provjerite unos.')
        return True

    if action_name == 'add_cashbook_entry' and page_slug == 'blagajna':
        cashbook_entry_form = CashbookEntryForm(request.POST)
        if cashbook_entry_form.is_valid():
            cleaned_data = cashbook_entry_form.cleaned_data
            normalize_parish_data(parish_data)
            create_cashbook_entry(parish_data, {
                'fields': {
                    'date': cleaned_data['date'].isoformat(),
                    'type': cleaned_data['entry_type'],
                    'ledger': normalize_ledger(
                        cleaned_data['ledger'],
                        cleaned_data['category'],
                    ),
                    'category': cleaned_data['category'],
                    'description': cleaned_data['description'],
                    'amount': float(cleaned_data['amount']),
                    'paymentMethod': (
                        cleaned_data.get('payment_method') or 'gotovina'
                    ),
                },
            })
            parish_data_service.save_financial(parish_data)
            messages.success(request, 'Unos u blagajnu dodan.')
        else:
            messages.error(request, 'Provjerite unos.')
        return True

    if action_name == 'add_donation' and page_slug == 'blagajna':
        donation_form = DonationForm(request.POST)
        if donation_form.is_valid():
            cleaned_data = donation_form.cleaned_data
            purpose = cleaned_data['purpose']
            if purpose not in {LEDGER_CRKVENI, LEDGER_GRADNJA, LEDGER_KOLEKTE}:
                purpose = LEDGER_CRKVENI
            donor = (cleaned_data.get('donor') or '').strip()
            note = (cleaned_data.get('note') or '').strip()
            description_parts = ['Donacija']
            if donor:
                description_parts.append(donor)
            if note:
                description_parts.append(note)
            normalize_parish_data(parish_data)
            create_cashbook_entry(parish_data, {
                'fields': {
                    'date': cleaned_data['date'].isoformat(),
                    'type': 'ulaz',
                    'ledger': normalize_ledger(purpose, 'donacija'),
                    'category': 'donacija',
                    'description': ' — '.join(description_parts),
                    'amount': float(cleaned_data['amount']),
                    'paymentMethod': (
                        cleaned_data.get('payment_method') or 'gotovina'
                    ),
                },
            })
            parish_data_service.save_financial(parish_data)
            messages.success(
                request,
                f'Donacija upisana u {ledger_label(purpose)}.',
            )
        else:
            messages.error(request, 'Provjerite unos donacije.')
        return True

    if action_name == 'add_invoice' and page_slug == 'racuni':
        invoice_form = InvoiceForm(request.POST)
        if invoice_form.is_valid():
            cleaned_data = invoice_form.cleaned_data
            invoice_amount = float(cleaned_data['amount'])
            normalize_parish_data(parish_data)
            upsert_invoice(parish_data, {
                'fields': {
                    'number': cleaned_data['number'],
                    'issueDate': (
                        cleaned_data['issue_date'].isoformat()
                        if cleaned_data.get('issue_date')
                        else ''
                    ),
                    'dueDate': (
                        cleaned_data['due_date'].isoformat()
                        if cleaned_data.get('due_date')
                        else ''
                    ),
                    'supplierName': cleaned_data['supplier_name'],
                    'category': cleaned_data['category'],
                    'description': cleaned_data['description'],
                    'amount': invoice_amount,
                    'vatRate': 0,
                    'total': invoice_amount,
                    'status': 'primljen',
                    'paidAmount': 0,
                    'direction': 'incoming',
                },
            })
            parish_data_service.save_financial(parish_data)
            messages.success(request, 'Račun dodan.')
        else:
            messages.error(request, 'Provjerite unos računa.')
        return True

    if action_name == 'mark_invoice_paid' and page_slug == 'racuni':
        normalize_parish_data(parish_data)
        operation_result = mark_invoice_paid(
            parish_data,
            {'id': request.POST.get('invoice_id', '')},
        )
        if operation_result.get('ok'):
            parish_data_service.save_financial(parish_data)
            messages.success(request, 'Račun označen kao plaćen.')
        else:
            messages.error(request, 'Račun nije pronađen.')
        return True

    return False
