from django.utils.translation import gettext_lazy as _


ADMIN_REORDER = [
    {
        'label': _('Župe i podatkovna jezgra'),
        'description': _('Kontrola tenant podataka, postavki i stanja župne evidencije.'),
        'models': (
            'pastoral.Parish',
            'control_plane.Diocese',
            'control_plane.TenantDatabase',
        ),
    },
    {
        'label': _('Liturgijski kalendar'),
        'description': _(
            'Kontrolirani godišnji uvoz svetaca i liturgijskih događaja koje koristi Pastoral.'
        ),
        'models': (
            'pastoral.LiturgicalCalendarImport',
            'pastoral.LiturgicalCalendarEntry',
        ),
    },
    {
        'label': _('Korisnici i ovlasti'),
        'description': _('Tehnički pristup, staff status, grupe i model-permissions.'),
        'models': (
            'users.User',
            'control_plane.ParishMembership',
            'auth.Group',
        ),
    },
    {
        'label': _('Licence i ručne uplate'),
        'description': _('Ručna evidencija uplata, dual control i vremenski ograničena prava korištenja.'),
        'models': (
            'control_plane.ManualPayment',
            'control_plane.LicenseGrant',
            'control_plane.LicenseEntitlement',
            'control_plane.LicenseDecision',
        ),
    },
    {
        'label': _('Javne web-stranice'),
        'description': _('Aktivacija dodatne usluge, domene, predlošci i proizvodni buildovi.'),
        'models': (
            'public_site.ParishWebsite',
            'public_site.ParishWebsiteMedia',
            'public_site.WebsiteBuild',
        ),
    },
    {
        'label': _('Control-plane audit'),
        'description': _('Nepromenjivi trag upravljačkih i sigurnosnih događaja.'),
        'models': (
            'control_plane.ControlPlaneAuditEvent',
        ),
    },
    {
        'label': _('Sigurnost prijave'),
        'description': _('Nadzor OTP challengea bez prikaza samog tajnog koda.'),
        'models': (
            'pastoral.OtpChallenge',
        ),
    },
    {
        'label': _('Izgled administracije'),
        'description': _('Vizualne postavke isključivo klasičnog Django admina.'),
        'models': (
            'admin_interface.Theme',
        ),
    },
]
