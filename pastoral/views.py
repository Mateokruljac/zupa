import json
import re
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .decorators import pastoral_login_required
from .page_actions.dispatcher import handle_page_post
from financije.forms import CashbookEntryForm, DonationForm, InvoiceForm, ParishDebtForm
from financije.ledgers import LEDGER_CRKVENI, LEDGER_GRADNJA, LEDGER_KOLEKTE
from isprave.document_print import document_print_response
from isprave.page_forms import attach_isprave_forms
from liturgija.forms import IntentionForm
from sakramenti.page_forms import attach_sacrament_forms
from ured.page_forms import attach_ured_forms
from zupa_vjernici.page_forms import attach_parish_community_forms
from .page_handlers import build_page_context
from .services.data import ParishDataService
from .services.admin_interface_theme import synchronize_admin_interface_theme

from .view_modules.authentication import (  # noqa: F401
    admin_login_redirect_view,
    index_view,
    login_view,
    logout_view,
    web_manifest_view,
)
from .view_modules.public_forms import (  # noqa: F401
    PUBLIC_FORMS,
    public_form_view,
    public_index_view,
    public_privacy_view,
    public_terms_view,
)
from phase_two.module_registry import module_for_page

ADMIN_PAGES = {
     'blagajna', 'dugovanja', 'financijska-izvjestaja',
    'javne-prijave', 'kalendar', 'krizma',
    'krsenja', 'maticne-knjige', 'mise', 'nakane', 'obitelji', 'pogrebi', 'pomazanje',
    'posjete', 'postavke', 'potvrde', 'prva-pricest', 'racuni',
     'ulice', 'vijeca', 'vjencanja', 'zupni-listic', 'podsjetnici', 'dekanat',
    'operativno-srediste',
}

THEME_COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')
THEME_PRESET_PATTERN = re.compile(r'^[a-z0-9-]{1,40}$')
THEME_COLOR_KEYS = frozenset({
    'primaryColor', 'accentColor', 'bgColor', 'bgPatternColor',
})

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
    'kalendar': 'ured/pages/kalendar.html',
    'nakane': 'liturgija/pages/nakane.html',
    'obitelji': 'zupa_vjernici/pages/obitelji.html',
    'krizma': 'sakramenti/pages/krizma.html',
    'krsenja': 'sakramenti/pages/krsenja.html',
    'vjencanja': 'sakramenti/pages/vjencanja.html',
    'pogrebi': 'sakramenti/pages/pogrebi.html',
    'pomazanje': 'sakramenti/pages/pomazanje.html',
    'dugovanja': 'financije/pages/dugovanja.html',
    'prva-pricest': 'sakramenti/pages/prva-pricest.html',
    'mise': 'liturgija/pages/mise.html',
    'vijeca': 'ured/pages/vijeca.html',
    'podsjetnici': 'ured/pages/podsjetnici.html',
    'postavke': 'ured/pages/postavke.html',
    'zupni-listic': 'liturgija/pages/zupni-listic.html',
    'ulice': 'zupa_vjernici/pages/ulice.html',
    'blagajna': 'financije/pages/blagajna.html',
    'racuni': 'financije/pages/racuni.html',
    'javne-prijave': 'ured/pages/javne-prijave.html',
    'financijska-izvjestaja': 'financije/pages/financijska-izvjestaja.html',
    'potvrde': 'isprave/pages/potvrde.html',
    'maticne-knjige': 'isprave/pages/maticne-knjige.html',
    'posjete': 'zupa_vjernici/pages/posjete.html',
    'dekanat': 'pastoral/pages/dekanat.html',
    'operativno-srediste': 'pastoral/pages/operativno-srediste.html',
}


def _add_standard_forms_to_page_context(
    page: str,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    if page == 'nakane':
        page_context['intention_form'] = IntentionForm(initial={
            'date': parish_data_service.today_iso(),
        })
    elif page == 'dugovanja':
        page_context['debt_form'] = ParishDebtForm()
    elif page == 'blagajna':
        current_ledger = page_context.get('cashbook_ledger') or LEDGER_CRKVENI
        donation_purpose = (
            current_ledger
            if current_ledger in {LEDGER_CRKVENI, LEDGER_GRADNJA, LEDGER_KOLEKTE}
            else LEDGER_CRKVENI
        )
        page_context['cashbook_form'] = CashbookEntryForm(initial={
            'date': parish_data_service.today_iso(),
            'ledger': current_ledger,
        })
        page_context['donation_form'] = DonationForm(initial={
            'date': parish_data_service.today_iso(),
            'purpose': donation_purpose,
        })
    elif page == 'racuni':
        page_context['invoice_form'] = InvoiceForm()


def _add_operations_forms_to_page_context(
    request,
    page: str,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    try:
        from phase_two.forms import (
            FacilityIssueForm,
            InterparishRequestForm,
            OfficeEntryForm,
        )
    except ModuleNotFoundError:
        return

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


def _build_admin_page_context(
    request,
    page: str,
    parish_data_service: ParishDataService,
) -> dict:
    page_context = build_page_context(request, page)
    page_context['current_page'] = page
    forms_attached = attach_parish_community_forms(
        request,
        page,
        parish_data_service,
        page_context,
    )
    forms_attached = forms_attached or attach_sacrament_forms(page, page_context)
    forms_attached = forms_attached or attach_isprave_forms(
        request, page, parish_data_service, page_context,
    )
    forms_attached = forms_attached or attach_ured_forms(
        request, page, parish_data_service, page_context,
    )
    if not forms_attached:
        _add_standard_forms_to_page_context(
            page,
            parish_data_service,
            page_context,
        )
    if page in {'dekanat', 'operativno-srediste'}:
        _add_operations_forms_to_page_context(
            request,
            page,
            parish_data_service,
            page_context,
        )
    return page_context


@pastoral_login_required
def app_view(request):
    """Kompatibilni alias — nadzorna ploča živi u pregled:dashboard."""
    return redirect('pregled:dashboard')


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

    parish_data_service = ParishDataService.for_request(request)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'preview_document' and page == 'potvrde':
            from isprave.services.documents import get_template

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
            return document_print_response(request, parish_data_service)

        if handle_page_post(request, page, parish_data_service):
            return redirect(request.get_full_path())

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
    if not isinstance(payload, dict):
        return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)

    invalid_colors = [
        key for key in THEME_COLOR_KEYS
        if key in payload and not THEME_COLOR_PATTERN.fullmatch(str(payload[key]))
    ]
    if invalid_colors:
        return JsonResponse({'ok': False, 'error': 'invalid_theme'}, status=400)
    if (
        'colorScheme' in payload
        and payload['colorScheme'] not in {'light', 'dark', 'system'}
    ):
        return JsonResponse({'ok': False, 'error': 'invalid_theme'}, status=400)
    if (
        'themePresetId' in payload
        and not THEME_PRESET_PATTERN.fullmatch(str(payload['themePresetId']))
    ):
        return JsonResponse({'ok': False, 'error': 'invalid_theme'}, status=400)
    if 'customTheme' in payload and not isinstance(payload['customTheme'], bool):
        return JsonResponse({'ok': False, 'error': 'invalid_theme'}, status=400)

    parish_data_service = ParishDataService.for_request(request)
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
                return redirect('pastoral:app')
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
