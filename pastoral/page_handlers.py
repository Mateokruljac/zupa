from datetime import date

from pastoral.services.data import ParishDataService
from pastoral.services.liturgical import LiturgicalService
from pastoral.services.cashbook import cashbook_page_context
from pastoral.services.debts import debts_page_context
from pastoral.services.documents_page import documents_page_context
from pastoral.services.finance_reports import finance_reports_context
from pastoral.services.invoices_page import invoices_page_context
from pastoral.services.kalendar import kalendar_page_context
from pastoral.services.nakane import nakane_page_context
from pastoral.services.public_submissions_page import public_submissions_context
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


def _svc(request):
    return ParishDataService()


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
    'posjete': ('Posjete', 'Pastoralni posjeti obiteljima i bolesnicima'),
}


def page_title_subtitle(slug: str) -> tuple[str, str]:
    return PAGE_META.get(slug, (slug.replace('-', ' ').title(), ''))


def dashboard_context(request, svc: ParishDataService) -> dict:
    data = svc.load()
    today = svc.today_iso()
    stats = svc.office_stats(data)
    intentions_today = [n for n in data.get('intentions', []) if n.get('date') == today]
    open_tasks = sorted(
        [t for t in data.get('tasks', []) if not t.get('done')],
        key=lambda t: t.get('due') or '9999',
    )[:6]
    year = date.today().year
    conf = next((c for c in data.get('confirmations', []) if c.get('year') == year), None)
    conf = conf or (data.get('confirmations') or [{}])[0]
    lukno_unpaid = []
    for fam in data.get('families', []):
        row = next((c for c in fam.get('contributions', []) if c.get('year') == year), None)
        if row and not row.get('luknoPaid'):
            lukno_unpaid.append(fam)
    sacraments = []
    for b in data.get('baptisms', [])[:2]:
        sacraments.append({'type': 'krštenje', 'name': b.get('childName'), 'date': b.get('baptismDate')})
    for w in data.get('weddings', [])[:1]:
        sacraments.append({'type': 'vjenčanje', 'name': w.get('couple'), 'date': w.get('weddingDate')})
    for f in data.get('funerals', [])[:1]:
        sacraments.append({'type': 'pogreb', 'name': f.get('deceased'), 'date': f.get('funeralDate')})
    return {
        'stats': stats,
        'intentions_today': intentions_today,
        'open_tasks': open_tasks,
        'conf_year': conf,
        'lukno_unpaid': lukno_unpaid[:6],
        'sacraments_upcoming': sacraments,
        'reminders': svc.collect_reminders(data)[:8],
        'today': today,
        'liturgical_day': LiturgicalService().get_day(today),
    }


def generic_table_context(request, svc: ParishDataService, slug: str) -> dict:
    data = svc.load()
    ctx = {'data': data}
    if slug == 'kalendar':
        ctx['parish_events'] = data.get('events', [])
        ctx['rows'] = data.get('tasks', [])
    elif slug == 'pomazanje':
        ctx['rows'] = data.get('anointing', [])
        ctx['columns'] = [
            ('person', 'Osoba'),
            ('address', 'Adresa'),
            ('scheduled', 'Datum'),
            ('priest', 'Svećenik'),
            ('done', 'Obavljeno'),
        ]
    elif slug == 'krsenja':
        ctx['rows'] = data.get('baptisms', [])
        ctx['columns'] = [
            ('childName', 'Dijete'),
            ('baptismDate', 'Datum'),
            ('parents', 'Roditelji'),
            ('status', 'Status'),
            ('stipendPaid', 'Stipendij'),
        ]
    elif slug == 'vjencanja':
        ctx['rows'] = data.get('weddings', [])
        ctx['columns'] = [
            ('couple', 'Par'),
            ('weddingDate', 'Datum'),
            ('status', 'Status'),
            ('stipendPaid', 'Stipendij'),
        ]
    elif slug == 'pogrebi':
        ctx['rows'] = data.get('funerals', [])
        ctx['columns'] = [
            ('deceased', 'Pokojnik'),
            ('funeralDate', 'Datum'),
            ('cemetery', 'Groblje'),
            ('status', 'Status'),
        ]
    elif slug == 'ulice':
        ctx['rows'] = data.get('streets', [])
        ctx['columns'] = [
            ('name', 'Ulica'),
            ('zone', 'Zona'),
            ('sortOrder', 'Red'),
        ]
    elif slug == 'dugovanja':
        ctx['rows'] = data.get('parishDebts', [])
        ctx['columns'] = [
            ('label', 'Opis'),
            ('category', 'Kategorija'),
            ('amount', 'Iznos'),
            ('paid', 'Plaćeno'),
            ('dueDate', 'Rok'),
        ]
    elif slug == 'racuni':
        ctx['rows'] = [
            i for i in data.get('invoices', [])
            if i.get('direction') != 'outgoing'
        ]
        ctx['columns'] = [
            ('number', 'Broj'),
            ('supplierName', 'Dobavljač'),
            ('total', 'Iznos'),
            ('status', 'Status'),
            ('dueDate', 'Rok'),
        ]
    elif slug == 'blagajna':
        ctx['rows'] = data.get('cashbook', [])
        ctx['columns'] = [
            ('date', 'Datum'),
            ('type', 'Smjer'),
            ('description', 'Opis'),
            ('amount', 'Iznos'),
            ('ledger', 'Dnevnik'),
        ]
    elif slug == 'maticne-knjige':
        ctx['rows'] = data.get('registryBooks', [])
        ctx['columns'] = [
            ('title', 'Knjiga'),
            ('type', 'Vrsta'),
            ('lastNo', 'Zadnji broj'),
            ('status', 'Status'),
        ]
    elif slug == 'javne-prijave':
        ctx['rows'] = data.get('publicSubmissions', [])
        ctx['columns'] = [
            ('formType', 'Obrazac'),
            ('submittedAt', 'Datum'),
            ('name', 'Ime'),
            ('status', 'Status'),
        ]
    else:
        ctx['rows'] = []
        ctx['columns'] = []
    return ctx


def build_page_context(request, slug: str) -> dict:
    svc = _svc(request)
    title, subtitle = page_title_subtitle(slug)
    ctx = {'page_slug': slug, 'page_title': title, 'page_subtitle': subtitle}
    data = svc.load()
    if slug == 'nakane':
        ctx.update(nakane_page_context(data, request))
    elif slug == 'mise':
        from pastoral.services.mass_schedule import migrate_mass_schedule
        migrate_mass_schedule(data)
        ctx['mise_bootstrap'] = {
            'massSchedule': data.get('massSchedule', []),
            'massExceptions': data.get('massExceptions', []),
            'massScheduleLog': data.get('massScheduleLog', []),
            'intentions': data.get('intentions', []),
        }
    elif slug == 'zupni-listic':
        settings = svc.load_settings()
        had_layout = bool(data.get('zupniListicLayout', {}).get('blocks'))
        migrate_listic_data(data)
        if not had_layout and data.get('zupniListicLayout', {}).get('blocks'):
            svc.save(data)
        ctx.update(zupni_listic_page_context(data, settings, request))
        cfg = load_config()
        ctx['listic_bootstrap'] = {
            'config': {'blockTypes': cfg['blockTypes'], 'defaultLayout': cfg['defaultLayout']},
            'editLayout': ctx['listic_edit_layout'],
            'savedLayout': ctx['listic_layout'],
        }
    elif slug == 'obitelji':
        ctx.update(families_page_context(data, request))
    elif slug == 'krizma':
        ctx.update(krizma_page_context(data, request))
    elif slug == 'prva-pricest':
        ctx.update(first_communion_page_context(data, request))
    elif slug == 'krsenja':
        ctx.update(baptisms_context(data, request))
    elif slug == 'vjencanja':
        ctx.update(weddings_context(data, request))
    elif slug == 'pogrebi':
        ctx.update(funerals_context(data, request))
    elif slug == 'pomazanje':
        ctx.update(anointing_context(data, request))
    elif slug == 'dugovanja':
        ctx.update(debts_page_context(data, request))
    elif slug == 'vijeca':
        data = svc.load()
        ctx['pastoral_council'] = data.get('pastoralCouncil', {})
        ctx['economic_council'] = data.get('economicCouncil', {})
    elif slug == 'podsjetnici':
        ctx['reminders'] = svc.collect_reminders()
    elif slug == 'postavke':
        ctx['settings'] = svc.load_settings()
        ctx['parish_decree'] = svc.load().get('parishDecree', {})
    elif slug == 'ulice':
        ctx.update(streets_page_context(data, request))
    elif slug == 'blagajna':
        ctx.update(cashbook_page_context(data, request))
    elif slug == 'racuni':
        ctx.update(invoices_page_context(data, request))
    elif slug == 'javne-prijave':
        ctx.update(public_submissions_context(data, request))
    elif slug == 'financijska-izvjestaja':
        ctx.update(finance_reports_context(data, request))
    elif slug == 'kalendar':
        ctx.update(kalendar_page_context(data, request))
    elif slug == 'formulari':
        ctx.update(documents_page_context(data, svc.load_settings(), request, 'formulari'))
    elif slug == 'potvrde':
        ctx.update(documents_page_context(data, svc.load_settings(), request, 'potvrde'))
    elif slug == 'dokumenti':
        ctx.update(documents_page_context(data, svc.load_settings(), request, 'dokumenti'))
    elif slug == 'maticne-knjige':
        ctx['registry_books'] = data.get('registryBooks', [])
    elif slug == 'posjete':
        ctx.update(visits_page_context(data, request))
    else:
        ctx.update(generic_table_context(request, svc, slug))
    return ctx
