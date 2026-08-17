from datetime import date
from enum import StrEnum

from control_plane.models import LicenseGrant


class LicenseAccess(StrEnum):
    FULL = 'full'
    READ_ONLY = 'read_only'
    ONBOARDING_ONLY = 'onboarding_only'
    DENIED = 'denied'


def evaluate_license(grant: LicenseGrant | None, today: date | None = None) -> LicenseAccess:
    today = today or date.today()
    if grant is None:
        return LicenseAccess.DENIED
    if grant.security_suspended or grant.status in {
        LicenseGrant.Status.SUSPENDED,
        LicenseGrant.Status.TERMINATED,
    }:
        return LicenseAccess.DENIED
    if grant.status == LicenseGrant.Status.PENDING:
        return LicenseAccess.ONBOARDING_ONLY
    if grant.valid_from <= today <= grant.valid_until:
        return LicenseAccess.FULL
    if grant.valid_until < today <= grant.grace_until:
        return LicenseAccess.FULL
    return LicenseAccess.READ_ONLY


def current_license_for(parish, today: date | None = None):
    today = today or date.today()
    return (
        parish.license_grants
        .exclude(status=LicenseGrant.Status.TERMINATED)
        .filter(valid_from__lte=today)
        .order_by('-valid_until', '-created_at')
        .first()
    )

