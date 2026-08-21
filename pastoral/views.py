import json
from datetime import date
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .decorators import pastoral_login_required
from .actions import handle_page_post
from .forms import (
    AnointingForm,
    BaptismForm,
    CashbookEntryForm,
    EventForm,
    FuneralForm,
    IntentionForm,
    InvoiceForm,
    ParishDebtForm,
    ParishSettingsForm,
    RegistryBookForm,
    RegistryRecordForm,
    StreetForm,
    TaskForm,
    CouncilMeetingForm,
    CouncilMemberForm,
    ConfirmationCandidateForm,
    ConfirmationGroupForm,
    ConfirmationYearForm,
    FamilyForm,
    FamilyMemberForm,
    FamilyContributionForm,
    FirstCommunionCandidateForm,
    FirstCommunionGroupForm,
    FirstCommunionYearForm,
    VisitForm,
    WeddingForm,
)
from .page_handlers import build_page_context, dashboard_context
from .services.data import ParishDataService
from .services.admin_interface_theme import synchronize_admin_interface_theme
from .view_modules.authentication import (
    admin_login_redirect_view,
    index_view,
    login_view,
    logout_view,
)
from .view_modules.public_forms import (
    public_form_view,
    public_index_view,
)
from phase_two.module_registry import module_for_page
from pastoral.services.documents import get_template, render_template
from pastoral.services.documents_page import (
    build_field_values,
    intentions_table_html,
    parish_doc_defaults,
)


def _document_print_response(request, parish_data_service: ParishDataService):
    template_id = request.POST.get('template_id', '')
    document_template = get_template(template_id)
    if not document_template:
        messages.error(request, 'Predložak nije pronađen.')
        return redirect(request.get_full_path())

    parish_data = parish_data_service.load()
    parish_settings = parish_data_service.load_settings()
    document_defaults = parish_doc_defaults(parish_settings)
    field_values = build_field_values(
        request,
        document_template,
        document_defaults,
    )
    if template_id == 'raspored_nakana':
        field_values['tablica_nakana'] = intentions_table_html(
            parish_data,
            field_values.get('tjedan_od', ''),
        )

    rendered_document = render_template(template_id, field_values)
    document_context = _document_print_context(
        document_template=document_template,
        rendered_document=rendered_document,
        parish_settings=parish_settings,
        document_defaults=document_defaults,
    )
    return render(request, 'pastoral/document_print.html', document_context)


def _document_print_context(
    *,
    document_template,
    rendered_document,
    parish_settings,
    document_defaults,
):
    return {
        'doc_html': rendered_document,
        'doc_title': document_template.get('name', 'Ispis'),
        'doc_category': document_template.get('category', 'dokument'),
        'doc_template_id': document_template.get('id', ''),
        'doc_parish': (
            parish_settings.get('name')
            or parish_settings.get('shortName')
            or 'Župa'
        ),
        'doc_city': parish_settings.get('city') or '',
        'doc_diocese': parish_settings.get('diocese') or '',
        'doc_pastor': parish_settings.get('pastor') or '',
        'doc_issued_at': document_defaults.get('danas', ''),
        'doc_primary': parish_settings.get('primaryColor') or '#5c2e3a',
        'doc_accent': parish_settings.get('accentColor') or '#b8922a',
    }

ADMIN_PAGES = {
     'blagajna', 'dugovanja', 'financijska-izvjestaja',
    'javne-prijave', 'kalendar', 'krizma',
    'krsenja', 'maticne-knjige', 'mise', 'nakane', 'obitelji', 'pogrebi', 'pomazanje',
    'posjete', 'postavke', 'potvrde', 'prva-pricest', 'racuni',
     'ulice', 'vijeca', 'vjencanja', 'zupni-listic', 'podsjetnici', 'dekanat',
    'operativno-srediste',
}

REMOVED_PAGE_REDIRECTS = {
    'zadaci': 'kalendar',
    'poruke': 'operativno-srediste',
    'korisnici': 'dashboard',
    'sigurnost': 'operativno-srediste',
    'komunikacija': 'operativno-srediste',
    'dokumenti': 'potvrde',
    'formulari': 'potvrde',
}

PAGE_TEMPLATE_NAMES = {
    'kalendar': 'pastoral/pages/kalendar.html',
    'nakane': 'pastoral/pages/nakane.html',
    'obitelji': 'pastoral/pages/obitelji.html',
    'krizma': 'pastoral/pages/krizma.html',
    'krsenja': 'pastoral/pages/krsenja.html',
    'vjencanja': 'pastoral/pages/vjencanja.html',
    'pogrebi': 'pastoral/pages/pogrebi.html',
    'pomazanje': 'pastoral/pages/pomazanje.html',
    'dugovanja': 'pastoral/pages/dugovanja.html',
    'prva-pricest': 'pastoral/pages/prva_pricest.html',
    'mise': 'pastoral/pages/mise.html',
    'vijeca': 'pastoral/pages/vijeca.html',
    'podsjetnici': 'pastoral/pages/podsjetnici.html',
    'postavke': 'pastoral/pages/postavke.html',
    'zupni-listic': 'pastoral/pages/zupni-listic.html',
    'ulice': 'pastoral/pages/ulice.html',
    'blagajna': 'pastoral/pages/blagajna.html',
    'racuni': 'pastoral/pages/racuni.html',
    'javne-prijave': 'pastoral/pages/javne-prijave.html',
    'financijska-izvjestaja': 'pastoral/pages/financijska-izvjestaja.html',
    'potvrde': 'pastoral/pages/potvrde.html',
    'maticne-knjige': 'pastoral/pages/maticne-knjige.html',
    'posjete': 'pastoral/pages/posjete.html',
    'dekanat': 'pastoral/pages/dekanat.html',
    'operativno-srediste': 'pastoral/pages/operativno-srediste.html',
}

@pastoral_login_required
@require_http_methods(['GET', 'POST'])
def app_view(request):
    parish_data_service = ParishDataService()
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_task':
            task_id = request.POST.get('task_id')
            parish_data = parish_data_service.load()
            for task in parish_data.get('tasks', []):
                if task.get('id') == task_id:
                    task['done'] = not task.get('done')
            parish_data_service.save(parish_data)
            return redirect('pastoral:page', page='kalendar')
    page_context = dashboard_context(request, parish_data_service)
    page_context['page_title'] = 'Početna'
    page_context['page_subtitle'] = 'Što danas radite u župi'
    page_context['current_page'] = 'dashboard'
    return render(request, 'pastoral/dashboard.html', page_context)


def _add_standard_forms_to_page_context(
    page: str,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    if page == 'kalendar':
        pastor_name = parish_data_service.load_settings().get('pastor', '')
        selected_date = page_context.get('filter_date') or parish_data_service.today_iso()
        selected_task = page_context.get('selected_task')
        task_initial_values = {
            'owner': pastor_name,
            'due': selected_date,
            'priority': 'srednja',
        }
        if selected_task:
            task_initial_values.update({
                'title': selected_task.get('title', ''),
                'owner': selected_task.get('owner', ''),
                'due': selected_task.get('due') or None,
                'priority': selected_task.get('priority', 'srednja'),
                'category': selected_task.get('category', ''),
            })
        page_context['task_form'] = TaskForm(initial=task_initial_values)

        selected_event = page_context.get('selected_event')
        event_initial_values = {
            'owner': pastor_name,
            'event_date': selected_date,
        }
        if selected_event:
            event_initial_values.update({
                'title': selected_event.get('title', ''),
                'event_date': selected_event.get('date') or selected_date,
                'event_time': selected_event.get('time') or None,
                'place': selected_event.get('place', ''),
                'event_type': selected_event.get('type', 'pastoral'),
                'owner': selected_event.get('owner', ''),
                'notes': selected_event.get('notes', ''),
            })
        page_context['event_form'] = EventForm(initial=event_initial_values)
    elif page == 'vijeca':
        selected_council_member = page_context.get(
            'selected_council_member'
        )
        council_member_initial_values = {
            'council_type': page_context.get(
                'selected_council_type',
                'pastoral',
            ),
            'confirmed': True,
        }
        if selected_council_member:
            council_member_initial_values.update({
                'name': selected_council_member.get('name', ''),
                'role': selected_council_member.get('role', ''),
                'confirmed': selected_council_member.get(
                    'confirmed',
                    False,
                ),
            })
        page_context['council_member_form'] = CouncilMemberForm(
            initial=council_member_initial_values,
        )
        page_context['council_meeting_form'] = CouncilMeetingForm(initial={
            'council_type': page_context.get(
                'selected_council_type',
                'pastoral',
            ),
        })
    elif page == 'krizma':
        confirmation_group = page_context.get('confirmation', {})
        confirmation_year = page_context.get('conf_year')
        confirmation_years = page_context.get('conf_years') or [confirmation_year]
        page_context['confirmation_year_form'] = ConfirmationYearForm(
            initial={'year': max(confirmation_years) + 1},
        )
        page_context['confirmation_group_form'] = ConfirmationGroupForm(
            initial={
                'year': confirmation_year,
                'ceremony_date': confirmation_group.get('ceremonyDate'),
                'bishop': confirmation_group.get('bishop', ''),
                'group_fee': confirmation_group.get('groupFee', 0),
                'group_fee_paid': confirmation_group.get('groupFeePaid', False),
            },
        )
        page_context['confirmation_candidate_form'] = (
            ConfirmationCandidateForm(initial={
                'year': confirmation_year,
                'status': 'priprema',
            })
        )
    elif page == 'prva-pricest':
        first_communion_group = page_context.get('fc_group', {})
        first_communion_year = page_context.get('fc_year')
        first_communion_years = page_context.get('fc_years') or [
            first_communion_year
        ]
        page_context['first_communion_year_form'] = FirstCommunionYearForm(
            initial={'year': max(first_communion_years) + 1},
        )
        page_context['first_communion_group_form'] = FirstCommunionGroupForm(
            initial={
                'year': first_communion_year,
                'group_name': first_communion_group.get('groupName', ''),
                'ceremony_date': first_communion_group.get('ceremonyDate'),
                'celebrant': first_communion_group.get('celebrant', ''),
                'group_fee': first_communion_group.get('groupFee', 0),
                'group_fee_paid': first_communion_group.get(
                    'groupFeePaid',
                    False,
                ),
            },
        )
        page_context['first_communion_candidate_form'] = (
            FirstCommunionCandidateForm(initial={
                'year': first_communion_year,
                'status': 'priprema',
            })
        )
    elif page == 'obitelji':
        selected_family = page_context.get('selected_family')
        family_initial_values = {'status': 'aktivna'}
        if selected_family:
            family_initial_values.update({
                'surname': selected_family.get('surname', ''),
                'street_id': selected_family.get('streetId', ''),
                'address': selected_family.get('address', ''),
                'phone': selected_family.get('phone', ''),
                'email': selected_family.get('email', ''),
                'origin_place': selected_family.get('originPlace', ''),
                'status': selected_family.get('status', 'aktivna'),
                'pastoral_notes': selected_family.get('pastoralNotes', ''),
            })
        page_context['family_form'] = FamilyForm(
            streets=page_context.get('street_list', []),
            initial=family_initial_values,
        )
        page_context['family_member_form'] = FamilyMemberForm()
        from pastoral.services.api_action_handlers.shared import (
            DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT,
        )

        page_context['family_contribution_form'] = FamilyContributionForm(
            initial={
                'year': date.today().year,
                'lukno_amount': DEFAULT_ANNUAL_CONTRIBUTION_AMOUNT,
                'church_donation': 0,
            },
        )
    elif page == 'nakane':
        page_context['intention_form'] = IntentionForm(initial={
            'date': parish_data_service.today_iso(),
        })
    elif page == 'dugovanja':
        page_context['debt_form'] = ParishDebtForm()
    elif page == 'krsenja':
        page_context['baptism_form'] = BaptismForm()
    elif page == 'vjencanja':
        page_context['wedding_form'] = WeddingForm()
    elif page == 'pogrebi':
        page_context['funeral_form'] = FuneralForm()
    elif page == 'pomazanje':
        page_context['anointing_form'] = AnointingForm()
    elif page == 'postavke':
        parish_settings = page_context.get('settings', {})
        page_context['settings_form'] = ParishSettingsForm(initial={
            'name': parish_settings.get('name'),
            'short_name': parish_settings.get('shortName'),
            'city': parish_settings.get('city'),
            'diocese': parish_settings.get('diocese'),
            'pastor': parish_settings.get('pastor'),
            'phone': parish_settings.get('phone'),
            'email': parish_settings.get('email'),
            'primary_color': parish_settings.get('primaryColor'),
            'accent_color': parish_settings.get('accentColor'),
            'logo_url': parish_settings.get('logoUrl', ''),
            'default_mass_intention_stipend': parish_settings.get(
                'defaultMassIntentionStipend', 0
            ),
        })
    elif page == 'ulice':
        selected_street = page_context.get('selected_street')
        if page_context.get('street_form_mode') == 'edit' and selected_street:
            page_context['street_form'] = StreetForm(initial={
                'name': selected_street.get('name', ''),
                'zone': selected_street.get('zone', ''),
                'notes': selected_street.get('notes', ''),
            })
        else:
            page_context['street_form'] = StreetForm()
    elif page == 'blagajna':
        page_context['cashbook_form'] = CashbookEntryForm(initial={
            'date': parish_data_service.today_iso(),
        })
    elif page == 'racuni':
        page_context['invoice_form'] = InvoiceForm()


def _add_visit_form_to_page_context(
    request,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    parish_data = parish_data_service.load()
    families = parish_data.get('families', [])
    visit_initial_values = {'scheduled': parish_data_service.today_iso()}
    family_id = request.GET.get('family') or request.GET.get('family_id')
    if family_id:
        selected_family = next(
            (
                family
                for family in families
                if family.get('id') == family_id
            ),
            None,
        )
        if selected_family:
            visit_initial_values.update({
                'person': f"Obitelj {selected_family.get('surname', '')}".strip(),
                'address': selected_family.get('address', ''),
                'family_id': selected_family.get('id', ''),
                'visit_type': 'obitelj',
                'purpose': 'Pastoralni posjet',
            })
            page_context['prefilled_family'] = selected_family
    page_context['visit_form'] = VisitForm(
        families=families,
        initial=visit_initial_values,
    )

    visit_id = request.GET.get('visit')
    if not visit_id:
        return
    selected_visit = next(
        (
            visit
            for visit in parish_data.get('visits', [])
            if visit.get('id') == visit_id
        ),
        None,
    )
    if not selected_visit:
        return
    page_context['selected_visit'] = selected_visit
    page_context['visit_form'] = VisitForm(families=families, initial={
        'scheduled': selected_visit.get('scheduled'),
        'person': selected_visit.get('person', ''),
        'visit_type': selected_visit.get('type', 'obitelj'),
        'address': selected_visit.get('address', ''),
        'priest': selected_visit.get('priest', ''),
        'purpose': selected_visit.get('purpose', ''),
        'family_id': selected_visit.get('familyId', ''),
        'report': selected_visit.get('report', ''),
    })


def _add_operations_forms_to_page_context(
    request,
    page: str,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    from phase_two.forms import (
        FacilityIssueForm,
        InterparishRequestForm,
        OfficeEntryForm,
    )

    if page == 'dekanat':
        active_parish_id = parish_data_service.load_settings().get('_parishId', '')
        page_context['interparish_form'] = InterparishRequestForm(
            parishes=page_context.get('parish_directory', []),
            active_parish_id=active_parish_id,
            initial={
                'request_type': 'marriage_certificate',
                'due_date': parish_data_service.add_days(3),
                'priority': 'normal',
                'confidentiality': 'povjerljivo',
            },
        )
    elif page == 'operativno-srediste':
        page_context['office_entry_form'] = OfficeEntryForm(initial={
            'direction': 'incoming',
            'channel': 'in_person',
            'due_date': parish_data_service.add_days(3),
            'priority': 'normal',
            'confidentiality': 'službeno',
            'owner': getattr(request.user, 'name', '') or 'Župni ured',
        })
        page_context['facility_issue_form'] = FacilityIssueForm(initial={
            'risk': 'medium',
            'due_date': parish_data_service.add_days(7),
            'owner': 'Župni ured',
        })


def _add_registry_book_form_to_page_context(
    request,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    page_context['book_form'] = RegistryBookForm()
    selected_registry_book = page_context.get('selected_registry_book_view')
    selected_registry_year = page_context.get('selected_registry_year')
    if selected_registry_book and selected_registry_year:
        page_context['registry_record_form'] = RegistryRecordForm(
            registry_type=selected_registry_book.get('type', 'ostalo'),
            selected_year=selected_registry_year,
        )
    selected_book_id = request.GET.get('book')
    if not selected_book_id:
        return

    selected_book = next(
        (
            registry_book
            for registry_book in parish_data_service.load().get('registryBooks', [])
            if registry_book.get('id') == selected_book_id
        ),
        None,
    )
    if not selected_book:
        return
    page_context['selected_book'] = selected_book
    page_context['book_form'] = RegistryBookForm(initial={
        'title': selected_book.get('title', ''),
        'book_type': selected_book.get('type', 'krštenja'),
        'location': selected_book.get('location', ''),
        'last_entry': selected_book.get('lastEntry') or None,
        'last_no': selected_book.get('lastNo', ''),
        'custodian': selected_book.get('custodian', ''),
        'status': selected_book.get('status', 'u župi'),
        'notes': selected_book.get('notes', ''),
    })


def _build_admin_page_context(
    request,
    page: str,
    parish_data_service: ParishDataService,
) -> dict:
    page_context = build_page_context(request, page)
    page_context['current_page'] = page
    _add_standard_forms_to_page_context(
        page,
        parish_data_service,
        page_context,
    )
    if page == 'posjete':
        _add_visit_form_to_page_context(request, parish_data_service, page_context)
    elif page in {'dekanat', 'operativno-srediste'}:
        _add_operations_forms_to_page_context(
            request,
            page,
            parish_data_service,
            page_context,
        )
    elif page == 'maticne-knjige':
        _add_registry_book_form_to_page_context(
            request,
            parish_data_service,
            page_context,
        )
    return page_context


@pastoral_login_required
@require_http_methods(['GET', 'POST'])
def admin_page_view(request, page: str):
    if page in REMOVED_PAGE_REDIRECTS:
        target = REMOVED_PAGE_REDIRECTS[page]
        if target == 'dashboard':
            return redirect('pastoral:app')
        if request.method == 'GET':
            redirect_url = reverse('pastoral:page', kwargs={'page': target})
            query_string = request.GET.urlencode()
            if query_string:
                redirect_url = f'{redirect_url}?{query_string}'
            return redirect(redirect_url)
        page = target

    if page not in ADMIN_PAGES:
        from django.http import Http404
        raise Http404()

    product_module = module_for_page(page)
    if product_module and not product_module.is_available:
        return render(request, 'pastoral/pages/product_phase.html', {
            'page_title': product_module.label,
            'page_subtitle': f'Planirano za fazu {product_module.release_phase}',
            'current_page': page,
            'product_module': product_module,
        })

    parish_data_service = ParishDataService()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'preview_document' and page == 'potvrde':
            template_id = request.POST.get('template_id', '')
            document_template = get_template(template_id)
            query_parameters = {'tpl': template_id, 'preview': '1'}
            if document_template:
                for field_name in document_template.get('fields') or []:
                    field_value = request.POST.get(f'field_{field_name}', '')
                    if field_value:
                        query_parameters[field_name] = field_value
            return redirect(f'{request.path}?{urlencode(query_parameters)}')

        if action == 'print_document' and page == 'potvrde':
            return _document_print_response(request, parish_data_service)

        if handle_page_post(request, page, parish_data_service):
            return redirect(request.get_full_path())

        parish_data = parish_data_service.load()

        if action == 'add_task' and page == 'kalendar':
            form = TaskForm(request.POST)
            if form.is_valid():
                parish_data.setdefault('tasks', []).append({
                    'id': f't_{uuid.uuid4().hex[:8]}',
                    'title': form.cleaned_data['title'],
                    'owner': form.cleaned_data['owner'],
                    'due': form.cleaned_data['due'].isoformat() if form.cleaned_data.get('due') else '',
                    'priority': form.cleaned_data['priority'],
                    'category': form.cleaned_data.get('category') or 'ured',
                    'done': False,
                })
                parish_data_service.save(parish_data)
                messages.success(request, 'Zadatak dodan.')
            return redirect('pastoral:page', page=page)

        if action == 'add_event' and page == 'kalendar':
            form = EventForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                event_date = cleaned_data['event_date'].isoformat()
                event_time = (
                    cleaned_data['event_time'].strftime('%H:%M')
                    if cleaned_data.get('event_time')
                    else ''
                )
                place = cleaned_data.get('place') or ''
                conflict = next((
                    event for event in parish_data.get('events', [])
                    if event.get('date') == event_date
                    and event_time and event.get('time') == event_time
                    and place and (event.get('place') or '').casefold() == place.casefold()
                ), None)
                if conflict:
                    messages.error(request, f"Termin se preklapa s događajem ‘{conflict.get('title', '')}’ u istom prostoru.")
                else:
                    parish_data.setdefault('events', []).append({
                        'id': f'e_{uuid.uuid4().hex[:8]}',
                        'title': cleaned_data['title'],
                        'date': event_date,
                        'time': event_time,
                        'place': place,
                        'type': cleaned_data['event_type'],
                        'owner': cleaned_data['owner'],
                        'notes': cleaned_data.get('notes') or '',
                    })
                    parish_data_service.save(parish_data)
                    messages.success(request, 'Župni događaj dodan u zajednički kalendar.')
            else:
                messages.error(request, 'Provjerite obvezna polja događaja.')
            return redirect(f"{reverse('pastoral:page', kwargs={'page': page})}?date={request.POST.get('event_date', '')}")

        if action == 'toggle_task' and page == 'kalendar':
            task_id = request.POST.get('task_id')
            for task in parish_data.get('tasks', []):
                if task.get('id') == task_id:
                    task['done'] = not task.get('done')
            parish_data_service.save(parish_data)
            return redirect('pastoral:page', page=page)

    page_context = _build_admin_page_context(
        request,
        page,
        parish_data_service,
    )
    template_name = PAGE_TEMPLATE_NAMES[page]
    return render(request, template_name, page_context)


@login_required
@require_POST
def save_theme_view(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    parish_data_service = ParishDataService()
    parish_settings = parish_data_service.load_settings()
    for key in (
        'primaryColor', 'accentColor', 'bgColor', 'bgPatternColor',
        'themePresetId', 'customTheme', 'colorScheme',
    ):
        if key in payload:
            parish_settings[key] = payload[key]
    parish_data_service.save_settings(parish_settings)
    synchronize_admin_interface_theme(
        parish_settings.get('primaryColor'),
        parish_settings.get('accentColor'),
    )
    return JsonResponse({'ok': True})


def legacy_redirect(request, target):
    mapping = {
        'login.html': 'pastoral:login',
        'app.html': 'pastoral:app',
        'index.html': 'pastoral:index',
    }
    if target in mapping:
        return redirect(mapping[target])
    if target.startswith('pages/'):
        page = target.replace('pages/', '').replace('.html', '')
        if page in REMOVED_PAGE_REDIRECTS:
            redirected_page = REMOVED_PAGE_REDIRECTS[page]
            if redirected_page == 'dashboard':
                return redirect(_login_destination(request, user))
            return redirect('pastoral:page', page=redirected_page)
        if page in ADMIN_PAGES:
            return redirect('pastoral:page', page=page)
    if target.startswith('public/'):
        rest = target.replace('public/', '')
        if rest == 'index.html':
            return redirect('pastoral:public_index')
        name = rest.replace('.html', '')
        if name in PUBLIC_FORMS:
            return redirect('pastoral:public_form', form=name)
    from django.http import Http404
    raise Http404()
