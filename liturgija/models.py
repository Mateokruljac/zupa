"""ORM modeli liturgijskog kalendara."""
import uuid

from core.models import FCTA, FCTB, SCD1, ContentHashedModel
from django.conf import settings
from django.db import models


class LiturgicalTradition(SCD1):
    """Kontrolirani globalni popis liturgijskih tradicija."""

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


class LiturgicalCalendarImport(FCTB):
    """Provjereni godišnji kalendar koji je uvezen kroz Django admin."""

    class Provider(models.TextChoices):
        LITCAL_VATICAN = 'litcal-va', 'LitCal — opći rimski kalendar'

    year = models.PositiveSmallIntegerField('Godina')
    provider = models.CharField(
        'Izvor',
        max_length=30,
        choices=Provider.choices,
        default=Provider.LITCAL_VATICAN,
    )
    events = models.JSONField('Uvezeni događaji', default=list, editable=False)
    event_count = models.PositiveIntegerField('Broj događaja', default=0, editable=False)
    source_file_name = models.CharField('Izvorna datoteka', max_length=255, blank=True, editable=False)
    checksum = models.CharField('SHA-256 kontrolni zbroj', max_length=64, blank=True, editable=False)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Uvezao',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='liturgical_calendar_imports',
    )
    imported_at = models.DateTimeField('Vrijeme uvoza', null=True, blank=True, editable=False)

    class Meta:
        db_table = 'pastoral_liturgicalcalendarimport'
        ordering = ['-year', 'provider']
        constraints = [
            models.UniqueConstraint(
                fields=('year', 'provider'),
                name='unique_liturgical_calendar_import',
            ),
        ]
        verbose_name = 'Uvoz liturgijskog kalendara'
        verbose_name_plural = 'Uvozi liturgijskog kalendara'

    def __str__(self):
        return f'{self.get_provider_display()} — {self.year}'


class LiturgicalCalendarEntry(FCTB):
    """Globalno liturgijsko slavlje dobiveno iz kontroliranog importa."""

    class LiturgicalColor(models.TextChoices):
        WHITE = 'white', 'Bijela'
        RED = 'red', 'Crvena'
        GREEN = 'green', 'Zelena'
        PURPLE = 'purple', 'Ljubičasta'
        ROSE = 'rose', 'Ružičasta'
        BLACK = 'black', 'Crna'
        OTHER = 'other', 'Druga / nepoznata'

    calendar_import = models.ForeignKey(
        LiturgicalCalendarImport,
        verbose_name='Kalendarski import',
        on_delete=models.CASCADE,
        related_name='calendar_entries',
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
        help_text='LitCal stupanj slavlja; veći broj znači viši prioritet.',
    )
    priority_label = models.CharField('Naziv prioriteta', max_length=120, blank=True)
    is_primary = models.BooleanField(
        'Glavno slavlje dana',
        default=False,
        db_index=True,
    )
    external_identifier = models.CharField('Identifikator izvora', max_length=160, blank=True)
    source_position = models.PositiveIntegerField('Redni broj u importu')
    raw_data = models.JSONField('Izvorni podaci', default=dict, editable=False)

    class Meta:
        db_table = 'pastoral_liturgicalcalendarentry'
        ordering = ['date', '-is_primary', '-priority', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=('calendar_import', 'source_position'),
                name='unique_liturgical_entry_source_position',
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


# --- Operativni liturgijski zapisi (bivši Parish.data) ---


class MassScheduleSlot(SCD1):
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


class BulletinLayout(ContentHashedModel):
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
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='bulletin_issues',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]

