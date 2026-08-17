import json
import uuid

from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods, require_POST

from users.models import User

from .decorators import pastoral_login_required
from .actions import handle_page_post
from .forms import (
    AnointingForm,
    BaptismForm,
    CashbookEntryForm,
    EventForm,
    FuneralForm,
    FacilityIssueForm,
    IntentionForm,
    InvoiceForm,
    InterparishRequestForm,
    LoginForm,
    OtpVerifyForm,
    OfficeEntryForm,
    ParishDebtForm,
    PUBLIC_FORM_CLASSES,
    PUBLIC_FORM_INTROS,
    ParishSettingsForm,
    RegistryBookForm,
    StreetForm,
    TaskForm,
    CommunicationPlanForm,
    CouncilMeetingForm,
    CouncilMemberForm,
    ConfirmationCandidateForm,
    ConfirmationGroupForm,
    FamilyForm,
    FirstCommunionCandidateForm,
    VisitForm,
    WeddingForm,
)
from .models import OtpChallenge
from .page_handlers import build_page_context, dashboard_context
from .services.data import ParishDataService
from .services.public_forms import build_submission_payload, dispatch_public_submission_email
from .services.otp import create_otp_challenge, dispatch_otp_email, store_otp_session
from pastoral.services.documents import get_template, render_template
from pastoral.services.documents_page import (
    build_field_values,
    intentions_table_html,
    parish_doc_defaults,
)
from pastoral.services.document_import import parse_csv_upload, render_row_html
from public_site.forms import ParishWebsiteForm, ParishWebsiteMediaForm
from public_site.models import ParishWebsite, ParishWebsiteMedia, PublicContentPublication
from public_site.snapshots import build_public_snapshot
from public_site.services import (
    activate_public_website,
    complete_demo_build,
    delete_website_media,
    publish_demo_website,
    reset_demo_website,
    save_website_media,
    update_content_publication,
    website_for,
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
     'blagajna', 'dokumenti', 'dugovanja', 'financijska-izvjestaja',
    'formulari', 'javne-prijave', 'kalendar', 'krizma',
    'krsenja', 'maticne-knjige', 'mise', 'nakane', 'obitelji', 'pogrebi', 'pomazanje',
    'posjete', 'postavke', 'potvrde', 'prva-pricest', 'racuni',
     'ulice', 'vijeca', 'vjencanja', 'zupni-listic', 'podsjetnici', 'dekanat',
    'operativno-srediste', 'web-stranica',
}

REMOVED_PAGE_REDIRECTS = {
    'zadaci': 'kalendar',
    'poruke': 'operativno-srediste',
    'korisnici': 'dashboard',
    'sigurnost': 'operativno-srediste',
    'komunikacija': 'operativno-srediste',
}

PUBLIC_FORMS = {
    'prijava-krizma', 'prijava-krsenje', 'prijava-pricest', 'prijava-ukop',
}

PUBLIC_FORM_LABELS = {
    'prijava-krizma': 'Prijava za krizmu',
    'prijava-krsenje': 'Prijava za krštenje',
    'prijava-pricest': 'Prijava za prvu pričest',
    'prijava-ukop': 'Prijava za ukop',
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
    'formulari': 'pastoral/pages/formulari.html',
    'potvrde': 'pastoral/pages/potvrde.html',
    'dokumenti': 'pastoral/pages/dokumenti.html',
    'maticne-knjige': 'pastoral/pages/maticne-knjige.html',
    'posjete': 'pastoral/pages/posjete.html',
    'dekanat': 'pastoral/pages/dekanat.html',
    'operativno-srediste': 'pastoral/pages/operativno-srediste.html',
    'web-stranica': 'pastoral/pages/web_stranica.html',
}



@require_http_methods(['GET', 'POST'])
def index_view(request):
    return redirect('pastoral:login')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('pastoral:app')

    pending = request.session.get('otp_pending')
    if pending and request.method == 'POST' and 'code' in request.POST:
        form = OtpVerifyForm(request.POST)
        if form.is_valid():
            challenge = (
                OtpChallenge.objects.filter(
                    email=pending['email'],
                    role=pending['role'],
                    used=False,
                )
                .order_by('-created_at')
                .first()
            )
            if challenge and challenge.code == form.cleaned_data['code']:
                challenge.used = True
                challenge.save(update_fields=['used'])
                user, _ = User.objects.get_or_create(
                    email=pending['email'],
                    defaults={'name': pending['email'].split('@')[0], 'role': pending['role']},
                )
                user.role = pending['role']
                user.save(update_fields=['role'])
                login(request, user)
                request.session.pop('otp_pending', None)
                messages.success(request, f'Dobrodošli, {user.role_label}.')
                return redirect('pastoral:app')
            messages.error(request, 'Neispravan kod. Pokušajte ponovo.')
        return render(request, 'pastoral/login.html', {
            'otp_mode': True,
            'otp_form': form,
            'form': LoginForm(),
            'email': pending.get('email'),
            'otp_recipient': getattr(settings, 'OTP_RECIPIENT', ''),
        })

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].lower()
        role = (
            User.objects.filter(email__iexact=email).values_list('role', flat=True).first()
            or User._meta.get_field('role').default
        )
        code = create_otp_challenge(email, role)
        mail_ok, mail_result = dispatch_otp_email(code, email, role)
        if not mail_ok:
            detail = mail_result.get('detail') or mail_result.get('error', 'mail_failed')
            messages.error(request, f'Nije moguće poslati e-mail: {detail}')
            return render(request, 'pastoral/login.html', {
                'form': form,
                'otp_form': OtpVerifyForm(),
            })

        store_otp_session(request, email=email, role=role)
        recipient = mail_result.get('recipient', getattr(settings, 'OTP_RECIPIENT', ''))
        messages.success(request, f'Kod je poslan na e-mail ({recipient}). Unesite ga ispod.')
        return render(request, 'pastoral/login.html', {
            'otp_mode': True,
            'otp_form': OtpVerifyForm(),
            'form': LoginForm(),
            'email': email,
            'otp_recipient': recipient,
        })

    return render(request, 'pastoral/login.html', {
        'form': form,
        'otp_form': OtpVerifyForm(),
    })


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Odjavljeni ste.')
    return redirect('pastoral:login')


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
        page_context['task_form'] = TaskForm(initial={
            'owner': pastor_name,
            'due': selected_date,
        })
        page_context['event_form'] = EventForm(initial={
            'owner': pastor_name,
            'event_date': selected_date,
        })
    elif page == 'vijeca':
        page_context['council_member_form'] = CouncilMemberForm(initial={
            'council_type': 'pastoral',
            'confirmed': True,
        })
        page_context['council_meeting_form'] = CouncilMeetingForm(initial={
            'council_type': 'pastoral',
        })
    elif page == 'krizma':
        confirmation_group = page_context.get('confirmation', {})
        confirmation_year = page_context.get('conf_year')
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
        page_context['first_communion_candidate_form'] = (
            FirstCommunionCandidateForm(initial={
                'year': page_context.get('fc_year'),
                'status': 'priprema',
            })
        )
    elif page == 'obitelji':
        page_context['family_form'] = FamilyForm(
            streets=page_context.get('street_list', []),
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


def _add_website_to_page_context(
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    parish_website = website_for(parish_data_service.parish)
    page_context['public_website'] = parish_website
    page_context['website_build'] = (
        parish_website.builds.first() if parish_website else None
    )
    page_context['website_form'] = (
        ParishWebsiteForm(instance=parish_website) if parish_website else None
    )
    page_context['hero_media_form'] = (
        ParishWebsiteMediaForm(prefix='hero') if parish_website else None
    )
    page_context['gallery_media_form'] = (
        ParishWebsiteMediaForm(prefix='gallery') if parish_website else None
    )
    page_context['website_hero_media'] = (
        parish_website.media.filter(kind=ParishWebsiteMedia.Kind.HERO).first()
        if parish_website
        else None
    )
    page_context['website_gallery_media'] = (
        parish_website.media.filter(kind=ParishWebsiteMedia.Kind.GALLERY)
        if parish_website
        else ()
    )
    page_context['website_demo_auto_activate'] = (
        settings.PUBLIC_WEBSITE_DEMO_AUTO_ACTIVATE
    )
    if not parish_website:
        return

    preview_snapshot = build_public_snapshot(parish_website, preview=True)
    page_context['website_content_items'] = [
        {'kind': 'announcement', 'kind_label': 'Obavijest', **announcement}
        for announcement in preview_snapshot['announcements']
    ] + [
        {'kind': 'event', 'kind_label': 'Događanje', **event}
        for event in preview_snapshot['events']
    ]
    page_context['publication_status_choices'] = (
        PublicContentPublication.Status.choices
    )


def _add_visit_form_to_page_context(
    request,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    parish_data = parish_data_service.load()
    visit_initial_values = {'scheduled': parish_data_service.today_iso()}
    family_id = request.GET.get('family') or request.GET.get('family_id')
    if family_id:
        selected_family = next(
            (
                family
                for family in parish_data.get('families', [])
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
    page_context['visit_form'] = VisitForm(initial=visit_initial_values)

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
    page_context['visit_form'] = VisitForm(initial={
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
        page_context['communication_plan_form'] = CommunicationPlanForm(initial={
            'channel': 'email',
            'requires_approval': True,
        })


def _add_registry_book_form_to_page_context(
    request,
    parish_data_service: ParishDataService,
    page_context: dict,
) -> None:
    page_context['book_form'] = RegistryBookForm()
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
    if page == 'web-stranica':
        _add_website_to_page_context(parish_data_service, page_context)
    elif page == 'posjete':
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
        return redirect('pastoral:page', page=target)

    if page not in ADMIN_PAGES:
        from django.http import Http404
        raise Http404()

    parish_data_service = ParishDataService()

    if request.method == 'POST':
        action = request.POST.get('action')

        if page == 'web-stranica' and action == 'activate_public_website':
            try:
                activate_public_website(
                    parish=parish_data_service.parish,
                    actor=request.user,
                )
            except PermissionDenied:
                messages.error(request, 'Aktivacija trenutačno nije dostupna.')
            else:
                messages.success(
                    request,
                    'Dodatna usluga je aktivirana. Izrada web-stranice je zakazana i pokrenuta.',
                )
            return redirect('pastoral:page', page=page)

        if page == 'web-stranica' and action == 'complete_demo_build':
            website = website_for(parish_data_service.parish)
            if website:
                complete_demo_build(website=website, actor=request.user)
                messages.success(request, 'Početna demo verzija je izrađena i spremna za uređivanje.')
            return redirect('pastoral:page', page=page)

        if page == 'web-stranica' and action == 'save_website':
            website = website_for(parish_data_service.parish)
            if website:
                form = ParishWebsiteForm(request.POST, instance=website)
                if form.is_valid():
                    form.save()
                    website.publication_status = ParishWebsite.PublicationStatus.DRAFT
                    website.save(update_fields=('publication_status', 'updated_at'))
                    messages.success(request, 'Promjene su spremljene kao skica. Provjerite ih prije objave.')
                else:
                    messages.error(request, 'Provjerite unesene postavke web-stranice.')
            return redirect('pastoral:page', page=page)

        if page == 'web-stranica' and action == 'update_content_publication':
            website = website_for(parish_data_service.parish)
            kind = request.POST.get('kind', '')
            source_key = request.POST.get('source_key', '')
            status = request.POST.get('status', '')
            scheduled_for = parse_datetime(request.POST.get('scheduled_for', ''))
            if scheduled_for and timezone.is_naive(scheduled_for):
                scheduled_for = timezone.make_aware(scheduled_for)
            available = {}
            if website:
                snapshot = build_public_snapshot(website, preview=True)
                available = {
                    ('announcement', announcement['source_key']): announcement['title']
                    for announcement in snapshot['announcements']
                }
                available.update({
                    ('event', event['source_key']): event['title']
                    for event in snapshot['events']
                })
            source_label = available.get((kind, source_key))
            if not website or not source_label:
                messages.error(request, 'Sadržaj za objavu nije pronađen u ovoj župi.')
            else:
                try:
                    update_content_publication(
                        website=website,
                        actor=request.user,
                        kind=kind,
                        source_key=source_key,
                        source_label=source_label,
                        status=status,
                        scheduled_for=scheduled_for,
                    )
                except ValueError as validation_error:
                    messages.error(request, str(validation_error))
                else:
                    messages.success(request, f'Status sadržaja „{source_label}” je spremljen.')
            return redirect('pastoral:page', page=page)

        if page == 'web-stranica' and action == 'upload_website_media':
            website = website_for(parish_data_service.parish)
            kind = request.POST.get('media_kind', '')
            prefix = 'hero' if kind == ParishWebsiteMedia.Kind.HERO else 'gallery'
            form = ParishWebsiteMediaForm(request.POST, request.FILES, prefix=prefix)
            if website and form.is_valid():
                try:
                    save_website_media(
                        website=website,
                        actor=request.user,
                        kind=kind,
                        uploaded=form.cleaned_data['image'],
                        alt_text=form.cleaned_data['alt_text'],
                        caption=form.cleaned_data['caption'],
                    )
                except ValueError as validation_error:
                    messages.error(request, str(validation_error))
                else:
                    messages.success(request, 'Fotografija je optimizirana i spremljena.')
            else:
                error_text = ' '.join(
                    error
                    for errors in form.errors.values()
                    for error in errors
                )
                messages.error(request, error_text or 'Fotografija nije mogla biti spremljena.')
            return redirect('pastoral:page', page=page)

        if page == 'web-stranica' and action == 'delete_website_media':
            website = website_for(parish_data_service.parish)
            try:
                media_id = uuid.UUID(request.POST.get('media_id', ''))
            except (ValueError, TypeError, AttributeError):
                media_id = None
            if website and media_id and delete_website_media(
                website=website,
                actor=request.user,
                media_id=media_id,
            ):
                messages.success(request, 'Fotografija je uklonjena.')
            else:
                messages.error(request, 'Fotografija nije pronađena.')
            return redirect('pastoral:page', page=page)

        if page == 'web-stranica' and action == 'publish_demo_website':
            website = website_for(parish_data_service.parish)
            if website and website.status != ParishWebsite.Status.PROVISIONING:
                publish_demo_website(website=website, actor=request.user)
                messages.success(request, 'Demo web-stranica je objavljena.')
            return redirect('pastoral:page', page=page)

        if page == 'web-stranica' and action == 'reset_demo_website':
            reset_demo_website(parish=parish_data_service.parish, actor=request.user)
            messages.success(request, 'Demo web-stranica vraćena je na početak aktivacije.')
            return redirect('pastoral:page', page=page)

        if action == 'preview_document' and page in ('formulari', 'potvrde', 'dokumenti'):
            template_id = request.POST.get('template_id', '')
            document_template = get_template(template_id)
            query_parameters = {'tpl': template_id, 'preview': '1'}
            if document_template:
                for field_name in document_template.get('fields') or []:
                    field_value = request.POST.get(f'field_{field_name}', '')
                    if field_value:
                        query_parameters[field_name] = field_value
            return redirect(f'{request.path}?{urlencode(query_parameters)}')

        if action == 'upload_doc_csv' and page == 'dokumenti':
            uploaded = request.FILES.get('csv_file')
            template_id = request.POST.get('template_id', '')
            if uploaded and template_id:
                column_names, imported_rows = parse_csv_upload(uploaded)
                request.session['doc_import'] = {
                    'templateId': template_id,
                    'fileName': uploaded.name,
                    'columns': column_names,
                    'rows': imported_rows,
                }
                messages.success(
                    request,
                    f'Učitano {len(imported_rows)} redova iz {uploaded.name}.',
                )
            else:
                messages.error(request, 'Odaberite CSV datoteku i predložak.')
            return redirect(f"{reverse('pastoral:page', kwargs={'page': page})}?tpl={template_id}")

        if action == 'print_doc_row' and page == 'dokumenti':
            template_id = request.POST.get('template_id', '')
            document_template = get_template(template_id)
            if not document_template:
                messages.error(request, 'Predložak nije pronađen.')
                return redirect(request.get_full_path())
            import_data = request.session.get('doc_import') or {}
            imported_rows = import_data.get('rows') or []
            try:
                selected_row_index = int(request.POST.get('row_index', 0))
            except ValueError:
                selected_row_index = 0
            if selected_row_index < 0 or selected_row_index >= len(imported_rows):
                messages.error(request, 'Red nije pronađen.')
                return redirect(request.get_full_path())
            mapping = {}
            for key in request.POST:
                if key.startswith('map_'):
                    mapping[key[4:]] = request.POST.get(key, '')
            if not mapping:
                binding_id = request.POST.get('binding_id')
                if binding_id:
                    binding = next(
                        (
                            document_binding
                            for document_binding in parish_data_service.load().get(
                                'docBindings',
                                [],
                            )
                            if document_binding.get('id') == binding_id
                        ),
                        None,
                    )
                    if binding:
                        mapping = binding.get('mapping', {})
            document_settings = parish_data_service.load_settings()
            rendered_document = render_row_html(
                template_id,
                imported_rows[selected_row_index],
                mapping,
                parish_doc_defaults(document_settings),
            )
            document_context = _document_print_context(
                document_template=document_template,
                rendered_document=rendered_document,
                parish_settings=document_settings,
                document_defaults=parish_doc_defaults(document_settings),
            )
            return render(
                request,
                'pastoral/document_print.html',
                document_context,
            )

        if action == 'print_document' and page in ('formulari', 'potvrde', 'dokumenti'):
            return _document_print_response(request, parish_data_service)

        parish_data = parish_data_service.load()

        if handle_page_post(request, page, parish_data_service):
            return redirect(request.get_full_path())

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

        if action == 'save_settings' and page == 'postavke':
            form = ParishSettingsForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                parish_data_service.save_settings({
                    'name': cleaned_data['name'],
                    'shortName': cleaned_data.get('short_name') or cleaned_data['name'],
                    'city': cleaned_data['city'],
                    'diocese': cleaned_data['diocese'],
                    'pastor': cleaned_data['pastor'],
                    'phone': cleaned_data.get('phone', ''),
                    'email': cleaned_data.get('email', ''),
                    'primaryColor': cleaned_data.get('primary_color') or '#5c2e3a',
                    'accentColor': cleaned_data.get('accent_color') or '#b8922a',
                    'logoUrl': cleaned_data.get('logo_url') or '',
                })
                messages.success(request, 'Postavke spremljene.')
            return redirect('pastoral:page', page=page)

        if action == 'reset_demo' and page == 'postavke':
            parish_data_service.reset_demo()
            messages.success(request, 'Demo podaci vraćeni.')
            return redirect('pastoral:page', page=page)

    page_context = _build_admin_page_context(
        request,
        page,
        parish_data_service,
    )
    template_name = PAGE_TEMPLATE_NAMES.get(
        page,
        'pastoral/pages/generic_table.html',
    )
    return render(request, template_name, page_context)


def public_index_view(request):
    parish_data_service = ParishDataService()
    parish_settings = parish_data_service.load_settings()
    return render(request, 'pastoral/public/index.html', {
        'parish_settings': parish_settings,
    })


@require_http_methods(['GET', 'POST'])
def public_form_view(request, form: str):
    if form not in PUBLIC_FORMS:
        from django.http import Http404
        raise Http404()

    parish_data_service = ParishDataService()
    parish_settings = parish_data_service.load_settings()
    parish_data = parish_data_service.load()
    streets = parish_data.get('streets', [])

    form_class = PUBLIC_FORM_CLASSES[form]
    form_kwargs = {
        'streets': streets,
        'parish_email': parish_settings.get('email', ''),
        'parish_phone': parish_settings.get('phone', ''),
    }

    if request.method == 'POST':
        bound_form = form_class(request.POST, **form_kwargs)
        if bound_form.is_valid():
            submission_payload = build_submission_payload(form, bound_form)
            parish_data = parish_data_service.load()
            submission_payload['id'] = f'ps_{uuid.uuid4().hex[:8]}'
            parish_data.setdefault('publicSubmissions', []).insert(
                0,
                submission_payload,
            )
            parish_data_service.save(parish_data)

            email_was_sent, email_result = dispatch_public_submission_email(
                form,
                submission_payload,
            )
            if email_was_sent:
                messages.success(
                    request,
                    'Prijava je zaprimljena. Župni ured će vas kontaktirati na navedeni telefon.',
                )
            else:
                error_detail = (
                    email_result.get('detail')
                    or email_result.get('error', 'mail_failed')
                )
                messages.warning(
                    request,
                    'Prijava je spremljena, ali e-mail obavijest nije poslana '
                    f'({error_detail}). '
                    'Molimo nazovite župni ured.',
                )
            return redirect('pastoral:public_index')
    else:
        bound_form = form_class(**form_kwargs)

    return render(request, 'pastoral/public/form.html', {
        'form_slug': form,
        'form_title': PUBLIC_FORM_LABELS.get(form, form),
        'form_intro': PUBLIC_FORM_INTROS.get(form, ''),
        'form': bound_form,
        'parish_settings': parish_settings,
        'street_not_listed': '__other__',
    })


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
