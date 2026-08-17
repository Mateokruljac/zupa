"""POST akcije za misne nakane, dugovanja, blagajnu i račune."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages

from pastoral.forms import (
    CashbookEntryForm,
    IntentionForm,
    InvoiceForm,
    ParishDebtForm,
)
from pastoral.services.api_actions import (
    create_cashbook_entry,
    mark_invoice_paid,
    normalize_parish_data,
    upsert_invoice,
)
from pastoral.services.mutations import (
    add_intention,
    add_parish_debt,
    delete_intention,
    mark_debt_paid,
    parse_debt_source,
    toggle_intention_paid,
)

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService


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
            parish_data_service.save(parish_data)
            messages.success(request, 'Označeno kao plaćeno.')
        else:
            messages.error(request, 'Stavka nije pronađena.')
        return True

    if action_name == 'add_intention' and page_slug == 'nakane':
        intention_form = IntentionForm(request.POST)
        if intention_form.is_valid():
            add_intention(parish_data, intention_form.cleaned_data)
            parish_data_service.save(parish_data)
            messages.success(request, 'Nakana dodana.')
        else:
            messages.error(request, 'Provjerite unos nakane.')
        return True

    if action_name == 'delete_intention' and page_slug == 'nakane':
        if delete_intention(
            parish_data,
            request.POST.get('intention_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Nakana obrisana.')
        return True

    if action_name == 'toggle_intention_paid' and page_slug == 'nakane':
        if toggle_intention_paid(
            parish_data,
            request.POST.get('intention_id', ''),
        ):
            parish_data_service.save(parish_data)
            messages.success(request, 'Status plaćanja ažuriran.')
        return True

    if action_name == 'add_parish_debt' and page_slug == 'dugovanja':
        parish_debt_form = ParishDebtForm(request.POST)
        if parish_debt_form.is_valid():
            cleaned_data = parish_debt_form.cleaned_data
            add_parish_debt(
                parish_data,
                {**cleaned_data, 'direction': 'payable'},
            )
            parish_data_service.save(parish_data)
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
                    'ledger': cleaned_data['ledger'],
                    'category': cleaned_data['category'],
                    'description': cleaned_data['description'],
                    'amount': float(cleaned_data['amount']),
                    'paymentMethod': (
                        cleaned_data.get('payment_method') or 'gotovina'
                    ),
                },
            })
            parish_data_service.save(parish_data)
            messages.success(request, 'Unos u blagajnu dodan.')
        else:
            messages.error(request, 'Provjerite unos.')
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
            parish_data_service.save(parish_data)
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
            parish_data_service.save(parish_data)
            messages.success(request, 'Račun označen kao plaćen.')
        else:
            messages.error(request, 'Račun nije pronađen.')
        return True

    return False
