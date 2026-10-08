"""Pydantic sheme za Ninja API misnih nakana.

Ulaz prati JSON koji šalje JS (`date`, `mass_time`, `paid`).
Izlaz prati camelCase zapis koji već čitaju nakane-engine i mise-engine.
"""
from datetime import date

from ninja import Schema
from pydantic import ConfigDict, Field

from liturgija.models import MassIntention


class MassIntentionWriteSchema(Schema):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)

    date: date
    mass_time: str = Field(min_length=1, max_length=20)
    intention_for: str = Field(min_length=1, max_length=255)
    stipend: float = Field(default=0, ge=0)
    paid: bool = False
    notes: str = ''


class MassIntentionOut(Schema):
    id: str
    date: date
    massTime: str
    intentionFor: str
    stipend: float
    paid: bool
    notes: str

    @classmethod
    def from_intention(cls, intention: MassIntention) -> 'MassIntentionOut':
        return cls(
            id=str(intention.id),
            date=intention.intention_date,
            massTime=intention.mass_time or '',
            intentionFor=intention.intention_for or '',
            stipend=float(intention.stipend or 0),
            paid=bool(intention.is_paid),
            notes=intention.notes or '',
        )


class IntentionMutationOut(Schema):
    ok: bool = True
    item: MassIntentionOut


class OkOut(Schema):
    ok: bool = True


class ErrorOut(Schema):
    ok: bool = False
    error: str
