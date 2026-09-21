"""
Mutacije dugovanja u parish JSON podacima.

Piše zastavice plaćanja i nove stavke `parishDebts` u dict koji kasnije
sprema `operational_store`. Nema vlastitog ORM poziva. Izvor stavke
(`source.type`) mora odgovarati onome što `debts.collect_*` stavlja u
redak; inače `mark_debt_paid` ne nađe zapis i UI misli da je akcija
uspješna ili neuspješna ovisno o pozivatelju.

Pozivatelji: `financije.page_actions` (POST forme) i `financije.api_actions`.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone

from pastoral.services.dates import today_iso


def mark_debt_paid(data: dict, source: dict) -> bool:
    """
    Označava jednu potraživanu ili obveznu stavku kao plaćenu.

    Traži izvorni zapis po `source.type` i id-u / godini lukna.
    Svaki izvor ima svoje polje (`luknoPaid`, `paid`, `stipendPaid`,
    `groupFeePaid`) jer podaci još žive u obiteljima, nakanama i
    sakramentima, ne u jednoj tablici duga.

    Ne uspijeva tiho (`False`) ako izvor nema ili zapis ne postoji —
    ne baca iznimku. Ne kreira stavku blagajne; knjiženje je odvojeni
    korak ako ga UI uopće nudi.

    Args:
        data: Parish dict koji se mijenja na mjestu.
        source: Dict iz `collect_*` polja `source` (type + identifikatori).

    Returns:
        True ako je zapis pronađen i ažuriran.

    Side effects:
        Mutira ugniježđene dictove u `data`.
    """
    if not source:
        return False
    source_type = source.get('type')
    if source_type == 'contribution':
        family = next(
            (
                family_record
                for family_record in data.get('families', [])
                if family_record.get('id') == source.get('familyId')
            ),
            None,
        )
        if not family:
            return False
        contribution = next(
            (
                contribution_record
                for contribution_record in family.get('contributions', [])
                if contribution_record.get('year') == source.get('year')
            ),
            None,
        )
        if not contribution:
            return False
        contribution['luknoPaid'] = True
        contribution['luknoPaidAt'] = today_iso()
        return True
    if source_type == 'intention':
        intention = next(
            (
                intention_record
                for intention_record in data.get('intentions', [])
                if intention_record.get('id') == source.get('id')
            ),
            None,
        )
        if not intention:
            return False
        intention['paid'] = True
        intention['paymentId'] = (
            intention.get('paymentId')
            or f"MAN-{uuid.uuid4().hex[:6].upper()}"
        )
        intention['paidAt'] = datetime.now(timezone.utc).isoformat()
        return True
    if source_type in ('baptisms', 'weddings', 'funerals'):
        sacrament_record = next(
            (
                record
                for record in data.get(source_type, [])
                if record.get('id') == source.get('id')
            ),
            None,
        )
        if not sacrament_record:
            return False
        sacrament_record['stipendPaid'] = True
        sacrament_record['stipendPaidAt'] = today_iso()
        return True
    if source_type == 'firstCommunion':
        group = next(
            (
                group_record
                for group_record in data.get('firstCommunion', [])
                if group_record.get('id') == source.get('id')
            ),
            None,
        )
        if not group:
            return False
        group['groupFeePaid'] = True
        group['groupFeePaidAt'] = today_iso()
        return True
    if source_type == 'confirmations':
        group = next(
            (
                group_record
                for group_record in data.get('confirmations', [])
                if group_record.get('id') == source.get('id')
            ),
            None,
        )
        if not group:
            return False
        group['groupFeePaid'] = True
        group['groupFeePaidAt'] = today_iso()
        return True
    if source_type == 'parishDebts':
        parish_debt = next(
            (
                debt_record
                for debt_record in data.get('parishDebts', [])
                if debt_record.get('id') == source.get('id')
            ),
            None,
        )
        if not parish_debt:
            return False
        parish_debt['paid'] = True
        parish_debt['paidAt'] = today_iso()
        return True
    return False


def parse_debt_source(raw: str) -> dict | None:
    """
    Parsira JSON izvora duga s forme (hidden polje `source`).

    Forma šalje isti objekt koji je `collect_*` stavio u redak, da
    `mark_debt_paid` ne ovisi o prikaznom `id` retka (`lukno_…`).

    Args:
        raw: JSON string ili bilo što što nije valjani objekt.

    Returns:
        Dict izvora ili None ako JSON nije objekt.
    """
    try:
        source = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return source if isinstance(source, dict) else None


def add_parish_debt(data: dict, cleaned: dict) -> dict:
    """
    Dodaje ručnu stavku u `parishDebts` (režije, DŽ, ostalo).

    Ovo nisu lukno ni stipend sakramenta — samo dugovi koji nemaju
    drugi izvorni zapis. Zadani smjer je `payable` (župa duguje).
    Godina se uzima s datuma dospijeća, inače tekuća.

    Args:
        data: Parish dict; ključ `parishDebts` se stvara po potrebi.
        cleaned: Očišćena polja forme (`label`, `amount`, opcionalno
            `direction`, `category`, `paid`, `notes`, `contact`, `due_date`).

    Returns:
        Novi dict stavke (isti objekt koji je appendan u listu).

    Side effects:
        Append u `data['parishDebts']`.
    """
    item = {
        'id': f"pd_{uuid.uuid4().hex[:8]}",
        'direction': cleaned.get('direction') or 'payable',
        'category': cleaned.get('category') or 'ostalo',
        'label': cleaned['label'],
        'amount': float(cleaned['amount']),
        'paid': cleaned.get('paid', False),
        'notes': cleaned.get('notes') or '',
        'contact': cleaned.get('contact') or '',
        'dueDate': (
            cleaned['due_date'].isoformat()
            if cleaned.get('due_date')
            else ''
        ),
        'year': (
            cleaned['due_date'].year
            if cleaned.get('due_date')
            else date.today().year
        ),
    }
    data.setdefault('parishDebts', []).append(item)
    return item
