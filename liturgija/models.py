"""
ORM modeli liturgije: kalendar slavlja i župni raspored misa.

Dva sloja:
- katalog slavlja (tradicija, kalendarski dan po izvoru)
- operativni zapisi župe (raspored, iznimke, nakane, listić)

Oboje živi u tenant schemi: schema *jest* župa, pa modeli nemaju FK na Parish.

Što se slavi kojeg dana vidi se iz `LiturgicalCalendarEntry`, ne iz zasebne
tablice „misa koja se dogodila”. Raspored kaže *kad župa služi*; kalendar
kaže *što je liturgijski dan*. Imena tablica još su `pastoral_*`.
"""
from core.models import FCTA, FCTB, SCD1
from django.db import models


class LiturgicalTradition(SCD1):
    """Obred slavlja (rimski, bizantski…), ne kanonska pripadnost.

    Latinska župa obično ima rimski obred; župa Križevačke eparhije bizantski.
    Kanonska linija (`latin` / `eastern`) živi na župi, ne ovdje.
    Sakrament može snimiti FK na ovaj red.
    """

    unified_key_origin_fields = ('code',)

    name = models.CharField('Naziv', max_length=50, unique=True)
    description = models.CharField('Opis', max_length=160)

    class Meta:
        db_table = 'pastoral_liturgicaltradition'
        ordering = ('name',)
        verbose_name = 'Liturgijska tradicija'
        verbose_name_plural = 'Liturgijske tradicije'

    def __str__(self):
        return self.name


class LiturgicalCalendarEntry(FCTB):
    """Jedno slavlje na jednom datumu (svagdan, svetac, blagdan…).

    Isti datum smije imati više redaka: npr. ponedjeljak vremena kroz godinu
    i usporedni svetac. Izvor uvoza je `romcal-croatia`; ostaje i ručni unos.
    Ponovni uvoz preskače red koji već postoji za isti izvor, datum i naziv.
    Bitna polja: datum, naziv, prioritet, boja. `is_primary` je slavlje s
    najvišim prioritetom toga dana.
    """

    class Provider(models.TextChoices):
        ROMCAL_CROATIA = 'romcal-croatia', 'Romcal — kalendar za Hrvatsku'
        MANUAL = 'manual', 'Ručni unos'

    class LiturgicalColor(models.TextChoices):
        WHITE = 'white', 'Bijela'
        RED = 'red', 'Crvena'
        GREEN = 'green', 'Zelena'
        PURPLE = 'purple', 'Ljubičasta'
        ROSE = 'rose', 'Ružičasta'
        BLACK = 'black', 'Crna'
        OTHER = 'other', 'Druga / nepoznata'

    provider = models.CharField(
        'Izvor',
        max_length=30,
        choices=Provider.choices,
        default=Provider.ROMCAL_CROATIA,
        db_index=True,
    )
    date = models.DateField('Datum', db_index=True)
    name = models.CharField('Svetac ili slavlje', max_length=255)
    original_name = models.CharField('Izvorni naziv', max_length=255, blank=True)
    liturgical_color = models.CharField(
        'Liturgijska boja',
        max_length=20,
        choices=LiturgicalColor.choices,
        default=LiturgicalColor.OTHER,
        db_index=True,
    )
    priority = models.PositiveSmallIntegerField(
        'Prioritet',
        default=0,
        help_text='Stupanj slavlja; veći broj znači viši prioritet.',
    )
    priority_label = models.CharField('Naziv prioriteta (svetkovina, blagdan, svagdan)', max_length=120, blank=True)
    is_primary = models.BooleanField(
        'Glavno slavlje dana',
        default=True,
        db_index=True,
    )

    class Meta:
        db_table = 'pastoral_liturgicalcalendarentry'
        ordering = ['date', '-priority', 'name']
        verbose_name = 'Liturgijski kalendarski zapis'
        verbose_name_plural = 'Liturgijski kalendarski zapisi'

    def __str__(self):
        return f'{self.date:%d.%m.%Y.} — {self.name}'


class MassScheduleSlot(SCD1):
    """Redoviti termin mise (npr. nedjelja 10:00).

    Predložak tjedna, ne zapis da je misa održana. Živi u tenant schemi
    župe — nema FK na Parish. Liturgijski dan čita se iz kalendara.
    `no_mass` znači da u tom terminu nema mise. Identitet je SCD1 `id`.
    """

    day_label = models.CharField(max_length=80, blank=True)
    mass_time = models.CharField(max_length=20, blank=True)
    weekdays = models.JSONField(default=list, blank=True)
    location = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    no_mass = models.BooleanField(default=False)


class MassException(FCTA):
    """Iznimka rasporeda za jedan datum (blagdan, sprovod, otkaz).

    Tjedni `MassScheduleSlot` ostaje netaknut. Ovaj red kaže što *tog dana*
    odstupa: otkaz svih misa, otkaz pojedinih sati, ili dodatni termini.
    Identitet retka je FCTA `id`. Schema tenanta je župa.
    """

    # Kalendarski dan na koji se iznimka odnosi (jedan red = jedan datum).
    exception_date = models.DateField(null=True, blank=True, db_index=True)
    # True = tog dana se ne uzima nijedan redoviti termin iz rasporeda.
    cancel_all = models.BooleanField(default=False)
    # Sati redovitih misa koji se tog dana otkazuju, npr. ["07:30", "18:00"].
    # Ignorira se ako je `cancel_all` True (tad otpada cijeli raspored).
    cancel_times = models.JSONField(default=list, blank=True)
    # Dodatne mise tog dana, izvan tjednog predloška. Lista dictova:
    # `time`, opcionalno `celebrant`, `location`, `note`.
    add_slots = models.JSONField(default=list, blank=True)
    # Razlog / interna bilješka (sprovod, blagdan, otkaz zbog…); vidi se u UI.
    note = models.TextField(blank=True)
    # Prazan JSON iz starog Parish.data; nije poslovno polje.
    payload = models.JSONField(default=dict, blank=True)


class MassIntention(FCTA):
    """Jedna naručena nakana: za koga, koji dan i sat.

    Stipend i `is_paid` su operativni; primitak novca knjiži se u knjigu
    misnih obveza. Identitet retka je FCTA `id`. Schema tenanta je župa.
    """

    intention_date = models.DateField(blank=False, null=False, db_index=True)
    mass_time = models.CharField(max_length=20, blank=False, null=False)
    intention_for = models.CharField(max_length=255, blank=False, null=False)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)




class BulletinIssue(FCTA):
    """Jedan broj župnog listića za određeno razdoblje.

    Predložak blokova je default u kodu (`zupni_listic_config`). Ovaj red je
    konkretan tjedan: period, naslov, status, snapshot blokova i HTML ispisa.
    Identitet je FCTA `id`. Schema tenanta je župa.
    """

    class Status(models.TextChoices):
        DRAFT = 'nacrt', 'Nacrt'
        PUBLISHED = 'izdan', 'Izdan'

    week_start = models.DateField(
        'Od',
        db_index=True,
        help_text='Početak razdoblja na koje se listić odnosi (obično ponedjeljak).',
    )
    week_end = models.DateField(
        'Do',
        help_text='Kraj razdoblja (obično nedjelja istog tjedna).',
    )
    title = models.CharField('Naslov', max_length=255)
    status = models.CharField(
        'Status',
        max_length=16,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )
    layout = models.JSONField(
        'Blokovi izdanja',
        default=dict,
        blank=True,
        help_text='Snapshot blokova ovog broja (`blocks`), ne predložak župe.',
    )
    rendered_html = models.TextField(
        'HTML ispisa',
        blank=True,
        help_text='Arhiva ispisa; reprint ne ovisi o kasnijim nakanama i rasporedu.',
    )

    class Meta:
        ordering = ('-week_start', '-created_at')
        verbose_name = 'Župni listić'
        verbose_name_plural = 'Župni listići'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(week_end__gte=models.F('week_start')),
                name='listic_week_end_gte_start',
            ),
        ]

    def __str__(self):
        return self.title or f'Listić {self.week_start}–{self.week_end}'

