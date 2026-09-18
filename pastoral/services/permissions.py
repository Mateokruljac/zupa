MODULES = {
    'pregled': {'label': 'Pregled', 'pages': ['dashboard']},
    'zupa': {'label': 'Župa i vjernici', 'pages': ['obitelji', 'ulice', 'posjete']},
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
        'pages': ['potvrde', 'maticne-knjige'],
    },
    'ured': {
        'label': 'Župni ured',
        'pages': ['podsjetnici', 'vijeca', 'kalendar', 'javne-prijave'],
    },
    'postavke': {'label': 'Postavke', 'pages': ['postavke']},
}

PAGE_TO_MODULE = {}
for module_identifier, module_configuration in MODULES.items():
    for page in module_configuration['pages']:
        PAGE_TO_MODULE[page] = module_identifier

LOCKED_FINANCE_PAGES = frozenset(MODULES['financije-zakljucano']['pages'])
FINANCE_PAGES = frozenset({'dugovanja', *LOCKED_FINANCE_PAGES})
FINANCE_SIDEBAR_CANDIDATES = ('financijska-izvjestaja', 'dugovanja')


def is_locked_finance_page(page: str) -> bool:
    return page in LOCKED_FINANCE_PAGES


def finance_sidebar_page(role: str) -> str | None:
    """Jedna sidebar stavka: pregled ako smije, inače dugovanja."""
    allowed_modules = set(role_permissions(role))
    for page in FINANCE_SIDEBAR_CANDIDATES:
        module = PAGE_TO_MODULE.get(page, 'pregled')
        if module in allowed_modules:
            return page
    return None

ROLE_PERMISSIONS = {
    'zupnik': list(MODULES.keys()),
    'vikar': list(MODULES.keys()),
    'upravitelj': ['pregled', 'zupa', 'liturgija', 'financije', 'isprave', 'ured', 'postavke'],
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
    {'type': 'link', 'page': 'financijska-izvjestaja', 'icon': '€', 'label': 'Financije'},
    {'type': 'label', 'text': 'Isprave'},
    {'type': 'link', 'page': 'potvrde', 'icon': '📜', 'label': 'Dokumenti i potvrde'},
    {'type': 'link', 'page': 'maticne-knjige', 'icon': '📖', 'label': 'Matične knjige'},
    {'type': 'label', 'text': 'Župni ured'},
    {'type': 'link', 'page': 'podsjetnici', 'icon': '🔔', 'label': 'Podsjetnici'},
    {'type': 'link', 'page': 'vijeca', 'icon': '👥', 'label': 'Vijeća ŽPV/ŽEV'},
    {'type': 'link', 'page': 'kalendar', 'icon': '📅', 'label': 'Događaji i zadaci'},
    {'type': 'link', 'page': 'javne-prijave', 'icon': '📝', 'label': 'Javne prijave'},
    {'type': 'link', 'page': 'postavke', 'icon': '⚙', 'label': 'Postavke'},
]

NAV_PAGES = {
    item['page']
    for item in NAV
    if item.get('type') == 'link'
}
KNOWN_NAV_PAGES = NAV_PAGES | FINANCE_PAGES


def current_nav_page(request) -> str:
    """Stranica za aktivnu stavku izbornika, i kad URL nema kwargs ``page``."""
    match = getattr(request, 'resolver_match', None)
    if not match:
        return 'dashboard'
    page = match.kwargs.get('page')
    if page in KNOWN_NAV_PAGES:
        return page
    if match.url_name in {'app', 'dashboard'}:
        return 'dashboard'
    if match.url_name in KNOWN_NAV_PAGES:
        return match.url_name
    path = (request.path or '').rstrip('/')
    if '/pages/' in path:
        slug = path.rsplit('/pages/', 1)[-1].split('/')[0]
        if slug in KNOWN_NAV_PAGES:
            return slug
    return 'dashboard'


SECTION_IDS = {
    'Pregled': 'pregled',
    'Župa i vjernici': 'zupa',
    'Liturgija': 'liturgija',
    'Sakramenti': 'sakramenti',
    'Financije': 'financije',
    'Isprave': 'isprave',
    'Župni ured': 'ured',
}


def group_nav_sections(nav_items: list) -> list:
    sections = []
    current_section = None
    for item in nav_items:
        if item['type'] == 'label':
            if current_section:
                sections.append(current_section)
            current_section = {
                'id': SECTION_IDS.get(item['text'], item['text'].lower()[:12]),
                'label': item['text'],
                'links': [],
            }
            continue
        if not current_section:
            current_section = {
                'id': 'pregled',
                'label': 'Pregled',
                'links': [],
            }
        current_section['links'].append(item)
    if current_section:
        sections.append(current_section)
    return sections


def nav_badges_from_stats(stats: dict) -> dict:
    badges = {}
    if stats.get('nova_prijave'):
        badges['javne-prijave'] = stats['nova_prijave']
    if stats.get('unpaid_nakane'):
        badges['nakane'] = stats['unpaid_nakane']
    if stats.get('debts_unpaid'):
        unpaid = stats['debts_unpaid']
        badges['dugovanja'] = unpaid
        badges['financijska-izvjestaja'] = unpaid
    if stats.get('reminders_count'):
        badges['podsjetnici'] = stats['reminders_count']
    task_badge = stats.get('overdue_tasks', 0) + stats.get('due_today_tasks', 0)
    if task_badge:
        badges['kalendar'] = task_badge
    if stats.get('lukno_unpaid'):
        badges['obitelji'] = stats['lukno_unpaid']
    if stats.get('visits_due'):
        badges['posjete'] = stats['visits_due']
    return badges


def filter_nav(role: str, current_page: str) -> list:
    allowed_modules = set(role_permissions(role))
    visible_navigation_items = []
    for item in NAV:
        if item['type'] == 'label':
            visible_navigation_items.append({
                **item,
                'hidden': True,
                'section_id': SECTION_IDS.get(item['text'], item['text'].lower()[:12]),
            })
            continue
        if item['page'] == 'financijska-izvjestaja':
            resolved_page = finance_sidebar_page(role)
            if not resolved_page:
                continue
            nav_item = {**item, 'page': resolved_page}
        else:
            module = PAGE_TO_MODULE.get(item['page'], 'pregled')
            if module not in allowed_modules:
                continue
            nav_item = item
        if (
            visible_navigation_items
            and visible_navigation_items[-1]['type'] == 'label'
            and visible_navigation_items[-1].get('hidden')
        ):
            visible_navigation_items[-1]['hidden'] = False
        finance_active = (
            nav_item['page'] in FINANCE_PAGES
            and current_page in FINANCE_PAGES
        )
        visible_navigation_items.append({
            **nav_item,
            'active': nav_item['page'] == current_page or finance_active,
        })
    return [
        navigation_item
        for navigation_item in visible_navigation_items
        if not (
            navigation_item['type'] == 'label'
            and navigation_item.get('hidden')
        )
    ]
