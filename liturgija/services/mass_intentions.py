"""CRUD misnih nakana nad ORM-om (bez parish JSON blob-a)."""
import logging
from datetime import date
from uuid import UUID

from liturgija.models import MassIntention
from liturgija.services.mass_records import schedule_collections
from liturgija.services.mass_schedule import has_scheduled_mass

logger = logging.getLogger(__name__)


class MassIntentionRejected(Exception):
    def __init__(self, code: str, status_code: int = 400):
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def _require_scheduled_mass(intention_date: date, mass_time: str) -> None:
    if has_scheduled_mass(schedule_collections(), intention_date.isoformat(), mass_time):
        return
    logger.warning(
        'nakana: nema mise date=%s time=%s',
        intention_date,
        mass_time,
    )
    raise MassIntentionRejected('no_mass_on_date')


def create_mass_intention(
    *,
    intention_date: date,
    mass_time: str,
    intention_for: str,
    stipend,
    is_paid: bool,
    notes: str,
) -> MassIntention:
    _require_scheduled_mass(intention_date, mass_time)
    return MassIntention.objects.create(
        intention_date=intention_date,
        mass_time=mass_time,
        intention_for=intention_for,
        stipend=stipend,
        is_paid=is_paid,
        notes=notes,
    )


def update_mass_intention(
    intention_id: UUID,
    *,
    intention_date: date,
    mass_time: str,
    intention_for: str,
    stipend,
    is_paid: bool,
    notes: str,
) -> MassIntention:
    intention = MassIntention.objects.filter(pk=intention_id).first()
    if intention is None:
        logger.warning('nakana: nije pronađena id=%s', intention_id)
        raise MassIntentionRejected('not_found', status_code=404)
    _require_scheduled_mass(intention_date, mass_time)
    intention.intention_date = intention_date
    intention.mass_time = mass_time
    intention.intention_for = intention_for
    intention.stipend = stipend
    intention.is_paid = is_paid
    intention.notes = notes
    intention.save(update_fields=(
        'intention_date',
        'mass_time',
        'intention_for',
        'stipend',
        'is_paid',
        'notes',
        'updated_at',
    ))
    return intention
