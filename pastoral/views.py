import json
import uuid

from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from users.models import User

from .decorators import pastoral_login_required
from .actions import handle_page_post
from .forms import (
    AnointingForm,
    BaptismForm,
    CashbookEntryForm,
    FuneralForm,
    IntentionForm,
    InvoiceForm,
    LoginForm,
    OtpVerifyForm,
    ParishDebtForm,
    PUBLIC_FORM_CLASSES,
    PUBLIC_FORM_INTROS,
    ParishSettingsForm,
    RegistryBookForm,
    StreetForm,
    TaskForm,
    VisitForm,
    WeddingForm,
)
from .models import OtpChallenge
from .page_handlers import build_page_context, dashboard_context, page_title_subtitle
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


def _document_print_response(request, svc: ParishDataService):
    template_id = request.POST.get('template_id', '')
    tpl = get_template(template_id)
    if not tpl:
        messages.error(request, 'Predložak nije pronađen.')
        return redirect(request.get_full_path())

    data = svc.load()
    settings = svc.load_settings()
    values = build_field_values(request, tpl, parish_doc_defaults(settings))
    if template_id == 'raspored_nakana':
        values['tablica_nakana'] = intentions_table_html(data, values.get('tjedan_od', ''))

    html = render_template(template_id, values)
    return render(request, 'pastoral/document_print.html', {
        'doc_html': html,
        'doc_title': tpl.get('name', 'Ispis'),
    })

ADMIN_PAGES = {
     'blagajna', 'dokumenti', 'dugovanja', 'financijska-izvjestaja',
    'formulari', 'javne-prijave', 'kalendar', 'krizma',
    'krsenja', 'maticne-knjige', 'mise', 'nakane', 'obitelji', 'pogrebi', 'pomazanje',
    'posjete', 'postavke', 'potvrde', 'prva-pricest', 'racuni',
     'ulice', 'vijeca', 'vjencanja', 'zupni-listic', 'podsjetnici',
}

REMOVED_PAGE_REDIRECTS = {
    'zadaci': 'kalendar',
    'poruke': 'dashboard',
    'korisnici': 'dashboard',
    'sigurnost': 'dashboard',
    'komunikacija': 'zupni-listic',
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
        role = form.cleaned_data['role']
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
    svc = ParishDataService()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_task':
            task_id = request.POST.get('task_id')
            data = svc.load()
            for t in data.get('tasks', []):
                if t.get('id') == task_id:
                    t['done'] = not t.get('done')
            svc.save(data)
            return redirect('pastoral:page', page='kalendar')
    ctx = dashboard_context(request, svc)
    ctx['page_title'] = 'Početna'
    ctx['page_subtitle'] = 'Što danas radite u župi'
    ctx['current_page'] = 'dashboard'
    return render(request, 'pastoral/dashboard.html', ctx)


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

    svc = ParishDataService()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'preview_document' and page in ('formulari', 'potvrde', 'dokumenti'):
            template_id = request.POST.get('template_id', '')
            tpl = get_template(template_id)
            qs = {'tpl': template_id, 'preview': '1'}
            if tpl:
                for field in tpl.get('fields') or []:
                    val = request.POST.get(f'field_{field}', '')
                    if val:
                        qs[field] = val
            return redirect(f'{request.path}?{urlencode(qs)}')

        if action == 'upload_doc_csv' and page == 'dokumenti':
            uploaded = request.FILES.get('csv_file')
            template_id = request.POST.get('template_id', '')
            if uploaded and template_id:
                cols, rows = parse_csv_upload(uploaded)
                request.session['doc_import'] = {
                    'templateId': template_id,
                    'fileName': uploaded.name,
                    'columns': cols,
                    'rows': rows,
                }
                messages.success(request, f'Učitano {len(rows)} redova iz {uploaded.name}.')
            else:
                messages.error(request, 'Odaberite CSV datoteku i predložak.')
            return redirect(f"{reverse('pastoral:page', kwargs={'page': page})}?tpl={template_id}")

        if action == 'print_doc_row' and page == 'dokumenti':
            template_id = request.POST.get('template_id', '')
            tpl = get_template(template_id)
            if not tpl:
                messages.error(request, 'Predložak nije pronađen.')
                return redirect(request.get_full_path())
            import_data = request.session.get('doc_import') or {}
            rows = import_data.get('rows') or []
            try:
                row_idx = int(request.POST.get('row_index', 0))
            except ValueError:
                row_idx = 0
            if row_idx < 0 or row_idx >= len(rows):
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
                        (b for b in svc.load().get('docBindings', []) if b.get('id') == binding_id),
                        None,
                    )
                    if binding:
                        mapping = binding.get('mapping', {})
            settings = svc.load_settings()
            html = render_row_html(template_id, rows[row_idx], mapping, parish_doc_defaults(settings))
            return render(request, 'pastoral/document_print.html', {
                'doc_html': html,
                'doc_title': tpl.get('name', 'Ispis'),
            })

        if action == 'print_document' and page in ('formulari', 'potvrde', 'dokumenti'):
            return _document_print_response(request, svc)

        data = svc.load()

        if handle_page_post(request, page, svc):
            return redirect(request.get_full_path())

        if action == 'add_task' and page == 'kalendar':
            form = TaskForm(request.POST)
            if form.is_valid():
                data.setdefault('tasks', []).append({
                    'id': f't_{uuid.uuid4().hex[:8]}',
                    'title': form.cleaned_data['title'],
                    'due': form.cleaned_data['due'].isoformat() if form.cleaned_data.get('due') else '',
                    'priority': form.cleaned_data['priority'],
                    'category': form.cleaned_data.get('category') or 'ured',
                    'done': False,
                })
                svc.save(data)
                messages.success(request, 'Zadatak dodan.')
            return redirect('pastoral:page', page=page)

        if action == 'toggle_task' and page == 'kalendar':
            task_id = request.POST.get('task_id')
            for t in data.get('tasks', []):
                if t.get('id') == task_id:
                    t['done'] = not t.get('done')
            svc.save(data)
            return redirect('pastoral:page', page=page)

        if action == 'save_settings' and page == 'postavke':
            form = ParishSettingsForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                svc.save_settings({
                    'name': cd['name'],
                    'shortName': cd.get('short_name') or cd['name'],
                    'city': cd['city'],
                    'diocese': cd['diocese'],
                    'pastor': cd['pastor'],
                    'phone': cd.get('phone', ''),
                    'email': cd.get('email', ''),
                    'primaryColor': cd.get('primary_color') or '#5c2e3a',
                    'accentColor': cd.get('accent_color') or '#b8922a',
                    'logoUrl': cd.get('logo_url') or '',
                })
                messages.success(request, 'Postavke spremljene.')
            return redirect('pastoral:page', page=page)

        if action == 'reset_demo' and page == 'postavke':
            svc.reset_demo()
            messages.success(request, 'Demo podaci vraćeni.')
            return redirect('pastoral:page', page=page)

    ctx = build_page_context(request, page)
    ctx['current_page'] = page

    template_map = {
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
    }
    template = template_map.get(page, 'pastoral/pages/generic_table.html')

    if page == 'kalendar':
        ctx['task_form'] = TaskForm()
    if page == 'nakane':
        ctx['intention_form'] = IntentionForm(initial={'date': svc.today_iso()})
    if page == 'dugovanja':
        ctx['debt_form'] = ParishDebtForm()
    if page == 'krsenja':
        ctx['baptism_form'] = BaptismForm()
    if page == 'vjencanja':
        ctx['wedding_form'] = WeddingForm()
    if page == 'pogrebi':
        ctx['funeral_form'] = FuneralForm()
    if page == 'pomazanje':
        ctx['anointing_form'] = AnointingForm()
    if page == 'postavke':
        s = ctx.get('settings', {})
        ctx['settings_form'] = ParishSettingsForm(initial={
            'name': s.get('name'),
            'short_name': s.get('shortName'),
            'city': s.get('city'),
            'diocese': s.get('diocese'),
            'pastor': s.get('pastor'),
            'phone': s.get('phone'),
            'email': s.get('email'),
            'primary_color': s.get('primaryColor'),
            'accent_color': s.get('accentColor'),
            'logo_url': s.get('logoUrl', ''),
        })
    if page == 'ulice':
        selected = ctx.get('selected_street')
        if ctx.get('street_form_mode') == 'edit' and selected:
            ctx['street_form'] = StreetForm(initial={
                'name': selected.get('name', ''),
                'zone': selected.get('zone', ''),
                'notes': selected.get('notes', ''),
            })
        else:
            ctx['street_form'] = StreetForm()
    if page == 'blagajna':
        ctx['cashbook_form'] = CashbookEntryForm(initial={'date': svc.today_iso()})
    if page == 'racuni':
        ctx['invoice_form'] = InvoiceForm()
    if page == 'posjete':
        ctx['visit_form'] = VisitForm(initial={'scheduled': svc.today_iso()})
        visit_id = request.GET.get('visit')
        if visit_id:
            visit = next((v for v in svc.load().get('visits', []) if v.get('id') == visit_id), None)
            if visit:
                ctx['selected_visit'] = visit
                ctx['visit_form'] = VisitForm(initial={
                    'scheduled': visit.get('scheduled'),
                    'person': visit.get('person', ''),
                    'visit_type': visit.get('type', 'obitelj'),
                    'address': visit.get('address', ''),
                    'priest': visit.get('priest', ''),
                    'purpose': visit.get('purpose', ''),
                    'family_id': visit.get('familyId', ''),
                    'report': visit.get('report', ''),
                })
    
    if page == 'maticne-knjige':
        ctx['book_form'] = RegistryBookForm()
        book_id = request.GET.get('book')
        if book_id:
            book = next((b for b in svc.load().get('registryBooks', []) if b.get('id') == book_id), None)
            if book:
                ctx['selected_book'] = book
                ctx['book_form'] = RegistryBookForm(initial={
                    'title': book.get('title', ''),
                    'book_type': book.get('type', 'krštenja'),
                    'location': book.get('location', ''),
                    'last_entry': book.get('lastEntry') or None,
                    'last_no': book.get('lastNo', ''),
                    'custodian': book.get('custodian', ''),
                    'status': book.get('status', 'u župi'),
                    'notes': book.get('notes', ''),
                })

    return render(request, template, ctx)


def public_index_view(request):
    svc = ParishDataService()
    settings_data = svc.load_settings()
    return render(request, 'pastoral/public/index.html', {
        'parish_settings': settings_data,
    })


@require_http_methods(['GET', 'POST'])
def public_form_view(request, form: str):
    if form not in PUBLIC_FORMS:
        from django.http import Http404
        raise Http404()

    svc = ParishDataService()
    parish_settings = svc.load_settings()
    parish_data = svc.load()
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
            payload = build_submission_payload(form, bound_form)
            data = svc.load()
            payload['id'] = f'ps_{uuid.uuid4().hex[:8]}'
            data.setdefault('publicSubmissions', []).insert(0, payload)
            svc.save(data)

            mail_ok, mail_result = dispatch_public_submission_email(form, payload)
            if mail_ok:
                messages.success(
                    request,
                    'Prijava je zaprimljena. Župni ured će vas kontaktirati na navedeni telefon.',
                )
            else:
                detail = mail_result.get('detail') or mail_result.get('error', 'mail_failed')
                messages.warning(
                    request,
                    f'Prijava je spremljena, ali e-mail obavijest nije poslana ({detail}). '
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

    svc = ParishDataService()
    settings = svc.load_settings()
    for key in (
        'primaryColor', 'accentColor', 'bgColor', 'bgPatternColor',
        'themePresetId', 'customTheme', 'colorScheme',
    ):
        if key in payload:
            settings[key] = payload[key]
    svc.save_settings(settings)
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
