"""JSON API mutacije misnih nakana (`/api/action/`).

Create / update / delete rade izravno na modelu `MassIntention`.
`id` u API-ju je PK retka (FCTA record_id).

Forma šalje: date, mass_time, intention_for, stipend, paid, notes.
Jedina poslovna provjera: tog dana u rasporedu postoji ta misa.
"""
from datetime import date

from liturgija.log import get_logger
from liturgija.models import MassIntention
from liturgija.services.mass_records import (
    mass_intention_as_legacy_record,
    schedule_collections,
)
from liturgija.services.mass_schedule import get_masses_for_date


def _has_mass(iso_date, mass_time) -> bool:
    """True ako tog dana u rasporedu postoji ta misa (raspored + iznimke)."""
    if not iso_date or not mass_time:
        return False
    return any(
        str(mass.get('time') or '') == mass_time
        for mass in get_masses_for_date(schedule_collections(), iso_date)
    )


def _fill(intention, data):
    """Prepiši polja modela iz podataka forme (bez id-a)."""
    raw_date = data.get('date')
    # Forma šalje ISO string; DateField očekuje date.
    intention.intention_date = (
        raw_date if isinstance(raw_date, date)
        else date.fromisoformat(str(raw_date)[:10]) if raw_date else None
    )
    intention.mass_time = data.get('mass_time') or ''
    intention.intention_for = data.get('intention_for') or ''
    intention.stipend = data.get('stipend') or 0
    intention.is_paid = bool(data.get('paid'))
    intention.notes = data.get('notes') or ''


def create_intention(data: dict) -> dict:
    """Nova nakana iz podataka forme. Svaki poziv sprema novi red."""
    iso_date = str(data.get('date') or '')[:10]
    mass_time = data.get('mass_time') or ''
    if not _has_mass(iso_date, mass_time):
        return {'ok': False, 'error': 'no_mass_on_date'}
    intention = MassIntention()
    _fill(intention, data)
    intention.save()
    return {'ok': True, 'item': mass_intention_as_legacy_record(intention)}


def update_intention(intention_id, data: dict) -> dict:
    """Ažuriraj nakanu po id. Podaci forme prepisuju sva polja."""
    intention = MassIntention.objects.filter(pk=intention_id).first()
    if not intention:
        return {'ok': False, 'error': 'not_found'}
    iso_date = str(data.get('date') or '')[:10]
    mass_time = data.get('mass_time') or ''
    if not _has_mass(iso_date, mass_time):
        return {'ok': False, 'error': 'no_mass_on_date'}
    _fill(intention, data)
    intention.save()
    return {'ok': True, 'item': mass_intention_as_legacy_record(intention)}


def delete_intention(intention_id) -> dict:
    """Obriši nakanu po id. Neuspjeh se logira u liturgija/logs/liturgija.log."""
    logger = get_logger()
    try:
        MassIntention.objects.get(pk=intention_id).delete()
    except Exception:
        logger.exception('Greška pri brisanju nakane id=%s', intention_id)
        return {'ok': False, 'error': 'delete_failed'}
    return {'ok': True}
