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
    notes: str = ''
    member_id: str = ''


class FamilyContributionWrite(Schema):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)

    contribution_id: str = ''
    year: int | None = None
    category: str = 'lukno'
    amount: float | None = None
    paid_at: date | None = None
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
    notes: str = ''


class FamilyContributionOut(Schema):
    id: str = ''
    year: int
    category: str = 'lukno'
    categoryLabel: str = 'Lukno'
    luknoAmount: float
    luknoPaid: bool
    luknoPaidAt: str
    churchDonation: float
    donationDate: str
    notes: str


class MembershipTimelineEventOut(Schema):
    id: str
    type: str
    at: str
    memberId: str
    name: str
    relation: str = ''
    relationFrom: str = ''
    relationTo: str = ''
    label: str
    detail: str = ''


class ContributionCategoryTotalOut(Schema):
    category: str
    label: str
    total: float


class ContributionYearTotalOut(Schema):
    year: int
    total: float
    byCategory: list[ContributionCategoryTotalOut] = Field(default_factory=list)


class ContributionTotalsOut(Schema):
    byYear: list[ContributionYearTotalOut] = Field(default_factory=list)
    byCategory: list[ContributionCategoryTotalOut] = Field(default_factory=list)
    grandTotal: float = 0


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
    lastVisitOn: str = ''
    lastVisitDays: int | None = None
    needsPastoralFollowup: bool = False
    members: list[FamilyMemberOut]
    contributions: list[FamilyContributionOut]
    contributionTotals: ContributionTotalsOut = Field(
        default_factory=ContributionTotalsOut,
    )
    membershipTimeline: list[MembershipTimelineEventOut] = Field(
        default_factory=list,
    )


class FamilyCardMutationOut(Schema):
    ok: bool = True
    message: str
    card: FamilyCardOut


class FamilyDeleteOut(Schema):
    ok: bool = True
    message: str


class FamilyCardErrorOut(Schema):
    ok: bool = False
    error: str
    fields: dict[str, list[str]] = Field(default_factory=dict)
