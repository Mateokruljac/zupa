"""Podsjetnici — agregacija obaveza župnog ureda (iz reminders-engine.js)."""
from __future__ import annotations

from datetime import date

from pastoral.services.dates import add_days_iso, days_since, today_iso


def collect_reminders(data: dict, *, include_dismissed: bool = False) -> list[dict]:
    """Vraća sortirane podsjetnike. Dismiss filtrira klijent (localStorage)."""
    today = today_iso()
    year = date.today().year
    items: list[dict] = []

    for s in data.get('publicSubmissions') or []:
        if s.get('status') != 'nova':
            continue
        items.append({
            'id': f"sub_{s.get('id')}",
            'priority': 'visoka',
            'category': 'prijava',
            'title': f"Nova javna prijava: {s.get('formType') or s.get('type', 'obrazac')}",
            'sub': s.get('submittedAt', ''),
            'href': f"javne-prijave?submission={s.get('id', '')}",
            'due': today,
        })

    for t in data.get('tasks') or []:
        if t.get('done'):
            continue
        due = t.get('due') or ''
        late = due and due < today
        items.append({
            'id': f"task_{t.get('id')}",
            'priority': 'visoka' if late or t.get('priority') == 'visoka' else 'srednja',
            'category': 'zadatak',
            'title': t.get('title', 'Zadatak'),
            'sub': f"{t.get('category', '')} · rok {due or '—'}",
            'href': f"kalendar?task={t.get('id', '')}",
            'due': due or today,
        })

    for n in data.get('intentions') or []:
        if n.get('paid') or float(n.get('stipend') or 0) <= 0:
            continue
        nd = n.get('date') or ''
        items.append({
            'id': f"nak_{n.get('id')}",
            'priority': 'visoka' if nd <= today else 'srednja',
            'category': 'nakana',
            'title': f"Neplaćena nakana: {n.get('intentionFor', '')}",
            'sub': f"{nd} {n.get('massTime', '')}",
            'href': f"nakane?date={nd}",
            'due': nd,
        })

    for fam in data.get('families') or []:
        row = next((c for c in fam.get('contributions') or [] if c.get('year') == year), None)
        if row and not row.get('luknoPaid'):
            items.append({
                'id': f"lukno_{fam.get('id')}_{year}",
                'priority': 'srednja',
                'category': 'lukno',
                'title': f"Lukno {year} — obitelj {fam.get('surname', '')}",
                'sub': fam.get('address') or fam.get('phone') or '',
                'href': f"obitelji?family={fam.get('id', '')}",
                'due': today,
            })
        notes = (fam.get('pastoralNotes') or '').lower()
        if fam.get('status') == 'aktivna' and (
            'posjetiti' in notes or days_since(fam.get('lastVisit')) > 60
        ):
            since = days_since(fam.get('lastVisit'))
            items.append({
                'id': f"visit_fam_{fam.get('id')}",
                'priority': 'visoka' if since > 120 else 'srednja',
                'category': 'posjet',
                'title': f"Posjet obitelji {fam.get('surname', '')}",
                'sub': f"Zadnji posjet: {fam.get('lastVisit')}" if fam.get('lastVisit') else 'Još nema zabilježenog posjeta',
                'href': f"obitelji?family={fam.get('id', '')}",
                'due': today,
            })

    for v in data.get('visits') or []:
        if v.get('done') or not v.get('scheduled'):
            continue
        if v['scheduled'] > add_days_iso(7):
            continue
        items.append({
            'id': f"visit_{v.get('id')}",
            'priority': 'visoka' if v['scheduled'] < today else 'srednja',
            'category': 'posjet',
            'title': v.get('purpose') or 'Pastoralni posjet',
            'sub': f"{v.get('person') or v.get('familyLabel') or ''} · {v['scheduled']}",
            'href': 'posjete',
            'due': v['scheduled'],
        })

    for key, page, label in (
        ('baptisms', 'krsenja', 'Krštenje'),
        ('weddings', 'vjencanja', 'Vjenčanje'),
    ):
        date_key = 'baptismDate' if key == 'baptisms' else 'weddingDate'
        name_key = 'childName' if key == 'baptisms' else 'couple'
        for rec in data.get(key) or []:
            dt = rec.get(date_key) or ''
            if not dt or dt < today or dt > add_days_iso(14):
                continue
            items.append({
                'id': f"sac_{key}_{rec.get('id')}",
                'priority': 'srednja',
                'category': 'sakrament',
                'title': f"{label}: {rec.get(name_key, '')}",
                'sub': dt,
                'href': page,
                'due': dt,
            })

    for f in data.get('funerals') or []:
        fd = f.get('funeralDate') or ''
        if fd and today <= fd <= add_days_iso(7):
            items.append({
                'id': f"fun_{f.get('id')}",
                'priority': 'visoka',
                'category': 'pogreb',
                'title': f"Pogreb: {f.get('deceased', '')}",
                'sub': fd,
                'href': 'pogrebi',
                'due': fd,
            })

    for inv in data.get('invoices') or []:
        if inv.get('direction') == 'outgoing':
            continue
        if inv.get('status') in ('placen', 'storno'):
            continue
        rest = float(inv.get('total') or 0) - float(inv.get('paidAmount') or 0)
        if rest <= 0:
            continue
        supplier = inv.get('supplierName') or inv.get('payerName') or 'dobavljač'
        due = inv.get('dueDate') or today
        items.append({
            'id': f"inv_{inv.get('id')}",
            'priority': 'visoka' if inv.get('dueDate') and inv['dueDate'] < today else 'srednja',
            'category': 'racun',
            'title': f"Ulazni račun {inv.get('number', '')} — {supplier}",
            'sub': f'{rest:.2f} € za platiti',
            'href': 'racuni',
            'due': due,
        })

    for d in data.get('parishDebts') or []:
        if d.get('paid') or float(d.get('amount') or 0) <= 0:
            continue
        items.append({
            'id': f"debt_{d.get('id')}",
            'priority': 'visoka' if (d.get('dueDate') or '9999') < today else 'srednja',
            'category': 'dug',
            'title': d.get('label', 'Dugovanje'),
            'sub': d.get('dueDate', ''),
            'href': 'dugovanja',
            'due': d.get('dueDate') or today,
        })

    order = {'visoka': 0, 'srednja': 1, 'niska': 2}
    items.sort(key=lambda r: (order.get(r['priority'], 9), r.get('due') or ''))
    return items
