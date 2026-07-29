"""POST akcije za admin stranice."""
from __future__ import annotations

from datetime import date

import uuid

from django.contrib import messages

from pastoral.forms import (
    AnointingForm,
    BaptismForm,
    CashbookEntryForm,
    FuneralForm,
    IntentionForm,
    InvoiceForm,
    ParishDebtForm,
    RegistryBookForm,
    StreetForm,
    VisitForm,
    WeddingForm,
)
from pastoral.services.api_actions import (
    create_cashbook_entry,
    delete_street,
    import_public_submission,
    mark_invoice_paid,
    normalize_data,
    toggle_visit_done,
    upsert_invoice,
    upsert_street,
    upsert_visit,
)
from pastoral.services.documents import get_template
from pastoral.services.document_import import delete_binding, save_binding
from pastoral.services.mutations import (
    add_intention,
    add_parish_debt,
    add_sacrament_record,
    delete_intention,
    delete_sacrament,
    mark_debt_paid,
    parse_debt_source,
    toggle_intention_paid,
)


def handle_page_post(request, page: str, svc) -> bool:
    """Obrađuje POST; vraća True ako je akcija obrađena."""
    action = request.POST.get('action')
    if not action:
        return False

    data = svc.load()

    if action == 'mark_debt_paid':
        source = parse_debt_source(request.POST.get('source', ''))
        if mark_debt_paid(data, source):
            svc.save(data)
            messages.success(request, 'Označeno kao plaćeno.')
        else:
            messages.error(request, 'Stavka nije pronađena.')
        return True

    if action == 'add_intention' and page == 'nakane':
        form = IntentionForm(request.POST)
        if form.is_valid():
            add_intention(data, form.cleaned_data)
            svc.save(data)
            messages.success(request, 'Nakana dodana.')
        else:
            messages.error(request, 'Provjerite unos nakane.')
        return True

    if action == 'delete_intention' and page == 'nakane':
        if delete_intention(data, request.POST.get('intention_id', '')):
            svc.save(data)
            messages.success(request, 'Nakana obrisana.')
        return True

    if action == 'toggle_intention_paid' and page == 'nakane':
        if toggle_intention_paid(data, request.POST.get('intention_id', '')):
            svc.save(data)
            messages.success(request, 'Status plaćanja ažuriran.')
        return True

    if action == 'add_parish_debt' and page == 'dugovanja':
        form = ParishDebtForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            add_parish_debt(data, {**cd, 'direction': 'payable'})
            svc.save(data)
            messages.success(request, 'Dugovanje dodano.')
        else:
            messages.error(request, 'Provjerite unos.')
        return True

    if action == 'add_baptism' and page == 'krsenja':
        form = BaptismForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            add_sacrament_record(data, 'baptisms', {
                'childName': cd['child_name'],
                'baptismDate': cd['baptism_date'].isoformat() if cd.get('baptism_date') else '',
                'parents': cd['parents'],
                'status': cd.get('status') or 'planirano',
                'stipend': float(cd.get('stipend') or 0),
                'stipendPaid': False,
            })
            svc.save(data)
            messages.success(request, 'Krštenje dodano.')
        return True

    if action == 'delete_baptism' and page == 'krsenja':
        if delete_sacrament(data, 'baptisms', request.POST.get('record_id', '')):
            svc.save(data)
            messages.success(request, 'Zapis obrisan.')
        return True

    if action == 'add_wedding' and page == 'vjencanja':
        form = WeddingForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            add_sacrament_record(data, 'weddings', {
                'couple': cd['couple'],
                'weddingDate': cd['wedding_date'].isoformat() if cd.get('wedding_date') else '',
                'status': cd.get('status') or 'planirano',
                'stipend': float(cd.get('stipend') or 0),
                'stipendPaid': False,
            })
            svc.save(data)
            messages.success(request, 'Vjenčanje dodano.')
        return True

    if action == 'delete_wedding' and page == 'vjencanja':
        if delete_sacrament(data, 'weddings', request.POST.get('record_id', '')):
            svc.save(data)
            messages.success(request, 'Zapis obrisan.')
        return True

    if action == 'add_funeral' and page == 'pogrebi':
        form = FuneralForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            add_sacrament_record(data, 'funerals', {
                'deceased': cd['deceased'],
                'funeralDate': cd['funeral_date'].isoformat() if cd.get('funeral_date') else '',
                'cemetery': cd.get('cemetery') or '',
                'status': cd.get('status') or 'planirano',
                'stipend': float(cd.get('stipend') or 0),
                'stipendPaid': False,
            })
            svc.save(data)
            messages.success(request, 'Pogreb dodan.')
        return True

    if action == 'delete_funeral' and page == 'pogrebi':
        if delete_sacrament(data, 'funerals', request.POST.get('record_id', '')):
            svc.save(data)
            messages.success(request, 'Zapis obrisan.')
        return True

    if action == 'add_anointing' and page == 'pomazanje':
        form = AnointingForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            add_sacrament_record(data, 'anointing', {
                'person': cd['person'],
                'scheduled': cd['scheduled'].isoformat() if cd.get('scheduled') else '',
                'priest': cd.get('priest') or '',
                'address': cd.get('address') or '',
                'contact': cd.get('contact') or '',
                'status': cd.get('status') or 'planirano',
                'stipend': float(cd.get('stipend') or 0),
                'stipendPaid': False,
            })
            svc.save(data)
            messages.success(request, 'Pomazanje dodano.')
        return True

    if action == 'delete_anointing' and page == 'pomazanje':
        if delete_sacrament(data, 'anointing', request.POST.get('record_id', '')):
            svc.save(data)
            messages.success(request, 'Zapis obrisan.')
        return True

    if action == 'upsert_street' and page == 'ulice':
        form = StreetForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            payload = {
                'id': request.POST.get('street_id') or None,
                'name': cd['name'],
                'zone': cd.get('zone') or '',
                'notes': cd.get('notes') or '',
            }
            normalize_data(data)
            result = upsert_street(data, payload)
            if result.get('ok'):
                svc.save(data)
                messages.success(request, 'Ulica spremljena.')
            else:
                messages.error(request, 'Provjerite unos ulice.')
        else:
            messages.error(request, 'Provjerite unos ulice.')
        return True

    if action == 'delete_street' and page == 'ulice':
        normalize_data(data)
        delete_street(data, {'id': request.POST.get('street_id', '')})
        svc.save(data)
        messages.success(request, 'Ulica obrisana.')
        return True

    if action == 'add_cashbook_entry' and page == 'blagajna':
        form = CashbookEntryForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            normalize_data(data)
            create_cashbook_entry(data, {
                'fields': {
                    'date': cd['date'].isoformat(),
                    'type': cd['entry_type'],
                    'ledger': cd['ledger'],
                    'category': cd['category'],
                    'description': cd['description'],
                    'amount': float(cd['amount']),
                    'paymentMethod': cd.get('payment_method') or 'gotovina',
                },
            })
            svc.save(data)
            messages.success(request, 'Unos u blagajnu dodan.')
        else:
            messages.error(request, 'Provjerite unos.')
        return True

    if action == 'add_invoice' and page == 'racuni':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            amt = float(cd['amount'])
            normalize_data(data)
            upsert_invoice(data, {
                'fields': {
                    'number': cd['number'],
                    'issueDate': cd['issue_date'].isoformat() if cd.get('issue_date') else '',
                    'dueDate': cd['due_date'].isoformat() if cd.get('due_date') else '',
                    'supplierName': cd['supplier_name'],
                    'category': cd['category'],
                    'description': cd['description'],
                    'amount': amt,
                    'vatRate': 0,
                    'total': amt,
                    'status': 'primljen',
                    'paidAmount': 0,
                    'direction': 'incoming',
                },
            })
            svc.save(data)
            messages.success(request, 'Račun dodan.')
        else:
            messages.error(request, 'Provjerite unos računa.')
        return True

    if action == 'mark_invoice_paid' and page == 'racuni':
        normalize_data(data)
        if mark_invoice_paid(data, {'id': request.POST.get('invoice_id', '')}).get('ok'):
            svc.save(data)
            messages.success(request, 'Račun označen kao plaćen.')
        else:
            messages.error(request, 'Račun nije pronađen.')
        return True

    if action == 'import_submission' and page == 'javne-prijave':
        sub_id = request.POST.get('submission_id', '')
        sub = next((s for s in data.get('publicSubmissions', []) if s.get('id') == sub_id), None)
        if not sub:
            messages.error(request, 'Prijava nije pronađena.')
            return True
        year = int(request.POST.get('year') or date.today().year)
        normalize_data(data)
        result = import_public_submission(data, {'submission': sub, 'year': year})
        if result.get('ok'):
            svc.save(data)
            messages.success(request, 'Prijava uvezena u evidenciju.')
        else:
            messages.error(request, 'Uvoz nije uspio.')
        return True

    if action == 'mark_submission_imported' and page == 'javne-prijave':
        sub_id = request.POST.get('submission_id', '')
        sub = next((s for s in data.get('publicSubmissions', []) if s.get('id') == sub_id), None)
        if sub:
            sub['status'] = 'preuzeto'
            svc.save(data)
            messages.success(request, 'Prijava označena kao preuzeta.')
        return True

    if action == 'upsert_visit' and page == 'posjete':
        form = VisitForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            payload = {
                'scheduled': cd['scheduled'].isoformat(),
                'person': cd['person'],
                'type': cd['visit_type'],
                'address': cd.get('address') or '',
                'priest': cd.get('priest') or '',
                'purpose': cd.get('purpose') or '',
                'familyId': cd.get('family_id') or '',
                'report': cd.get('report') or '',
            }
            vid = request.POST.get('visit_id')
            result = upsert_visit(data, {'id': vid, 'fields': payload} if vid else payload)
            if result.get('ok'):
                svc.save(data)
                messages.success(request, 'Posjet spremljen.')
            else:
                messages.error(request, 'Posjet nije spremljen.')
        else:
            messages.error(request, 'Provjerite unos posjeta.')
        return True

    if action == 'toggle_visit' and page == 'posjete':
        result = toggle_visit_done(data, {'id': request.POST.get('visit_id', '')})
        if result.get('ok'):
            svc.save(data)
            messages.success(request, 'Status posjeta ažuriran.')
        return True

    if action == 'delete_visit' and page == 'posjete':
        vid = request.POST.get('visit_id', '')
        before = len(data.get('visits', []))
        data['visits'] = [v for v in data.get('visits', []) if v.get('id') != vid]
        if len(data['visits']) < before:
            svc.save(data)
            messages.success(request, 'Posjet obrisan.')
        return True

    if action == 'upsert_registry_book' and page == 'maticne-knjige':
        form = RegistryBookForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            bid = request.POST.get('book_id')
            payload = {
                'title': cd['title'],
                'type': cd['book_type'],
                'location': cd.get('location') or '',
                'lastEntry': cd['last_entry'].isoformat() if cd.get('last_entry') else '',
                'lastNo': cd.get('last_no') or '',
                'custodian': cd.get('custodian') or '',
                'status': cd.get('status') or 'u župi',
                'notes': cd.get('notes') or '',
            }
            books = data.setdefault('registryBooks', [])
            if bid:
                row = next((b for b in books if b.get('id') == bid), None)
                if row:
                    row.update(payload)
            else:
                books.append({'id': f"rk_{uuid.uuid4().hex[:8]}", **payload})
            svc.save(data)
            messages.success(request, 'Matična knjiga spremljena.')
        else:
            messages.error(request, 'Provjerite unos.')
        return True

    if action == 'delete_registry_book' and page == 'maticne-knjige':
        bid = request.POST.get('book_id', '')
        books = data.get('registryBooks', [])
        data['registryBooks'] = [b for b in books if b.get('id') != bid]
        if len(data['registryBooks']) < len(books):
            svc.save(data)
            messages.success(request, 'Zapis obrisan.')
        return True

    if action == 'save_doc_binding' and page == 'dokumenti':
        template_id = request.POST.get('template_id', '')
        tpl = get_template(template_id)
        if not tpl:
            messages.error(request, 'Predložak nije pronađen.')
            return True
        mapping = {}
        for key in request.POST:
            if key.startswith('map_'):
                mapping[key[4:]] = request.POST.get(key, '')
        import_data = request.session.get('doc_import') or {}
        rows = import_data.get('rows') or []
        save_binding(
            data,
            template_id,
            tpl.get('name', ''),
            import_data.get('fileName', ''),
            mapping,
            len(rows),
        )
        svc.save(data)
        messages.success(request, 'Povezivanje stupaca spremljeno.')
        return True

    if action == 'delete_doc_binding' and page == 'dokumenti':
        if delete_binding(data, request.POST.get('binding_id', '')):
            svc.save(data)
            messages.success(request, 'Povezivanje uklonjeno.')
        return True

    return False
