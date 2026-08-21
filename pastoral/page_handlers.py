from pastoral.services.data import ParishDataService
from pastoral.services.dashboard import build_dashboard_context
from pastoral.services.cashbook import cashbook_page_context
from pastoral.services.debts import debts_page_context
from pastoral.services.documents_page import documents_page_context
from pastoral.services.finance_reports import finance_reports_context
from pastoral.services.invoices_page import invoices_page_context
from pastoral.services.kalendar import calendar_page_context
from pastoral.services.nakane import nakane_page_context
from pastoral.services.public_submissions_page import public_submissions_context
from pastoral.services.registry_books import registry_books_page_context
from pastoral.services.streets import streets_page_context
from pastoral.services.visits_page import visits_page_context
from pastoral.services.zupni_listic import (
    load_config,
    migrate_listic_data,
    zupni_listic_page_context,
)
from pastoral.services.sacraments import (
    anointing_context,
    baptisms_context,
    families_page_context,
    first_communion_page_context,
    funerals_context,
    krizma_page_context,
    weddings_context,
)


PAGE_META = {
    'podsjetnici': ('Podsjetnici', 'Inbox obaveza župnog ureda'),
    'obitelji': ('Obitelji', 'Karton domaćinstva — članovi, sakramenti, lukno i pastoralne bilješke'),
    'ulice': ('Ulice i kvartovi', 'Popis ulica župe — obitelji po adresi za obilazak'),
    'nakane': ('Kalendar misnih nakana', 'Upis nakan po danu i misi'),
    'mise': ('Raspored misa', 'Stalni termini i veza na misne nakane'),
    'zupni-listic': (
        'Župni listić', ''
    ),
    'krsenja': ('Krštenja', 'Matična evidencija krštenja'),
    'prva-pricest': ('Prva pričest', 'Evidencija prvopričesnika — škola, roditelji, plaćanje'),
    'krizma': ('Krizma', 'Evidencija krizmanika — godina, priprema'),
    'vjencanja': ('Vjenčanja', 'Mladoženja, mlada, kumovi, datum i svećenik'),
    'pogrebi': ('Pogrebi', 'Pokojnik, misa, groblje, svećenik i naknada'),
    'pomazanje': ('Pomazanje', 'Tko, kada i gdje — bolesničko pomazanje'),
    'dugovanja': ('Dugovanja', 'Prema župi i dugovanja župe'),
    'racuni': ('Ulazni računi', 'Evidencija računa dobavljača'),
    'blagajna': ('Blagajna', 'Plavi i crveni dnevnik'),
    'financijska-izvjestaja': ('Financijski pregled', 'Prihodi, rashodi i otvorene obveze'),
    'potvrde': ('Dokumenti i potvrde', 'Pronađite zapis, odaberite dokument i ispišite ga'),
    'maticne-knjige': ('Matične knjige', 'Pregled knjiga u župi'),
    'vijeca': ('Vijeća ŽPV/ŽEV', 'Članovi i sastanci'),
    'kalendar': ('Događaji i zadaci', 'Župni kalendar, liturgija i obaveze ureda'),
    'javne-prijave': ('Javne prijave', 'Prijave s weba'),
    'postavke': ('Postavke', 'Naziv župe, logo, boje'),
    'posjete': ('Posjete', 'Pastoralni posjeti obiteljima i bolesnicima'),
}


def page_title_subtitle(slug: str) -> tuple[str, str]:
    return PAGE_META.get(slug, (slug.replace('-', ' ').title(), ''))


def dashboard_context(request, parish_data_service: ParishDataService) -> dict:
    return build_dashboard_context(parish_data_service)


def build_page_context(request, page_slug: str) -> dict:
    parish_data_service = ParishDataService()
    page_title, page_subtitle = page_title_subtitle(page_slug)
    page_context = {
        'page_slug': page_slug,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
    parish_data = parish_data_service.load()
    page_context['baptism_data_source'] = 'relational'
    if page_slug == 'nakane':
        page_context.update(nakane_page_context(parish_data, request))
        page_context['nakane_bootstrap']['defaultStipend'] = float(
            parish_data_service.load_settings().get(
                'defaultMassIntentionStipend', 0
            ) or 0
        )
    elif page_slug == 'mise':
        from pastoral.services.mass_schedule import migrate_mass_schedule
        migrate_mass_schedule(parish_data)
        page_context['mise_bootstrap'] = {
            'massSchedule': parish_data.get('massSchedule', []),
            'massExceptions': parish_data.get('massExceptions', []),
            'intentions': parish_data.get('intentions', []),
            'defaultStipend': float(
                parish_data_service.load_settings().get(
                    'defaultMassIntentionStipend', 0
                ) or 0
            ),
        }
    elif page_slug == 'zupni-listic':
        parish_settings = parish_data_service.load_settings()
        migrate_listic_data(parish_data)
        page_context.update(
            zupni_listic_page_context(parish_data, parish_settings, request)
        )
        bulletin_configuration = load_config()
        page_context['listic_bootstrap'] = {
            'config': {
                'blockTypes': bulletin_configuration['blockTypes'],
                'defaultLayout': bulletin_configuration['defaultLayout'],
            },
            'editLayout': page_context['listic_edit_layout'],
            'savedLayout': page_context['listic_layout'],
        }
    elif page_slug == 'obitelji':
        page_context.update(families_page_context(parish_data, request))
    elif page_slug == 'krizma':
        page_context.update(krizma_page_context(parish_data, request))
    elif page_slug == 'prva-pricest':
        page_context.update(first_communion_page_context(parish_data, request))
    elif page_slug == 'krsenja':
        page_context.update(baptisms_context(parish_data, request))
    elif page_slug == 'vjencanja':
        page_context.update(weddings_context(parish_data, request))
    elif page_slug == 'pogrebi':
        page_context.update(funerals_context(parish_data, request))
    elif page_slug == 'pomazanje':
        page_context.update(anointing_context(parish_data, request))
    elif page_slug == 'dugovanja':
        page_context.update(debts_page_context(parish_data, request))
    elif page_slug == 'vijeca':
        pastoral_council = parish_data.get('pastoralCouncil', {})
        economic_council = parish_data.get('economicCouncil', {})
        selected_council_type = request.GET.get('council', 'pastoral')
        if selected_council_type not in {'pastoral', 'economic'}:
            selected_council_type = 'pastoral'
        selected_council = (
            economic_council
            if selected_council_type == 'economic'
            else pastoral_council
        )
        selected_member_identifier = request.GET.get('member', '')
        selected_council_member = next(
            (
                council_member
                for council_member in selected_council.get('members', [])
                if council_member.get('id') == selected_member_identifier
            ),
            None,
        )
        page_context.update({
            'pastoral_council': pastoral_council,
            'economic_council': economic_council,
            'selected_council_type': selected_council_type,
            'selected_council_member': selected_council_member,
            'council_member_form_mode': (
                'add'
                if selected_member_identifier == 'new'
                else 'edit'
                if selected_council_member
                else ''
            ),
            'council_meeting_dialog_open': (
                request.GET.get('meeting') == '1'
            ),
            'pastoral_confirmed_member_count': sum(
                bool(council_member.get('confirmed'))
                for council_member in pastoral_council.get('members', [])
            ),
            'economic_confirmed_member_count': sum(
                bool(council_member.get('confirmed'))
                for council_member in economic_council.get('members', [])
            ),
        })
    elif page_slug == 'podsjetnici':
        all_reminders = parish_data_service.collect_reminders()
        selected_priority = request.GET.get('priority', 'all')
        selected_category = request.GET.get('category', 'all')
        search_term = request.GET.get('search', '').strip().casefold()

        visible_reminders = [
            reminder
            for reminder in all_reminders
            if (
                selected_priority == 'all'
                or reminder.get('priority') == selected_priority
            )
            and (
                selected_category == 'all'
                or reminder.get('category') == selected_category
            )
            and (
                not search_term
                or search_term in ' '.join((
                    str(reminder.get('title') or ''),
                    str(reminder.get('sub') or ''),
                    str(reminder.get('category') or ''),
                )).casefold()
            )
        ]
        page_context.update({
            'reminders': visible_reminders,
            'reminder_count': len(all_reminders),
            'high_priority_reminder_count': sum(
                reminder.get('priority') == 'visoka'
                for reminder in all_reminders
            ),
            'reminder_categories': sorted({
                reminder.get('category')
                for reminder in all_reminders
                if reminder.get('category')
            }),
            'selected_reminder_priority': selected_priority,
            'selected_reminder_category': selected_category,
            'reminder_search_term': request.GET.get('search', '').strip(),
        })
    elif page_slug == 'postavke':
        page_context['settings'] = parish_data_service.load_settings()
        page_context['parish_decree'] = parish_data.get('parishDecree', {})
    elif page_slug == 'ulice':
        page_context.update(streets_page_context(
            parish_data,
            request,
            parish_data_service.load_settings(),
        ))
    elif page_slug == 'blagajna':
        page_context.update(cashbook_page_context(parish_data, request))
    elif page_slug == 'racuni':
        page_context.update(invoices_page_context(parish_data, request))
    elif page_slug == 'javne-prijave':
        page_context.update(public_submissions_context(parish_data, request))
    elif page_slug == 'financijska-izvjestaja':
        page_context.update(finance_reports_context(parish_data, request))
    elif page_slug == 'kalendar':
        page_context.update(calendar_page_context(parish_data, request))
    elif page_slug == 'potvrde':
        page_context.update(
            documents_page_context(
                parish_data,
                parish_data_service.load_settings(),
                request,
            )
        )
    elif page_slug == 'maticne-knjige':
        page_context.update(registry_books_page_context(parish_data, request))
    elif page_slug == 'posjete':
        page_context.update(visits_page_context(parish_data, request))
    elif page_slug == 'dekanat':
        from phase_two.interparish_collaboration.services import (
            deanery_page_context,
        )

        page_context.update(
            deanery_page_context(
                parish_data,
                request,
                parish_data_service.load_settings(),
            )
        )
    elif page_slug == 'operativno-srediste':
        from phase_two.operations_center.services import (
            operations_page_context,
        )

        page_context.update(operations_page_context(parish_data, request))
    return page_context
