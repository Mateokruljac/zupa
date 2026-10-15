"""Ulaz i izlaz Ninja API-ja za karticu obitelji.

Ulaz prati nazive polja na formi. Izlaz je samo kartica koja je otvorena
u modalu, ne cijela stranica obitelji.
"""
from datetime import date

from ninja import Schema
from pydantic import ConfigDict, Field


class FamilyBasicsWrite(Schema):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)

    surname: str = ''
    street_id: str = ''
    address: str = ''
    phone: str = ''
    email: str = ''
    status: str = 'aktivna'


class FamilyMemberWrite(Schema):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)

    given_name: str = ''
    surname: str = ''
    relation: str = ''
    birth_date: date | None = None
    member_id: str = ''


class FamilyContributionWrite(Schema):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)

    year: int | None = None
    lukno_amount: float | None = None
    lukno_paid: bool = False
    lukno_paid_at: date | None = None
    church_donation: float | None = None
    donation_date: date | None = None
    notes: str = ''


class FamilyNotesWrite(Schema):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)

    pastoral_notes: str = ''


class FamilyMemberOut(Schema):
    id: str
    givenName: str
    surname: str
    name: str
    relation: str
    birthDate: str
    birthYear: str


class FamilyContributionOut(Schema):
    year: int
    luknoAmount: float
    luknoPaid: bool
    luknoPaidAt: str
    churchDonation: float
    donationDate: str
    notes: str


class FamilyCardOut(Schema):
    id: str
    surname: str
    address: str
    phone: str
    email: str
    status: str
    streetId: str
    streetName: str
    pastoralNotes: str
    dataGaps: list[str]
    currentYear: int
    luknoStatus: str
    members: list[FamilyMemberOut]
    contributions: list[FamilyContributionOut]


class FamilyCardMutationOut(Schema):
    ok: bool = True
    message: str
    card: FamilyCardOut


class FamilyCardErrorOut(Schema):
    ok: bool = False
    error: str
    fields: dict[str, list[str]] = Field(default_factory=dict)
