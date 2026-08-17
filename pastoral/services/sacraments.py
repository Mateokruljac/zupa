"""Sakramenti — filtriranje i kontekst stranica."""
from __future__ import annotations

from datetime import date

from pastoral.services.dates import parse_iso_date, today_iso


def filter_rows(rows: list, request, search_fields: list[str]) -> tuple[list, dict]:
    q = (request.GET.get('q') or '').strip().lower()
    status = request.GET.get('status', '')
    out = list(rows)
    if status:
        out = [r for r in out if r.get('status') == status]
    if q:
        def match(r):
            for f in search_fields:
                val = r.get(f)
                if val is not None and q in str(val).lower():
                    return True
            return False
        out = [r for r in out if match(r)]
    return out, {'q': request.GET.get('q', ''), 'status': status}


def sacrament_stats(rows: list, date_key: str = '') -> dict:
    today = today_iso()
    upcoming = 0
    done = 0
    if date_key:
        for r in rows:
            dt = r.get(date_key) or r.get('scheduled') or ''
            st = r.get('status', '')
            if st == 'obavljeno':
                done += 1
            elif dt and dt >= today and st != 'obavljeno':
                upcoming += 1
    return {'total': len(rows), 'upcoming': upcoming, 'done': done}


def _workflow_rows(rows: list, page: str) -> list:
    today = date.today()
    date_key, prefix = {
        'krsenja': ('baptismDate', 'KRŠ'),
        'vjencanja': ('weddingDate', 'VJ'),
        'pogrebi': ('funeralDate', 'POG'),
        'pomazanje': ('scheduled', 'BOL'),
    }[page]
    output = []
    for index, original in enumerate(rows, start=1):
        row = dict(original)
        ceremony_date = parse_iso_date(row.get(date_key))
        is_past = bool(ceremony_date and ceremony_date < today)
        if page == 'krsenja':
            checks = [
                ('Roditelji i kontakt', bool(row.get('parents'))), ('Termin', bool(row.get('baptismDate'))),
                ('Kumovi', bool(row.get('godparents'))), ('Potvrda kuma', bool(row.get('godparentCertReceived'))),
                ('Celebrant', bool(row.get('celebrant'))),
            ]
            if is_past:
                checks.append(('Upis u maticu', bool(row.get('registryNo'))))
        elif page == 'vjencanja':
            checks = [
                ('Termin', bool(row.get('weddingDate'))), ('Dokumenti', bool(row.get('documentsOk'))),
                ('Priprava', bool(row.get('preparatorySessions'))), ('Celebrant', bool(row.get('celebrant'))),
                ('Kontakt para', bool(row.get('contact'))),
            ]
        elif page == 'pogrebi':
            checks = [
                ('Termin pogreba', bool(row.get('funeralDate'))), ('Kontakt obitelji', bool(row.get('familyContact'))),
                ('Celebrant', bool(row.get('celebrant'))), ('Groblje', bool(row.get('cemetery') or row.get('cemeteryLocation'))),
                ('Misa zadušnica', bool(row.get('massPlanned') and row.get('massDate'))),
            ]
        else:
            checks = [
                ('Kontakt', bool(row.get('contact'))), ('Adresa / lokacija', bool(row.get('address') or row.get('location'))),
                ('Termin', bool(row.get('scheduled'))), ('Svećenik', bool(row.get('priest'))),
                ('Ishod posjeta', bool(row.get('done') or row.get('notes'))),
            ]
        incomplete = [label for label, done in checks if not done]
        row['workflowChecks'] = [{'label': label, 'done': done} for label, done in checks]
        row['workflowReady'] = not incomplete
        row['workflowMissing'] = incomplete
        row['caseRef'] = row.get('caseRef') or f"{prefix}-{today.year}-{index:04d}"
        row['nextStep'] = f"Dopuniti: {incomplete[0]}" if incomplete else ('Provjeriti upis i arhiviranje' if is_past else 'Predmet spreman za termin')
        output.append(row)
    return output


def confirmation_group(data: dict, year: int) -> dict | None:
    for g in data.get('confirmations', []):
        if g.get('year') == year:
            return g
    return None


def confirmation_years(data: dict) -> list[int]:
    years = sorted({g.get('year') for g in data.get('confirmations', []) if g.get('year')}, reverse=True)
    if not years:
        years = [date.today().year]
    return years


def krizma_page_context(data: dict, request) -> dict:
    years = confirmation_years(data)
    cur = date.today().year
    try:
        year = int(request.GET.get('year', years[0] if years else cur))
    except ValueError:
        year = years[0] if years else cur
    conf = confirmation_group(data, year) or {
        'year': year,
        'candidates': [],
        'ceremonyDate': '',
        'bishop': '',
        'groupFee': 0,
        'groupFeePaid': False,
    }
    q = (request.GET.get('q') or '').strip().lower()
    status = request.GET.get('status', '')
    group = request.GET.get('group', '')
    candidates = list(conf.get('candidates') or [])
    if status:
        candidates = [c for c in candidates if c.get('status') == status]
    if group:
        candidates = [c for c in candidates if c.get('group') == group]
    if q:
        candidates = [
            c for c in candidates
            if any(q in str(c.get(k) or '').lower() for k in ('name', 'school', 'class', 'group', 'sponsor', 'status'))
        ]
    groups = sorted({c.get('group') for c in conf.get('candidates') or [] if c.get('group')})
    all_c = conf.get('candidates') or []
    return {
        'conf_year': year,
        'conf_years': years,
        'confirmation': conf,
        'candidates': candidates,
        'candidate_groups': groups,
        'krizma_filters': {'q': request.GET.get('q', ''), 'status': status, 'group': group},
        'krizma_stats': {
            'total': len(all_c),
            'prep': sum(1 for c in all_c if c.get('status') in ('priprema', 'pristupnica')),
            'confirmed': sum(1 for c in all_c if c.get('status') == 'potvrđen'),
        },
    }


def first_communion_page_context(data: dict, request) -> dict:
    groups = data.get('firstCommunion', [])
    try:
        year = int(request.GET.get('year', date.today().year))
    except ValueError:
        year = date.today().year
    group = next((g for g in groups if g.get('year') == year), groups[0] if groups else None)
    candidates = list((group or {}).get('candidates') or [])
    q = (request.GET.get('q') or '').strip().lower()
    if q:
        candidates = [c for c in candidates if q in str(c.get('name', '')).lower()]
    years = sorted({g.get('year') for g in groups if g.get('year')}, reverse=True) or [date.today().year]
    return {
        'fc_year': year,
        'fc_years': years,
        'fc_group': group or {'year': year, 'candidates': [], 'groupName': '', 'ceremonyDate': ''},
        'fc_candidates': candidates,
        'fc_filters': {'q': request.GET.get('q', '')},
    }


def baptisms_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('baptisms', []),
        request,
        ['childName', 'parents', 'status', 'baptismDate'],
    )
    return {'rows': _workflow_rows(rows, 'krsenja'), 'filters': filters, 'stats': {'total': len(data.get('baptisms', []))}}


def weddings_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('weddings', []),
        request,
        ['couple', 'status', 'weddingDate'],
    )
    return {'rows': _workflow_rows(rows, 'vjencanja'), 'filters': filters, 'stats': {'total': len(data.get('weddings', []))}}


def funerals_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('funerals', []),
        request,
        ['deceased', 'cemetery', 'status', 'funeralDate'],
    )
    return {'rows': _workflow_rows(rows, 'pogrebi'), 'filters': filters, 'stats': {'total': len(data.get('funerals', []))}}


def anointing_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('anointing', []),
        request,
        ['person', 'priest', 'address', 'location', 'contact', 'notes', 'status'],
    )
    stats = sacrament_stats(data.get('anointing', []), 'scheduled')
    return {'rows': _workflow_rows(rows, 'pomazanje'), 'filters': filters, 'stats': stats}


def families_page_context(data: dict, request) -> dict:
    streets = {s['id']: s for s in data.get('streets', [])}
    street_filter = request.GET.get('street', '')
    q = (request.GET.get('q') or '').strip().lower()
    families = list(data.get('families', []))
    if street_filter:
        families = [f for f in families if f.get('streetId') == street_filter]
    if q:
        families = [
            f for f in families
            if q in (f.get('surname') or '').lower()
            or q in (f.get('address') or '').lower()
            or any(q in (m.get('name') or '').lower() for m in f.get('members') or [])
        ]
    year = date.today().year
    lukno_unpaid = 0
    total_members = sum(len(f.get('members') or []) for f in data.get('families', []))
    today = date.today()
    enriched_families = []
    pastoral_due = 0
    missing_contact = 0
    for fam in families:
        row = next((c for c in fam.get('contributions', []) if c.get('year') == year), None)
        if row and not row.get('luknoPaid'):
            lukno_unpaid += 1
        item = dict(fam)
        last_visit = parse_iso_date(item.get('lastVisit'))
        item['last_visit_days'] = (today - last_visit).days if last_visit else None
        item['needs_pastoral_followup'] = not last_visit or item['last_visit_days'] > 365 or 'posjetiti' in (item.get('pastoralNotes') or '').casefold()
        if item['needs_pastoral_followup']:
            pastoral_due += 1
        if not item.get('phone') and not item.get('email'):
            missing_contact += 1
        enriched_families.append(item)
    families = enriched_families
    selected = request.GET.get('family', '')
    selected_family = next((f for f in families if f.get('id') == selected), None)
    selected_family_profile = None
    if selected_family:
        visits = sorted(
            [v for v in data.get('visits', []) if v.get('familyId') == selected_family.get('id')],
            key=lambda v: v.get('scheduled') or '',
            reverse=True,
        )
        current_contribution = next(
            (c for c in selected_family.get('contributions', []) if c.get('year') == year),
            None,
        )
        data_gaps = []
        if not selected_family.get('phone'):
            data_gaps.append('telefon')
        if not selected_family.get('email'):
            data_gaps.append('e-mail')
        if not selected_family.get('streetId'):
            data_gaps.append('teritorijalna pripadnost')
        if not selected_family.get('lastVisit'):
            data_gaps.append('zadnji pastoralni posjet')
        selected_family_profile = {
            'visits': visits,
            'last_visit': visits[0] if visits else None,
            'open_visits': sum(1 for visit in visits if not visit.get('done')),
            'current_contribution': current_contribution,
            'data_gaps': data_gaps,
            'tags': selected_family.get('tags') or [],
            'notes': selected_family.get('pastoralNotes') or '',
        }
    return {
        'families': families,
        'streets': streets,
        'street_list': data.get('streets', []),
        'selected_family': selected_family,
        'selected_family_profile': selected_family_profile,
        'family_filters': {'q': request.GET.get('q', ''), 'street': street_filter},
        'family_stats': {
            'total': len(data.get('families', [])),
            'shown': len(families),
            'members': total_members,
            'streets_count': len(data.get('streets', [])),
            'lukno_unpaid': lukno_unpaid,
            'pastoral_due': pastoral_due,
            'missing_contact': missing_contact,
        },
        'current_year': year,
    }
