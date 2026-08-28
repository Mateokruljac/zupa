from django.utils.translation import gettext_lazy as _


# DJANGO ADMIN
ADMIN_REORDER = [
    {
        'label': _('Župa — postavke'),
        'description': _(
            'Osnovni podaci župe i veze na referentne kataloške vrijednosti. '
            'Svakodnevni pastoralni unos ostaje u Pastoralu.'
        ),
        'models': (
            'pastoral.Parish',
        ),
    },
    {
        'label': _('Šifrarnici i crkvena struktura'),
        'description': _(
            'Periodični referentni katalozi za dropdown i zadane vrijednosti župe.'
        ),
        'models': (
            'zupa_vjernici.ChurchSuiIuris',
            'zupa_vjernici.EcclesiasticalJurisdiction',
            'liturgija.LiturgicalTradition',
            'pastoral.Diocese',
        ),
    },
    {
        'label': _('Predlošci matičnih knjiga'),
        'description': _(
            'Verzionirani predlošci koje Pastoral koristi pri ispisu i unosu.'
        ),
        'models': (
            'isprave.RegisterTemplate',
            'isprave.RegisterTemplateVersion',
        ),
    },
    {
        'label': _('Liturgijski kalendar'),
        'description': _(
            'Godišnji uvoz svetaca i liturgijskih događaja — ne dnevni unos nakana.'
        ),
        'models': (
            'liturgija.LiturgicalCalendarImport',
            'liturgija.LiturgicalCalendarEntry',
        ),
    },
    {
        'label': _('Korisnici i ovlasti'),
        'description': _(
            'Tko smije u Pastoral i tko ima pristup ovoj tehničkoj administraciji.'
        ),
        'models': (
            'pastoral.User',
            'auth.Group',
        ),
    },
    {
        'label': _('Sigurnost prijave'),
        'description': _('Nadzor OTP challengea bez prikaza tajnog koda.'),
        'models': (
            'pastoral.OtpChallenge',
        ),
    },
]
