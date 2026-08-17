import uuid

from django.conf import settings
from django.db import models


class Parish(models.Model):
    """Jedna župa — podaci i postavke (struktura kao bivši localStorage)."""

    class LifecycleStatus(models.TextChoices):
        PROVISIONING = 'provisioning', 'Provisioning'
        ACTIVE = 'active', 'Aktivno'
        SUSPENDED = 'suspended', 'Suspendirano'
        OFFBOARDING = 'offboarding', 'Offboarding'
        ARCHIVED = 'archived', 'Arhivirano'

    tenant_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    slug = models.SlugField(unique=True, default=settings.PARISH_DEFAULT_SLUG)
    diocese = models.ForeignKey(
        'control_plane.Diocese',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parishes',
    )
    lifecycle_status = models.CharField(
        max_length=20,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.ACTIVE,
        db_index=True,
    )
    settings = models.JSONField(default=dict, blank=True)
    data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Župa'
        verbose_name_plural = 'Župe'

    def __str__(self):
        return self.settings.get('name', self.slug)


class OtpChallenge(models.Model):
    """OTP kod za prijavu (demo / produkcija)."""

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    role = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class LiturgicalCalendarImport(models.Model):
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
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
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


class LiturgicalCalendarEntry(models.Model):
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
