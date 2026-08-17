MODULES = {
    'pregled': {'label': 'Pregled', 'pages': ['dashboard']},
    'zupa': {'label': 'Župa i vjernici', 'pages': ['podsjetnici', 'obitelji', 'ulice', 'posjete']},
    'liturgija': {'label': 'Liturgija', 'pages': ['nakane', 'mise', 'zupni-listic']},
    'sakramenti': {
        'label': 'Sakramenti',
        'pages': ['krsenja', 'prva-pricest', 'krizma', 'vjencanja', 'pogrebi', 'pomazanje'],
    },
    'financije': {
        'label': 'Financije',
        'pages': ['dugovanja'],
    },
    'financije-zakljucano': {
        'label': 'Financije (zaključano)',
        'pages': ['racuni', 'blagajna', 'financijska-izvjestaja'],
    },
    'isprave': {
        'label': 'Isprave i matice',
        'pages': ['formulari', 'potvrde', 'dokumenti', 'maticne-knjige'],
    },
    'suradnja': {
        'label': 'Dekanat i suradnja',
        'pages': ['dekanat'],
    },
    'ured': {
        'label': 'Župni ured',
        'pages': ['operativno-srediste', 'vijeca', 'kalendar', 'javne-prijave'],
    },
    'postavke': {'label': 'Postavke', 'pages': ['postavke', 'web-stranica']},
}

PAGE_TO_MODULE = {}
for mod, cfg in MODULES.items():
    for page in cfg['pages']:
        PAGE_TO_MODULE[page] = mod

LOCKED_FINANCE_PAGES = frozenset(MODULES['financije-zakljucano']['pages'])


def is_locked_finance_page(page: str) -> bool:
    return page in LOCKED_FINANCE_PAGES

ROLE_PERMISSIONS = {
    'zupnik': list(MODULES.keys()),
    'vikar': list(MODULES.keys()),
    'upravitelj': ['pregled', 'zupa', 'liturgija', 'financije', 'isprave', 'suradnja', 'ured', 'postavke'],
}


def role_permissions(role: str) -> list[str]:
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS['zupnik'])


def can_access_page(page: str, role: str) -> bool:
    if page in ('dashboard', 'login', 'index'):
        return True
    module = PAGE_TO_MODULE.get(page)
    if not module:
        return True
    return module in role_permissions(role)


NAV = [
    {'type': 'label', 'text': 'Pregled'},
    {'type': 'link', 'page': 'dashboard', 'icon': '⊞', 'label': 'Nadzorna ploča'},
    {'type': 'label', 'text': 'Župa i vjernici'},
    {'type': 'link', 'page': 'podsjetnici', 'icon': '🔔', 'label': 'Podsjetnici'},
    {'type': 'link', 'page': 'obitelji', 'icon': '👨‍👩‍👧', 'label': 'Obitelji'},
    {'type': 'link', 'page': 'ulice', 'icon': '🛣', 'label': 'Ulice'},
    {'type': 'link', 'page': 'posjete', 'icon': '🏠', 'label': 'Posjete'},
    {'type': 'label', 'text': 'Liturgija'},
    {'type': 'link', 'page': 'nakane', 'icon': '☩', 'label': 'Misne nakane'},
    {'type': 'link', 'page': 'mise', 'icon': '◉', 'label': 'Raspored misa'},
    {'type': 'link', 'page': 'zupni-listic', 'icon': '📰', 'label': 'Župni listić'},
    {'type': 'label', 'text': 'Sakramenti'},
    {'type': 'link', 'page': 'krsenja', 'icon': '💧', 'label': 'Krštenja'},
    {'type': 'link', 'page': 'prva-pricest', 'icon': '✞', 'label': 'Prva pričest'},
    {'type': 'link', 'page': 'krizma', 'icon': '✠', 'label': 'Krizma'},
    {'type': 'link', 'page': 'vjencanja', 'icon': '♥', 'label': 'Vjenčanja'},
    {'type': 'link', 'page': 'pogrebi', 'icon': '✝', 'label': 'Pogrebi'},
    {'type': 'link', 'page': 'pomazanje', 'icon': '🕯', 'label': 'Pomazanje'},
    {'type': 'label', 'text': 'Financije'},
    {'type': 'link', 'page': 'dugovanja', 'icon': '€', 'label': 'Dugovanja'},
    {'type': 'link', 'page': 'racuni', 'icon': '🧾', 'label': 'Ulazni računi'},
    {'type': 'link', 'page': 'blagajna', 'icon': '📒', 'label': 'Blagajna'},
    {'type': 'link', 'page': 'financijska-izvjestaja', 'icon': '📊', 'label': 'Fin. izvješća'},
    {'type': 'label', 'text': 'Isprave'},
    {'type': 'link', 'page': 'formulari', 'icon': '🖨', 'label': 'Formulari (ispis)'},
    {'type': 'link', 'page': 'potvrde', 'icon': '📜', 'label': 'Potvrde'},
    {'type': 'link', 'page': 'dokumenti', 'icon': '📄', 'label': 'Dokumenti (Excel)'},
    {'type': 'link', 'page': 'maticne-knjige', 'icon': '📖', 'label': 'Matične knjige'},
    {'type': 'label', 'text': 'Dekanat i suradnja'},
    {'type': 'link', 'page': 'dekanat', 'icon': '⇄', 'label': 'Međužupni zahtjevi'},
    {'type': 'label', 'text': 'Župni ured'},
    {'type': 'link', 'page': 'operativno-srediste', 'icon': '⌘', 'label': 'Operativno središte'},
    {'type': 'link', 'page': 'vijeca', 'icon': '👥', 'label': 'Vijeća ŽPV/ŽEV'},
    {'type': 'link', 'page': 'kalendar', 'icon': '📅', 'label': 'Događaji i zadaci'},
    {'type': 'link', 'page': 'javne-prijave', 'icon': '📝', 'label': 'Javne prijave'},
    {'type': 'link', 'page': 'web-stranica', 'icon': '◎', 'label': 'Web-stranica'},
    {'type': 'link', 'page': 'postavke', 'icon': '⚙', 'label': 'Postavke'},
]


SECTION_IDS = {
    'Pregled': 'pregled',
    'Župa i vjernici': 'zupa',
    'Liturgija': 'liturgija',
    'Sakramenti': 'sakramenti',
    'Financije': 'financije',
    'Isprave': 'isprave',
    'Dekanat i suradnja': 'suradnja',
    'Župni ured': 'ured',
}


def group_nav_sections(nav_items: list) -> list:
    sections = []
    current = None
    for item in nav_items:
        if item['type'] == 'label':
            if current:
                sections.append(current)
            current = {
                'id': SECTION_IDS.get(item['text'], item['text'].lower()[:12]),
                'label': item['text'],
                'links': [],
            }
            continue
        if not current:
            current = {'id': 'pregled', 'label': 'Pregled', 'links': []}
        current['links'].append(item)
    if current:
        sections.append(current)
    return sections


def nav_badges_from_stats(stats: dict) -> dict:
    badges = {}
    if stats.get('nova_prijave'):
        badges['javne-prijave'] = stats['nova_prijave']
    if stats.get('unpaid_nakane'):
        badges['nakane'] = stats['unpaid_nakane']
    if stats.get('debts_unpaid'):
        badges['dugovanja'] = stats['debts_unpaid']
    if stats.get('reminders_count'):
        badges['podsjetnici'] = stats['reminders_count']
    task_badge = stats.get('overdue_tasks', 0) + stats.get('due_today_tasks', 0)
    if task_badge:
        badges['kalendar'] = task_badge
    if stats.get('lukno_unpaid'):
        badges['obitelji'] = stats['lukno_unpaid']
    if stats.get('visits_due'):
        badges['posjete'] = stats['visits_due']
    if stats.get('interparish_pending'):
        badges['dekanat'] = stats['interparish_pending']
    if stats.get('operations_attention'):
        badges['operativno-srediste'] = stats['operations_attention']
    return badges


def filter_nav(role: str, current_page: str) -> list:
    allowed = set(role_permissions(role))
    out = []
    section_visible = False
    for item in NAV:
        if item['type'] == 'label':
            section_visible = False
            out.append({
                **item,
                'hidden': True,
                'section_id': SECTION_IDS.get(item['text'], item['text'].lower()[:12]),
            })
            continue
        module = PAGE_TO_MODULE.get(item['page'], 'pregled')
        if module not in allowed:
            continue
        if out and out[-1]['type'] == 'label' and out[-1].get('hidden'):
            out[-1]['hidden'] = False
            section_visible = True
        out.append({
            **item,
            'active': item['page'] == current_page or (
                current_page == 'dashboard' and item['page'] == 'dashboard'
            ),
        })
    return [i for i in out if not (i['type'] == 'label' and i.get('hidden'))]
