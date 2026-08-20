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
        'label': _('Crkvena struktura'),
        'description': _(
            'Kontrolirani referentni podaci za Crkve sui iuris, jurisdikcije i liturgijske tradicije.'
        ),
        'models': (
            'pastoral.ChurchSuiIuris',
            'pastoral.EcclesiasticalJurisdiction',
            'pastoral.LiturgicalTradition',
        ),
    },
    {
        'label': _('Osobe i kanonska pripadnost'),
        'description': _(
            'Osjetljiva tenant evidencija osoba, povijesti pripadnosti i nepromjenjivog matičnog audita.'
        ),
        'models': (
            'pastoral.Person',
            'pastoral.ChurchEnrollment',
            'pastoral.RegistryAuditEvent',
        ),
    },
    {
        'label': _('Matične knjige — predlošci'),
        'description': _(
            'Verzionirani predlošci i pravila prikaza; kompatibilni predložak nije službeni obrazac.'
        ),
        'models': (
            'pastoral.RegisterTemplate',
            'pastoral.RegisterTemplateVersion',
        ),
    },
    {
        'label': _('Sakramentalna priprava'),
        'description': _(
            'Godine, skupine i kandidati prve pričesti i krizme, odvojeni od potvrđenih matičnih činjenica.'
        ),
        'models': (
            'pastoral.FormationProgramYear',
            'pastoral.FormationCandidate',
        ),
    },
    {
        'label': _('Matične knjige — relacijska jezgra'),
        'description': _(
            'Kontrolirani prijelaz postojećih zapisa u događaje, knjige i godine bez promjene aktivnog sučelja.'
        ),
        'models': (
            'pastoral.RegisterBook',
            'pastoral.RegisterBookYear',
            'pastoral.SacramentalEvent',
            'pastoral.EventParticipant',
            'pastoral.BaptismDetails',
            'pastoral.MarriageDetails',
            'pastoral.FuneralDetails',
            'pastoral.AnointingDetails',
            'pastoral.RegisterEntry',
            'pastoral.GeneralRegisterEntry',
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
]
