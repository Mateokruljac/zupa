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


def filter_rows_by_time_period(
    rows: list[dict],
    request,
    date_field_name: str,
) -> tuple[list[dict], str]:
    selected_period = request.GET.get('period', 'all')
    if selected_period not in {'all', 'upcoming', 'today', 'past'}:
        selected_period = 'all'

    today = date.today()
    completed_statuses = {'obavljeno', 'dovršeno', 'završeno'}

    def belongs_to_selected_period(record: dict) -> bool:
        record_date = parse_iso_date(record.get(date_field_name))
        if selected_period == 'all':
            return True
        if record_date is None:
            return False
        if selected_period == 'today':
            return record_date == today
        if selected_period == 'past':
            return record_date < today
        return (
            record_date >= today
            and (record.get('status') or '').casefold() not in completed_statuses
        )

    return [record for record in rows if belongs_to_selected_period(record)], selected_period


def add_time_badges(rows: list[dict], date_field_name: str) -> list[dict]:
    today = date.today()
    completed_statuses = {'obavljeno', 'dovršeno', 'završeno'}
    records_with_badges = []

    for original_record in rows:
        record = dict(original_record)
        record_date = parse_iso_date(record.get(date_field_name))
        record_status = (record.get('status') or '').casefold()

        if record_status in completed_statuses:
            badge_label, badge_tone = 'Obavljeno', 'done'
        elif record_date == today:
            badge_label, badge_tone = 'Danas', 'today'
        elif record_date and record_date > today:
            badge_label, badge_tone = 'Nadolazeće', 'upcoming'
        elif record_date and record_date < today:
            badge_label, badge_tone = 'Prošlo', 'past'
        else:
            badge_label, badge_tone = 'Bez datuma', 'missing'

        record['time_badge_label'] = badge_label
        record['time_badge_tone'] = badge_tone
        records_with_badges.append(record)

    return records_with_badges


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
    years = sorted(
        {group.get('year') for group in groups if group.get('year')},
        reverse=True,
    ) or [date.today().year]
    try:
        year = int(request.GET.get('year', years[0]))
    except ValueError:
        year = years[0]
    group = next((group for group in groups if group.get('year') == year), None)
    candidates = list((group or {}).get('candidates') or [])
    q = (request.GET.get('q') or '').strip().lower()
    if q:
        candidates = [
            candidate
            for candidate in candidates
            if any(
                q in str(candidate.get(field_name) or '').lower()
                for field_name in ('name', 'school', 'class', 'parents', 'status')
            )
        ]
    all_candidates = list((group or {}).get('candidates') or [])
    return {
        'fc_year': year,
        'fc_years': years,
        'fc_group': group or {'year': year, 'candidates': [], 'groupName': '', 'ceremonyDate': ''},
        'fc_candidates': candidates,
        'fc_filters': {'q': request.GET.get('q', '')},
        'fc_stats': {
            'total': len(all_candidates),
            'paid': sum(1 for candidate in all_candidates if candidate.get('paid')),
        },
    }


def baptisms_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('baptisms', []),
        request,
        [
            'childName',
            'parents',
            'godparents',
            'celebrant',
            'status',
            'baptismDate',
            'registryNo',
        ],
    )
    rows, selected_period = filter_rows_by_time_period(
        rows,
        request,
        'baptismDate',
    )
    filters['period'] = selected_period
    workflow_rows = _workflow_rows(rows, 'krsenja')
    return {
        'rows': add_time_badges(workflow_rows, 'baptismDate'),
        'filters': filters,
        'stats': sacrament_stats(data.get('baptisms', []), 'baptismDate'),
    }


def weddings_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('weddings', []),
        request,
        [
            'couple',
            'status',
            'weddingDate',
            'church',
            'contact',
            'celebrant',
            'witnesses',
        ],
    )
    rows, selected_period = filter_rows_by_time_period(
        rows,
        request,
        'weddingDate',
    )
    filters['period'] = selected_period
    workflow_rows = _workflow_rows(rows, 'vjencanja')
    return {
        'rows': add_time_badges(workflow_rows, 'weddingDate'),
        'filters': filters,
        'stats': sacrament_stats(data.get('weddings', []), 'weddingDate'),
    }


def funerals_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('funerals', []),
        request,
        ['deceased', 'cemetery', 'status', 'funeralDate'],
    )
    rows, selected_period = filter_rows_by_time_period(
        rows,
        request,
        'funeralDate',
    )
    filters['period'] = selected_period
    workflow_rows = _workflow_rows(rows, 'pogrebi')
    return {
        'rows': add_time_badges(workflow_rows, 'funeralDate'),
        'filters': filters,
        'stats': sacrament_stats(data.get('funerals', []), 'funeralDate'),
    }


def anointing_context(data: dict, request) -> dict:
    rows, filters = filter_rows(
        data.get('anointing', []),
        request,
        ['person', 'priest', 'address', 'location', 'contact', 'notes', 'status'],
    )
    rows, selected_period = filter_rows_by_time_period(
        rows,
        request,
        'scheduled',
    )
    filters['period'] = selected_period
    stats = sacrament_stats(data.get('anointing', []), 'scheduled')
    return {
        'rows': add_time_badges(rows, 'scheduled'),
        'filters': filters,
        'stats': stats,
    }


def families_page_context(data: dict, request) -> dict:
    streets = {
        street['id']: street
        for street in data.get('streets', [])
    }
    street_filter = request.GET.get('street', '')
    search_term = (request.GET.get('q') or '').strip().lower()
    all_families = list(data.get('families', []))
    families = list(all_families)
    if street_filter:
        families = [
            family
            for family in families
            if family.get('streetId') == street_filter
        ]
    if search_term:
        families = [
            family
            for family in families
            if search_term in (family.get('surname') or '').lower()
            or search_term in (family.get('address') or '').lower()
            or any(
                search_term in (family_member.get('name') or '').lower()
                for family_member in family.get('members') or []
            )
        ]
    year = date.today().year
    lukno_unpaid = 0
    total_members = sum(
        len(family.get('members') or [])
        for family in all_families
    )
    today = date.today()
    enriched_families = []
    pastoral_due = 0
    missing_contact = 0
    for family in families:
        annual_contribution = next(
            (
                contribution
                for contribution in family.get('contributions', [])
                if contribution.get('year') == year
            ),
            None,
        )
        if annual_contribution and not annual_contribution.get('luknoPaid'):
            lukno_unpaid += 1
        enriched_family = dict(family)
        last_visit = parse_iso_date(enriched_family.get('lastVisit'))
        enriched_family['last_visit_days'] = (
            (today - last_visit).days
            if last_visit
            else None
        )
        enriched_family['needs_pastoral_followup'] = (
            not last_visit
            or enriched_family['last_visit_days'] > 365
            or 'posjetiti' in (
                enriched_family.get('pastoralNotes') or ''
            ).casefold()
        )
        if enriched_family['needs_pastoral_followup']:
            pastoral_due += 1
        if not enriched_family.get('phone') and not enriched_family.get('email'):
            missing_contact += 1
        enriched_families.append(enriched_family)
    families = enriched_families
    selected_family_id = request.GET.get('family', '')
    selected_family = next(
        (
            family
            for family in all_families
            if family.get('id') == selected_family_id
        ),
        None,
    )
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
            'total': len(all_families),
            'shown': len(families),
            'members': total_members,
            'streets_count': len(data.get('streets', [])),
            'lukno_unpaid': lukno_unpaid,
            'pastoral_due': pastoral_due,
            'missing_contact': missing_contact,
        },
        'current_year': year,
    }
