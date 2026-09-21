"""
ORM modeli liturgije: kalendar slavlja i župni raspored misa.

Dva sloja:
- globalni kalendar (tradicija, slavlje dana po izvoru) — nije tenant
- operativni zapisi župe (raspored, iznimke, nakane, listić) — bivši Parish.data

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

    code = models.SlugField('Stabilni kod', max_length=50, unique=True)
    name = models.CharField('Naziv', max_length=160)

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
    Ponovni uvoz preskače red koji već postoji za isti izvor, datum i
    identifikator slavlja. Bitna polja: datum, naziv, prioritet, boja.
    `is_primary` je slavlje s najvišim prioritetom toga dana.
    """

    class Provider(models.TextChoices):
        LITCAL_VATICAN = 'litcal-va', 'LitCal — opći rimski kalendar'
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
        default=Provider.LITCAL_VATICAN,
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
    priority_label = models.CharField('Naziv prioriteta', max_length=120, blank=True)
    is_primary = models.BooleanField(
        'Glavno slavlje dana',
        default=True,
        db_index=True,
    )
    external_identifier = models.CharField('Identifikator izvora', max_length=160, blank=True)
    raw_data = models.JSONField('Izvorni podaci', default=dict, editable=False)

    class Meta:
        db_table = 'pastoral_liturgicalcalendarentry'
        ordering = ['date', '-priority', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=('provider', 'date', 'external_identifier'),
                name='unique_liturgical_entry_source_celebration',
            ),
        ]
        indexes = [
            models.Index(
                fields=('date', 'is_primary'),
                name='liturgical_date_primary_idx',
            ),
        ]
        verbose_name = 'Liturgijski kalendarski zapis'
        verbose_name_plural = 'Liturgijski kalendarski zapisi'

    def __str__(self):
        return f'{self.date:%d.%m.%Y.} — {self.name}'


class MassScheduleSlot(SCD1):
    """Redoviti termin mise u župi (npr. nedjelja 10:00).

    Predložak tjedna, ne zapis da je misa održana. Liturgijski dan
    (svetac, boja) čita se iz kalendara za taj datum. `no_mass` znači
    da u tom terminu nema mise. `payload` je ostavština starog JSON-a.
    """

    unified_key_origin_fields = ('parish_id', 'public_identifier')

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='mass_schedule_slots',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    day_label = models.CharField(max_length=80, blank=True)
    mass_time = models.CharField(max_length=20, blank=True)
    weekdays = models.JSONField(default=list, blank=True)
    celebrant = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    no_mass = models.BooleanField(default=False)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class MassException(FCTA):
    """Iznimka rasporeda za jedan datum (blagdan, sprovod, otkaz).

    Ne mijenja tjedni predložak. `cancel_all` / `cancel_times` / `add_slots`
    opisuju što tog dana odstupa od `MassScheduleSlot`.
    """

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='mass_exceptions',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    exception_date = models.DateField(null=True, blank=True, db_index=True)
    cancel_all = models.BooleanField(default=False)
    cancel_times = models.JSONField(default=list, blank=True)
    add_slots = models.JSONField(default=list, blank=True)
    note = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class MassScheduleLogEntry(FCTA):
    """Kratka poruka uz izmjenu rasporeda, nije kalendarski događaj.

    `logged_at` je naslijeđeni tekst, ne DateTime.
    """

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='mass_schedule_log_entries',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    logged_at = models.CharField(max_length=64, blank=True)
    message = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class MassIntention(FCTA):
    """Jedna naručena nakana (za koga, tko traži, koji termin).

    Status je pastoralni tijek, ne knjiga računa. Stipend i `is_paid`
    ovdje su operativni; primitak novca knjiži se u knjigu misnih obveza.
    """

    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Zatraženo'
        SCHEDULED = 'scheduled', 'Raspoređeno'
        FULFILLED = 'fulfilled', 'Ispunjeno'
        TRANSFERRED = 'transferred', 'Upućeno'
        CANCELLED = 'cancelled', 'Otkazano'

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='mass_intentions',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    intention_date = models.DateField(null=True, blank=True, db_index=True)
    mass_time = models.CharField(max_length=20, blank=True)
    requested_by = models.CharField(max_length=160, blank=True)
    intention_for = models.CharField(max_length=255, blank=True)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        blank=True,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class BulletinLayout(models.Model):
    """Raspored župnog listića: jedna župa, jedan red (PK = parish).

    Sadržaj još nije tipiziran (`payload` / `template_payload`).
    Nakane i slavlja dana listić čita iz nakana i liturgijskog kalendara
    pri ispisu, ne kopira ih ovdje.
    """

    parish = models.OneToOneField(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='bulletin_layout',
        primary_key=True,
    )
    payload = models.JSONField(default=dict, blank=True)
    template_payload = models.JSONField(null=True, blank=True)
    unified_key = models.CharField(max_length=512, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.unified_key = str(self.parish_id or self.unified_key)
        return super().save(*args, **kwargs)


class BulletinIssue(FCTA):
    """Jedan izdani broj župnog listića.

    Tijelo je još u `payload`. Nije arhiva održanih misa.
    """

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='bulletin_issues',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]
