"""ORM modeli isprava i matičnih knjiga."""
import uuid

from core.models import FCTA, SCD1
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from zupa_vjernici.canonical import CanonicalTradition

# Isti skup tipova događaja kao sakramenti.SacramentalEvent.EventType
# (bez importa modela radi kružnih ovisnosti).
EVENT_TYPE_CHOICES = (
    ('baptism', 'Krštenje'),
    ('first_communion', 'Prva pričest'),
    ('confirmation', 'Krizma'),
    ('marriage', 'Vjenčanje'),
    ('anointing', 'Pomazanje'),
    ('funeral', 'Sprovod'),
)
from django_multitenant.schema import with_tenant_schema


class RegistryAuditEvent(FCTA):
    """Nepromenjivi tenant-svjestan trag osjetljivih matičnih radnji."""

    class Outcome(models.TextChoices):
        SUCCESS = 'success', 'Uspjeh'
        DENIED = 'denied', 'Odbijeno'
        FAILURE = 'failure', 'Greška'

    parish = models.ForeignKey('pastoral.Parish',
        verbose_name='Župa',
        on_delete=models.PROTECT,
        related_name='registry_audit_events',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Korisnik',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='registry_audit_events',
    )
    event_type = models.CharField('Vrsta događaja', max_length=100, db_index=True)
    target_type = models.CharField('Vrsta cilja', max_length=100, blank=True)
    target_id = models.CharField('Identifikator cilja', max_length=100, blank=True)
    outcome = models.CharField(
        'Ishod',
        max_length=16,
        choices=Outcome.choices,
        default=Outcome.SUCCESS,
        db_index=True,
    )
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    changed_fields = models.JSONField('Promijenjena polja', default=list, blank=True)
    metadata = models.JSONField('Metapodaci', default=dict, blank=True)
    occurred_at = models.DateTimeField('Vrijeme', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'pastoral_registryauditevent'
        ordering = ('-occurred_at',)
        indexes = (
            models.Index(
                fields=('parish', 'occurred_at'),
                name='registry_audit_parish_time',
            ),
            models.Index(
                fields=('actor', 'occurred_at'),
                name='registry_audit_actor_time',
            ),
        )
        verbose_name = 'Audit matične evidencije'
        verbose_name_plural = 'Audit matične evidencije'

    def __str__(self):
        return f'{self.event_type} · {self.get_outcome_display()}'

    @with_tenant_schema
    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError('Audit događaj je nepromjenjiv.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Audit događaj se ne smije brisati.')


class RegisterTemplate(SCD1):
    """A governed template identity; field definitions live in versions."""

    class OwnerScope(models.TextChoices):
        SYSTEM = 'system', 'Sustav'
        CHURCH = 'church', 'Kanonska tradicija'
        JURISDICTION = 'jurisdiction', 'Crkvena jurisdikcija'

    unified_key_origin_fields = ('code',)

    code = models.SlugField('Stabilni kod', max_length=100, unique=True)
    event_type = models.CharField(
        'Vrsta sakramenta', max_length=24, choices=EVENT_TYPE_CHOICES
    )
    name = models.CharField('Naziv', max_length=220)
    owner_scope = models.CharField(
        'Vlasnik', max_length=16, choices=OwnerScope.choices, default=OwnerScope.SYSTEM
    )
    canonical_tradition = models.CharField(
        'Kanonska tradicija',
        max_length=16,
        choices=CanonicalTradition.choices,
        blank=True,
        db_index=True,
        help_text='Latinska ili istočna (Križevačka eparhija), ako predložak nije opći.',
    )
    ecclesiastical_jurisdiction = models.ForeignKey('zupa_vjernici.EcclesiasticalJurisdiction', verbose_name='Crkvena jurisdikcija',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='register_templates',
    )
    is_official = models.BooleanField('Službeni obrazac', default=False)

    class Meta:
        db_table = 'pastoral_registertemplate'
        ordering = ('event_type', 'name')
        verbose_name = 'Predložak matične knjige'
        verbose_name_plural = 'Predlošci matičnih knjiga'

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        validation_errors = {}
        if self.owner_scope == self.OwnerScope.CHURCH and not self.canonical_tradition:
            validation_errors['canonical_tradition'] = (
                'Odaberite kanonsku tradiciju (latinska ili istočna).'
            )
        if self.owner_scope == self.OwnerScope.JURISDICTION and not self.ecclesiastical_jurisdiction_id:
            validation_errors['ecclesiastical_jurisdiction'] = 'Odaberite crkvenu jurisdikciju.'
        if validation_errors:
            raise ValidationError(validation_errors)


class RegisterTemplateVersion(SCD1):
    """Immutable-in-practice schema and print configuration for a template."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nacrt'
        PUBLISHED = 'published', 'Objavljeno'
        RETIRED = 'retired', 'Povučeno'

    unified_key_origin_fields = ('template_id', 'version_number')

    template = models.ForeignKey('isprave.RegisterTemplate', verbose_name='Predložak', on_delete=models.PROTECT,
        related_name='versions',
    )
    version_number = models.PositiveSmallIntegerField('Verzija')
    status = models.CharField(
        'Status', max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    field_schema = models.JSONField('Definicije polja', default=list, blank=True)
    validation_schema = models.JSONField('Pravila validacije', default=dict, blank=True)
    terminology = models.JSONField('Terminologija', default=dict, blank=True)
    print_configuration = models.JSONField('Postavke ispisa', default=dict, blank=True)
    effective_from = models.DateField('Vrijedi od', null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Objavio', on_delete=models.PROTECT,
        null=True, blank=True, related_name='published_register_template_versions',
    )
    published_at = models.DateTimeField('Objavljeno', null=True, blank=True)

    class Meta:
        db_table = 'pastoral_registertemplateversion'
        ordering = ('template', '-version_number')
        constraints = (
            models.UniqueConstraint(
                fields=('template', 'version_number'), name='unique_register_template_version'
            ),
        )
        verbose_name = 'Verzija predloška matične knjige'
        verbose_name_plural = 'Verzije predložaka matičnih knjiga'

    def __str__(self):
        return f'{self.template} · v{self.version_number}'

    @with_tenant_schema
    def _validate_published_version_is_unchanged(self):
        if self.pk:
            previous_version = type(self).objects.filter(pk=self.pk).first()
            if previous_version and previous_version.status == self.Status.PUBLISHED:
                raise ValidationError(
                    'Objavljena verzija predloška je nepromjenjiva. Izradite novu verziju.'
                )

    def clean(self):
        super().clean()
        self._validate_published_version_is_unchanged()

    @with_tenant_schema
    def save(self, *args, **kwargs):
        self._validate_published_version_is_unchanged()
        return super().save(*args, **kwargs)

    @with_tenant_schema
    def delete(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED:
            raise ValidationError(
                'Objavljena verzija predloška ne može se brisati.'
            )
        return super().delete(*args, **kwargs)


class RegisterBook(SCD1):
    """A physical or logical register book owned by one parish."""

    class RegistryType(models.TextChoices):
        BAPTISMS = 'krštenja', 'Krštenja'
        MARRIAGES = 'vjenčanja', 'Vjenčanja'
        DECEASED = 'umrli', 'Umrli'
        CONFIRMATIONS = 'krizma', 'Krizma'
        OTHER = 'ostalo', 'Ostalo'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nacrt'
        ACTIVE = 'active', 'Aktivna'
        LOCKED = 'locked', 'Zaključana'
        ARCHIVED = 'archived', 'Arhivirana'

    unified_key_origin_fields = ('parish_id', 'public_identifier')

    public_identifier = models.CharField(
        'Stabilni identifikator', max_length=160, blank=True
    )
    parish = models.ForeignKey('pastoral.Parish', verbose_name='Župa', on_delete=models.PROTECT, related_name='register_books'
    )
    template_version = models.ForeignKey('isprave.RegisterTemplateVersion', verbose_name='Verzija predloška',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='register_books',
    )
    title = models.CharField('Naziv', max_length=220)
    registry_type = models.CharField(
        'Vrsta knjige', max_length=20,
        choices=RegistryType.choices, default=RegistryType.OTHER,
    )
    volume = models.CharField('Svezak', max_length=80, blank=True)
    year_from = models.PositiveSmallIntegerField('Od godine', null=True, blank=True)
    year_until = models.PositiveSmallIntegerField('Do godine', null=True, blank=True)
    location = models.CharField('Mjesto čuvanja', max_length=200, blank=True)
    custodian = models.CharField('Odgovorna osoba', max_length=200, blank=True)
    status = models.CharField(
        'Status', max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    operational_status = models.CharField(
        'Opis statusa', max_length=80, blank=True
    )
    last_entry_date = models.DateField('Zadnji unos', null=True, blank=True)
    last_entry_reference = models.CharField(
        'Zadnji broj', max_length=80, blank=True
    )
    notes = models.TextField('Napomena', blank=True)

    class Meta:
        db_table = 'pastoral_registerbook'
        ordering = ('parish', 'title')
        indexes = (models.Index(fields=('parish', 'status'), name='book_parish_status'),)
        constraints = (
            models.UniqueConstraint(
                fields=('parish', 'public_identifier'),
                condition=~Q(public_identifier=''),
                name='unique_register_book_public_identifier',
            ),
        )
        verbose_name = 'Matična knjiga'
        verbose_name_plural = 'Matične knjige'

    def __str__(self):
        return f'{self.parish} · {self.title}'

    def clean(self):
        super().clean()
        if self.year_from and self.year_until and self.year_until < self.year_from:
            raise ValidationError({'year_until': 'Završna godina ne smije biti prije početne.'})


class RegisterBookYear(SCD1):
    """An explicitly opened year, including empty retroactive years."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Otvorena'
        LOCKED = 'locked', 'Zaključana'
        ARCHIVED = 'archived', 'Arhivirana'

    unified_key_origin_fields = ('register_book_id', 'year')

    register_book = models.ForeignKey('isprave.RegisterBook', verbose_name='Matična knjiga', on_delete=models.PROTECT,
        related_name='years',
    )
    year = models.PositiveSmallIntegerField('Godina')
    status = models.CharField(
        'Status', max_length=12, choices=Status.choices, default=Status.OPEN
    )
    next_entry_number = models.PositiveIntegerField('Sljedeći redni broj', default=1)

    class Meta:
        db_table = 'pastoral_registerbookyear'
        ordering = ('register_book', '-year')
        constraints = (
            models.UniqueConstraint(
                fields=('register_book', 'year'), name='unique_register_book_year'
            ),
        )
        verbose_name = 'Godina matične knjige'
        verbose_name_plural = 'Godine matičnih knjiga'

    def __str__(self):
        return f'{self.register_book.title} · {self.year}'


class GeneralRegisterEntry(FCTA):
    """A non-sacramental entry in a parish register book."""

    public_identifier = models.CharField('Stabilni identifikator', max_length=160)
    register_book_year = models.ForeignKey('isprave.RegisterBookYear',
        verbose_name='Godina knjige',
        on_delete=models.PROTECT,
        related_name='general_entries',
    )
    registry_reference = models.CharField('Matični broj', max_length=100, blank=True)
    subject_name = models.CharField('Osoba / zapis', max_length=240)
    record_date = models.DateField('Datum zapisa')
    place = models.CharField('Mjesto / napomena', max_length=240, blank=True)
    responsible_name = models.CharField(
        'Odgovorna osoba', max_length=200, blank=True
    )
    operational_status = models.CharField(
        'Status', max_length=60, default='upisano', db_index=True
    )

    class Meta:
        db_table = 'pastoral_generalregisterentry'
        ordering = ('register_book_year', 'record_date', 'created_at')
        constraints = (
            models.UniqueConstraint(
                fields=('register_book_year', 'public_identifier'),
                name='unique_general_entry_identifier',
            ),
        )
        verbose_name = 'Opći zapis matične knjige'
        verbose_name_plural = 'Opći zapisi matične knjige'

    def __str__(self):
        return self.registry_reference or self.subject_name


class RegisterEntry(FCTA):
    """A register-book entry linked to the underlying sacramental event."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nacrt'
        CONFIRMED = 'confirmed', 'Potvrđeno'
        LOCKED = 'locked', 'Zaključano'
        CORRECTED = 'corrected', 'Ispravljeno'
        CANCELLED = 'cancelled', 'Poništeno'
        LEGACY_IMPORTED = 'legacy_imported', 'Uvezeno iz postojećeg sustava'

    parish = models.ForeignKey('pastoral.Parish', verbose_name='Župa', on_delete=models.PROTECT,
        related_name='register_entries',
    )
    register_book_year = models.ForeignKey('isprave.RegisterBookYear', verbose_name='Godina knjige', on_delete=models.PROTECT,
        related_name='entries',
    )
    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Događaj', on_delete=models.PROTECT,
        related_name='register_entry',
    )
    template_version = models.ForeignKey('isprave.RegisterTemplateVersion', verbose_name='Verzija predloška',
        on_delete=models.PROTECT, related_name='register_entries',
    )
    entry_number = models.PositiveIntegerField('Redni broj', null=True, blank=True)
    entry_reference = models.CharField('Izvorna oznaka zapisa', max_length=100, blank=True)
    page_number = models.CharField('Stranica', max_length=40, blank=True)
    entry_date = models.DateField('Datum upisa', null=True, blank=True)
    status = models.CharField(
        'Status', max_length=24, choices=Status.choices,
        default=Status.DRAFT, db_index=True,
    )
    custom_values = models.JSONField('Dodatna polja predloška', default=dict, blank=True)
    previous_entry = models.ForeignKey(
        'self', verbose_name='Prethodni zapis', on_delete=models.PROTECT,
        null=True, blank=True, related_name='correction_entries',
    )
    correction_reason = models.TextField('Razlog ispravka', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Kreirao', on_delete=models.PROTECT,
        null=True, blank=True, related_name='created_register_entries',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Ažurirao', on_delete=models.PROTECT,
        null=True, blank=True,         related_name='updated_register_entries',
    )

    class Meta:
        db_table = 'pastoral_registerentry'
        ordering = ('register_book_year', 'entry_number', 'created_at')
        constraints = (
            models.UniqueConstraint(
                fields=('register_book_year', 'entry_number'),
                condition=Q(entry_number__isnull=False),
                name='unique_number_in_register_book_year',
            ),
        )
        indexes = (
            models.Index(fields=('parish', 'status'), name='entry_parish_status'),
        )
        verbose_name = 'Zapis matične knjige'
        verbose_name_plural = 'Zapisi matičnih knjiga'

    def __str__(self):
        return self.entry_reference or str(self.entry_number or self.id)

    def clean(self):
        super().clean()
        validation_errors = {}
        if self.event_id and self.event.parish_id != self.parish_id:
            validation_errors['event'] = 'Događaj mora pripadati istoj župi.'
        if (
            self.register_book_year_id
            and self.register_book_year.register_book.parish_id != self.parish_id
        ):
            validation_errors['register_book_year'] = 'Knjiga mora pripadati istoj župi.'
        if self.previous_entry_id and self.previous_entry.parish_id != self.parish_id:
            validation_errors['previous_entry'] = 'Prethodni zapis mora pripadati istoj župi.'
        if validation_errors:
            raise ValidationError(validation_errors)
        self._validate_locked_entry_is_unchanged()

    @with_tenant_schema
    def _validate_locked_entry_is_unchanged(self):
        if self.pk:
            previous_status = type(self).objects.filter(pk=self.pk).values_list(
                'status', flat=True
            ).first()
            if previous_status == self.Status.LOCKED:
                raise ValidationError(
                    'Zaključani matični upis ne može se izravno mijenjati.'
                )

    @with_tenant_schema
    def save(self, *args, **kwargs):
        self._validate_locked_entry_is_unchanged()
        return super().save(*args, **kwargs)

    @with_tenant_schema
    def delete(self, *args, **kwargs):
        if self.status == self.Status.LOCKED:
            raise ValidationError('Zaključani matični upis ne može se brisati.')
        return super().delete(*args, **kwargs)
