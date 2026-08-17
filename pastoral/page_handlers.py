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
from pastoral.services.streets import streets_page_context
from pastoral.services.visits_page import visits_page_context
from pastoral.services.zupni_listic import (
    load_config,
    migrate_listic_data,
    zupni_listic_page_context,
)
from pastoral.services.deanery import deanery_page_context
from pastoral.services.operations import operations_page_context
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
    'mise': ('Raspored misa', 'Stalni termini, iznimke i veza na misne nakane'),
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
    'financijska-izvjestaja': ('Financijska izvješća', 'Kvartalni i godišnji obračun'),
    'formulari': ('Formulari', 'Katalog ispisnica'),
    'potvrde': ('Potvrde', 'Ispis isprava iz evidencije'),
    'dokumenti': ('Dokumenti', 'Predlošci i serijski ispis'),
    'maticne-knjige': ('Matične knjige', 'Pregled knjiga u župi'),
    'vijeca': ('Vijeća ŽPV/ŽEV', 'Članovi i sastanci'),
    'kalendar': ('Događaji i zadaci', 'Župni kalendar, liturgija i obaveze ureda'),
    'javne-prijave': ('Javne prijave', 'Prijave s weba'),
    'postavke': ('Postavke', 'Naziv župe, logo, boje'),
    'web-stranica': (
        'Javna web-stranica',
        'Aktivacija, izrada i objava stranice župe',
    ),
    'posjete': ('Posjete', 'Pastoralni posjeti obiteljima i bolesnicima'),
    'dekanat': ('Dekanat i suradnja', 'Sigurni zahtjevi, potvrde i koordinacija između župa'),
    'operativno-srediste': (
        'Operativno središte',
        'Jedinstveni radni red: uredska pošta, ljudi, prostori, imovina, kontrole i komunikacija',
    ),
}


def page_title_subtitle(slug: str) -> tuple[str, str]:
    return PAGE_META.get(slug, (slug.replace('-', ' ').title(), ''))


def dashboard_context(request, parish_data_service: ParishDataService) -> dict:
    return build_dashboard_context(parish_data_service)


def generic_table_context(
    request,
    parish_data_service: ParishDataService,
    page_slug: str,
) -> dict:
    parish_data = parish_data_service.load()
    page_context = {'data': parish_data}
    if page_slug == 'kalendar':
        page_context['parish_events'] = parish_data.get('events', [])
        page_context['rows'] = parish_data.get('tasks', [])
    elif page_slug == 'pomazanje':
        page_context['rows'] = parish_data.get('anointing', [])
        page_context['columns'] = [
            ('person', 'Osoba'),
            ('address', 'Adresa'),
            ('scheduled', 'Datum'),
            ('priest', 'Svećenik'),
            ('done', 'Obavljeno'),
        ]
    elif page_slug == 'krsenja':
        page_context['rows'] = parish_data.get('baptisms', [])
        page_context['columns'] = [
            ('childName', 'Dijete'),
            ('baptismDate', 'Datum'),
            ('parents', 'Roditelji'),
            ('status', 'Status'),
            ('stipendPaid', 'Stipendij'),
        ]
    elif page_slug == 'vjencanja':
        page_context['rows'] = parish_data.get('weddings', [])
        page_context['columns'] = [
            ('couple', 'Par'),
            ('weddingDate', 'Datum'),
            ('status', 'Status'),
            ('stipendPaid', 'Stipendij'),
        ]
    elif page_slug == 'pogrebi':
        page_context['rows'] = parish_data.get('funerals', [])
        page_context['columns'] = [
            ('deceased', 'Pokojnik'),
            ('funeralDate', 'Datum'),
            ('cemetery', 'Groblje'),
            ('status', 'Status'),
        ]
    elif page_slug == 'ulice':
        page_context['rows'] = parish_data.get('streets', [])
        page_context['columns'] = [
            ('name', 'Ulica'),
            ('zone', 'Zona'),
            ('sortOrder', 'Red'),
        ]
    elif page_slug == 'dugovanja':
        page_context['rows'] = parish_data.get('parishDebts', [])
        page_context['columns'] = [
            ('label', 'Opis'),
            ('category', 'Kategorija'),
            ('amount', 'Iznos'),
            ('paid', 'Plaćeno'),
            ('dueDate', 'Rok'),
        ]
    elif page_slug == 'racuni':
        page_context['rows'] = [
            invoice
            for invoice in parish_data.get('invoices', [])
            if invoice.get('direction') != 'outgoing'
        ]
        page_context['columns'] = [
            ('number', 'Broj'),
            ('supplierName', 'Dobavljač'),
            ('total', 'Iznos'),
            ('status', 'Status'),
            ('dueDate', 'Rok'),
        ]
    elif page_slug == 'blagajna':
        page_context['rows'] = parish_data.get('cashbook', [])
        page_context['columns'] = [
            ('date', 'Datum'),
            ('type', 'Smjer'),
            ('description', 'Opis'),
            ('amount', 'Iznos'),
            ('ledger', 'Dnevnik'),
        ]
    elif page_slug == 'maticne-knjige':
        page_context['rows'] = parish_data.get('registryBooks', [])
        page_context['columns'] = [
            ('title', 'Knjiga'),
            ('type', 'Vrsta'),
            ('lastNo', 'Zadnji broj'),
            ('status', 'Status'),
        ]
    elif page_slug == 'javne-prijave':
        page_context['rows'] = parish_data.get('publicSubmissions', [])
        page_context['columns'] = [
            ('formType', 'Obrazac'),
            ('submittedAt', 'Datum'),
            ('name', 'Ime'),
            ('status', 'Status'),
        ]
    else:
        page_context['rows'] = []
        page_context['columns'] = []
    return page_context


def build_page_context(request, page_slug: str) -> dict:
    parish_data_service = ParishDataService()
    page_title, page_subtitle = page_title_subtitle(page_slug)
    page_context = {
        'page_slug': page_slug,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
    parish_data = parish_data_service.load()
    if page_slug == 'nakane':
        page_context.update(nakane_page_context(parish_data, request))
    elif page_slug == 'mise':
        from pastoral.services.mass_schedule import migrate_mass_schedule
        migrate_mass_schedule(parish_data)
        page_context['mise_bootstrap'] = {
            'massSchedule': parish_data.get('massSchedule', []),
            'massExceptions': parish_data.get('massExceptions', []),
            'massScheduleLog': parish_data.get('massScheduleLog', []),
            'intentions': parish_data.get('intentions', []),
        }
    elif page_slug == 'zupni-listic':
        parish_settings = parish_data_service.load_settings()
        had_saved_layout = bool(parish_data.get('zupniListicLayout', {}).get('blocks'))
        migrate_listic_data(parish_data)
        if not had_saved_layout and parish_data.get('zupniListicLayout', {}).get('blocks'):
            parish_data_service.save(parish_data)
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
        page_context['pastoral_council'] = parish_data.get('pastoralCouncil', {})
        page_context['economic_council'] = parish_data.get('economicCouncil', {})
    elif page_slug == 'podsjetnici':
        page_context['reminders'] = parish_data_service.collect_reminders()
    elif page_slug == 'postavke':
        page_context['settings'] = parish_data_service.load_settings()
        page_context['parish_decree'] = parish_data.get('parishDecree', {})
    elif page_slug == 'web-stranica':
        page_context['settings'] = parish_data_service.load_settings()
    elif page_slug == 'ulice':
        page_context.update(streets_page_context(parish_data, request))
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
    elif page_slug in {'formulari', 'potvrde', 'dokumenti'}:
        page_context.update(
            documents_page_context(
                parish_data,
                parish_data_service.load_settings(),
                request,
                page_slug,
            )
        )
    elif page_slug == 'maticne-knjige':
        page_context['registry_books'] = parish_data.get('registryBooks', [])
    elif page_slug == 'posjete':
        page_context.update(visits_page_context(parish_data, request))
    elif page_slug == 'dekanat':
        page_context.update(
            deanery_page_context(
                parish_data,
                request,
                parish_data_service.load_settings(),
            )
        )
    elif page_slug == 'operativno-srediste':
        page_context.update(operations_page_context(parish_data, request))
    else:
        page_context.update(
            generic_table_context(request, parish_data_service, page_slug)
        )
    return page_context
