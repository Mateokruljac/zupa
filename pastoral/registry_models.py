import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .models import (
    ChurchSuiIuris,
    EcclesiasticalJurisdiction,
    LiturgicalTradition,
    Parish,
    Person,
)


class SacramentalEvent(models.Model):
    """A sacramental fact, independent from its register-book presentation."""

    class EventType(models.TextChoices):
        BAPTISM = 'baptism', 'Krštenje'
        FIRST_COMMUNION = 'first_communion', 'Prva pričest'
        CONFIRMATION = 'confirmation', 'Krizma'
        MARRIAGE = 'marriage', 'Vjenčanje'
        ANOINTING = 'anointing', 'Pomazanje'
        FUNERAL = 'funeral', 'Sprovod'

    class CanonicalTradition(models.TextChoices):
        LATIN = 'latin', 'Latinska'
        EASTERN = 'eastern', 'Istočna'
        UNCONFIRMED = 'unconfirmed', 'Nepotvrđeno'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nacrt'
        CONFIRMED = 'confirmed', 'Potvrđeno'
        LOCKED = 'locked', 'Zaključano'
        CORRECTED = 'corrected', 'Ispravljeno'
        CANCELLED = 'cancelled', 'Poništeno'
        LEGACY_IMPORTED = 'legacy_imported', 'Uvezeno iz postojećeg sustava'

    class Source(models.TextChoices):
        MANUAL = 'manual', 'Ručni unos'
        PUBLIC_SUBMISSION = 'public_submission', 'Javna prijava'
        LEGACY_IMPORT = 'legacy_import', 'Postojeći sustav'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_identifier = models.CharField(
        'Stabilni identifikator',
        max_length=160,
        blank=True,
        help_text='Stabilni identifikator koji koriste URL-ovi i korisničko sučelje.',
    )
    parish = models.ForeignKey(
        Parish, verbose_name='Župa', on_delete=models.PROTECT,
        related_name='sacramental_events',
    )
    event_type = models.CharField(
        'Vrsta sakramenta', max_length=24, choices=EventType.choices, db_index=True
    )
    event_date = models.DateField('Datum', null=True, blank=True, db_index=True)
    place_name = models.CharField('Mjesto', max_length=200, blank=True)
    celebrating_parish = models.ForeignKey(
        Parish, verbose_name='Župa slavlja', on_delete=models.PROTECT,
        null=True, blank=True, related_name='celebrated_sacramental_events',
    )
    minister = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Služitelj', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ministered_sacramental_events',
    )
    minister_name = models.CharField('Povijesni naziv služitelja', max_length=200, blank=True)
    liturgical_tradition = models.ForeignKey(
        LiturgicalTradition, verbose_name='Liturgijska tradicija',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='sacramental_events',
    )
    canonical_tradition = models.CharField(
        'Kanonska tradicija', max_length=16,
        choices=CanonicalTradition.choices,
        default=CanonicalTradition.UNCONFIRMED,
    )
    status = models.CharField(
        'Status', max_length=24, choices=Status.choices,
        default=Status.DRAFT, db_index=True,
    )
    source = models.CharField(
        'Izvor', max_length=24, choices=Source.choices,
        default=Source.MANUAL, db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Kreirao', on_delete=models.PROTECT,
        null=True, blank=True, related_name='created_sacramental_events',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Ažurirao', on_delete=models.PROTECT,
        null=True, blank=True, related_name='updated_sacramental_events',
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('-event_date', '-created_at')
        indexes = (
            models.Index(fields=('parish', 'event_type', 'event_date'), name='event_parish_type_date'),
            models.Index(fields=('parish', 'status'), name='event_parish_status'),
        )
        constraints = (
            models.UniqueConstraint(
                fields=('parish', 'event_type', 'public_identifier'),
                condition=~Q(public_identifier=''),
                name='unique_event_public_identifier',
            ),
        )
        verbose_name = 'Sakramentalni događaj'
        verbose_name_plural = 'Sakramentalni događaji'

    def __str__(self):
        return f'{self.get_event_type_display()} · {self.event_date or "bez datuma"}'

    def clean(self):
        super().clean()
        if self.celebrating_parish_id and self.celebrating_parish_id != self.parish_id:
            raise ValidationError({
                'celebrating_parish': 'Župa slavlja mora biti jednaka župi zapisa.'
            })
        self._validate_locked_event_is_unchanged()

    def _validate_locked_event_is_unchanged(self):
        if self.pk:
            previous_status = type(self).objects.filter(pk=self.pk).values_list(
                'status', flat=True
            ).first()
            if previous_status == self.Status.LOCKED:
                raise ValidationError(
                    'Zaključani sakramentalni događaj ne može se izravno mijenjati.'
                )

    def save(self, *args, **kwargs):
        self._validate_locked_event_is_unchanged()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == self.Status.LOCKED:
            raise ValidationError('Zaključani sakramentalni događaj ne može se brisati.')
        return super().delete(*args, **kwargs)


class EventParticipant(models.Model):
    """A person or an unparsed historical name participating in an event."""

    class Role(models.TextChoices):
        RECIPIENT = 'recipient', 'Primatelj'
        PARENT = 'parent', 'Roditelj'
        GODPARENT = 'godparent', 'Kum / kuma'
        SPOUSE = 'spouse', 'Zaručnik / zaručnica'
        WITNESS = 'witness', 'Svjedok'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish = models.ForeignKey(
        Parish, verbose_name='Župa', on_delete=models.PROTECT,
        related_name='sacramental_event_participants',
    )
    event = models.ForeignKey(
        SacramentalEvent, verbose_name='Događaj', on_delete=models.PROTECT,
        related_name='participants',
    )
    person = models.ForeignKey(
        Person, verbose_name='Osoba', on_delete=models.PROTECT,
        null=True, blank=True, related_name='sacramental_participations',
    )
    role = models.CharField('Uloga', max_length=20, choices=Role.choices, db_index=True)
    historical_name = models.CharField(
        'Povijesni zapis imena', max_length=300, blank=True,
        help_text='Čuva izvorni tekst kada osobe nije sigurno automatski razdvojiti.',
    )
    display_order = models.PositiveSmallIntegerField('Redoslijed prikaza', default=0)

    class Meta:
        ordering = ('display_order', 'id')
        constraints = (
            models.CheckConstraint(
                condition=Q(person__isnull=False) | ~Q(historical_name=''),
                name='participant_has_person_or_name',
            ),
        )
        indexes = (
            models.Index(fields=('parish', 'role'), name='participant_parish_role'),
        )
        verbose_name = 'Sudionik sakramentalnog događaja'
        verbose_name_plural = 'Sudionici sakramentalnih događaja'

    def __str__(self):
        return self.historical_name or str(self.person)

    def clean(self):
        super().clean()
        validation_errors = {}
        if self.event_id and self.event.parish_id != self.parish_id:
            validation_errors['event'] = 'Događaj mora pripadati istoj župi.'
        if self.person_id and self.person.parish_id != self.parish_id:
            validation_errors['person'] = 'Osoba mora pripadati istoj župi.'
        if not self.person_id and not self.historical_name.strip():
            validation_errors['historical_name'] = 'Upišite osobu ili povijesni zapis imena.'
        if validation_errors:
            raise ValidationError(validation_errors)


class BaptismDetails(models.Model):
    """Data used only by baptism events."""

    event = models.OneToOneField(
        SacramentalEvent, verbose_name='Krštenje', on_delete=models.PROTECT,
        related_name='baptism_details',
    )
    godparent_certificate_received = models.BooleanField(
        'Zaprimljena potvrda za kuma', default=False
    )
    operational_status = models.CharField(
        'Operativni status', max_length=40, default='upis', db_index=True
    )
    stipend = models.DecimalField(
        'Prilog', max_digits=10, decimal_places=2, default=0
    )
    stipend_paid = models.BooleanField('Prilog evidentiran', default=False)

    class Meta:
        verbose_name = 'Podaci o krštenju'
        verbose_name_plural = 'Podaci o krštenjima'

    def __str__(self):
        return str(self.event)

    def clean(self):
        super().clean()
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.BAPTISM:
            raise ValidationError({'event': 'Podaci o krštenju mogu pripadati samo krštenju.'})


class MarriageDetails(models.Model):
    """Operational details specific to a marriage preparation and celebration."""

    event = models.OneToOneField(
        SacramentalEvent, verbose_name='Vjenčanje', on_delete=models.PROTECT,
        related_name='marriage_details',
    )
    couple_display_name = models.CharField('Mladenci', max_length=320)
    contact = models.CharField('Kontakt', max_length=160, blank=True)
    preparatory_sessions = models.PositiveSmallIntegerField(
        'Broj susreta priprave', default=0
    )
    documents_complete = models.BooleanField('Dokumenti potpuni', default=False)
    witnesses_name = models.CharField('Svjedoci', max_length=400, blank=True)
    groom_witness_name = models.CharField(
        'Svjedok zaručnika', max_length=220, blank=True
    )
    bride_witness_name = models.CharField(
        'Svjedok zaručnice', max_length=220, blank=True
    )
    operational_status = models.CharField(
        'Operativni status', max_length=40, default='planirano', db_index=True
    )
    stipend = models.DecimalField(
        'Stipendij', max_digits=10, decimal_places=2, default=0
    )
    stipend_paid = models.BooleanField('Stipendij evidentiran', default=False)

    class Meta:
        verbose_name = 'Podaci o vjenčanju'
        verbose_name_plural = 'Podaci o vjenčanjima'

    def __str__(self):
        return self.couple_display_name

    def clean(self):
        super().clean()
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.MARRIAGE:
            raise ValidationError({'event': 'Podaci o vjenčanju mogu pripadati samo vjenčanju.'})


class FuneralDetails(models.Model):
    """Operational and pastoral details specific to a funeral."""

    event = models.OneToOneField(
        SacramentalEvent, verbose_name='Pogreb', on_delete=models.PROTECT,
        related_name='funeral_details',
    )
    death_date = models.DateField('Datum smrti', null=True, blank=True)
    cemetery_location = models.CharField(
        'Adresa / lokacija groblja', max_length=240, blank=True
    )
    family_contact = models.CharField('Kontakt obitelji', max_length=240, blank=True)
    mass_planned = models.BooleanField('Misa zadušnica planirana', default=False)
    mass_date = models.DateField('Datum mise zadušnice', null=True, blank=True)
    mass_time = models.TimeField('Vrijeme mise zadušnice', null=True, blank=True)
    operational_status = models.CharField(
        'Operativni status', max_length=40, default='planirano', db_index=True
    )
    stipend = models.DecimalField(
        'Stipendij', max_digits=10, decimal_places=2, default=0
    )
    stipend_paid = models.BooleanField('Stipendij evidentiran', default=False)

    class Meta:
        verbose_name = 'Podaci o pogrebu'
        verbose_name_plural = 'Podaci o pogrebima'

    def __str__(self):
        recipient = self.event.participants.filter(
            role=EventParticipant.Role.RECIPIENT
        ).first()
        return recipient.historical_name if recipient else str(self.event)

    def clean(self):
        super().clean()
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.FUNERAL:
            raise ValidationError({'event': 'Podaci o pogrebu mogu pripadati samo pogrebu.'})


class AnointingDetails(models.Model):
    """Operational details for an anointing appointment, without financial data."""

    event = models.OneToOneField(
        SacramentalEvent, verbose_name='Pomazanje', on_delete=models.PROTECT,
        related_name='anointing_details',
    )
    scheduled_time = models.TimeField('Vrijeme', null=True, blank=True)
    address = models.CharField('Adresa / ustanova', max_length=240, blank=True)
    location = models.CharField('Detalj lokacije', max_length=240, blank=True)
    contact = models.CharField('Kontakt', max_length=240, blank=True)
    notes = models.TextField('Napomena', blank=True)
    operational_status = models.CharField(
        'Operativni status', max_length=40, default='planirano', db_index=True
    )
    completed = models.BooleanField('Obavljeno', default=False)

    class Meta:
        verbose_name = 'Podaci o pomazanju'
        verbose_name_plural = 'Podaci o pomazanjima'

    def __str__(self):
        recipient = self.event.participants.filter(
            role=EventParticipant.Role.RECIPIENT
        ).first()
        return recipient.historical_name if recipient else str(self.event)

    def clean(self):
        super().clean()
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.ANOINTING:
            raise ValidationError({'event': 'Podaci o pomazanju mogu pripadati samo pomazanju.'})


class FormationProgramYear(models.Model):
    """One parish preparation cycle for First Communion or Confirmation."""

    class ProgramType(models.TextChoices):
        FIRST_COMMUNION = 'first_communion', 'Prva pričest'
        CONFIRMATION = 'confirmation', 'Krizma'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_identifier = models.CharField(
        'Stabilni identifikator',
        max_length=160,
        default=uuid.uuid4,
        help_text='Identifikator koji koriste postojeći URL-ovi i korisničko sučelje.',
    )
    parish = models.ForeignKey(
        Parish, verbose_name='Župa', on_delete=models.PROTECT,
        related_name='formation_program_years',
    )
    program_type = models.CharField(
        'Vrsta priprave', max_length=24, choices=ProgramType.choices, db_index=True
    )
    year = models.PositiveSmallIntegerField('Godina')
    group_name = models.CharField('Naziv skupine', max_length=160, blank=True)
    ceremony_date = models.DateField('Datum slavlja', null=True, blank=True)
    celebrant_name = models.CharField('Slavitelj', max_length=200, blank=True)
    contribution_amount = models.DecimalField(
        'Zajednički prilog', max_digits=10, decimal_places=2, default=0
    )
    contribution_paid = models.BooleanField('Prilog evidentiran', default=False)
    contribution_paid_at = models.DateField(
        'Datum evidencije priloga', null=True, blank=True
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('program_type', '-year')
        constraints = (
            models.UniqueConstraint(
                fields=('parish', 'program_type', 'year'),
                name='unique_formation_program_year',
            ),
            models.UniqueConstraint(
                fields=('parish', 'program_type', 'public_identifier'),
                name='unique_formation_program_identifier',
            ),
        )
        verbose_name = 'Godina sakramentalne priprave'
        verbose_name_plural = 'Godine sakramentalne priprave'

    def __str__(self):
        return f'{self.get_program_type_display()} · {self.year}'


class FormationCandidate(models.Model):
    """Operational candidate record, separate from a confirmed sacramental fact."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_identifier = models.CharField('Stabilni identifikator', max_length=160)
    program_year = models.ForeignKey(
        FormationProgramYear, verbose_name='Godina priprave',
        on_delete=models.PROTECT, related_name='candidates',
    )
    person = models.ForeignKey(
        Person, verbose_name='Osoba', on_delete=models.PROTECT,
        null=True, blank=True, related_name='formation_candidates',
    )
    sacramental_event = models.OneToOneField(
        SacramentalEvent,
        verbose_name='Potvrđeni sakramentalni događaj',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='formation_candidate',
    )
    historical_name = models.CharField('Ime i prezime', max_length=220)
    given_names = models.CharField('Ime / imena', max_length=160, blank=True)
    surname = models.CharField('Prezime', max_length=160, blank=True)
    birth_date = models.DateField('Datum rođenja', null=True, blank=True)
    school_name = models.CharField('Škola', max_length=200, blank=True)
    school_class = models.CharField('Razred', max_length=40, blank=True)
    group_name = models.CharField('Skupina', max_length=80, blank=True)
    parents_name = models.CharField('Roditelji', max_length=300, blank=True)
    sponsor_name = models.CharField('Kum / kuma', max_length=220, blank=True)
    baptism_date = models.DateField('Datum krštenja', null=True, blank=True)
    operational_status = models.CharField('Status', max_length=40, default='upis')
    contribution_paid = models.BooleanField('Prilog evidentiran', default=False)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('historical_name',)
        constraints = (
            models.UniqueConstraint(
                fields=('program_year', 'public_identifier'),
                name='unique_candidate_in_program_year',
            ),
        )
        verbose_name = 'Kandidat sakramentalne priprave'
        verbose_name_plural = 'Kandidati sakramentalne priprave'

    def __str__(self):
        return self.historical_name


class RegisterTemplate(models.Model):
    """A governed template identity; field definitions live in versions."""

    class OwnerScope(models.TextChoices):
        SYSTEM = 'system', 'Sustav'
        CHURCH = 'church', 'Crkva sui iuris'
        JURISDICTION = 'jurisdiction', 'Crkvena jurisdikcija'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField('Stabilni kod', max_length=100, unique=True)
    event_type = models.CharField(
        'Vrsta sakramenta', max_length=24, choices=SacramentalEvent.EventType.choices
    )
    name = models.CharField('Naziv', max_length=220)
    owner_scope = models.CharField(
        'Vlasnik', max_length=16, choices=OwnerScope.choices, default=OwnerScope.SYSTEM
    )
    church_sui_iuris = models.ForeignKey(
        ChurchSuiIuris, verbose_name='Crkva sui iuris', on_delete=models.PROTECT,
        null=True, blank=True, related_name='register_templates',
    )
    ecclesiastical_jurisdiction = models.ForeignKey(
        EcclesiasticalJurisdiction, verbose_name='Crkvena jurisdikcija',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='register_templates',
    )
    is_official = models.BooleanField('Službeni obrazac', default=False)
    is_active = models.BooleanField('Aktivno', default=True, db_index=True)

    class Meta:
        ordering = ('event_type', 'name')
        verbose_name = 'Predložak matične knjige'
        verbose_name_plural = 'Predlošci matičnih knjiga'

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        validation_errors = {}
        if self.owner_scope == self.OwnerScope.CHURCH and not self.church_sui_iuris_id:
            validation_errors['church_sui_iuris'] = 'Odaberite Crkvu sui iuris.'
        if self.owner_scope == self.OwnerScope.JURISDICTION and not self.ecclesiastical_jurisdiction_id:
            validation_errors['ecclesiastical_jurisdiction'] = 'Odaberite crkvenu jurisdikciju.'
        if validation_errors:
            raise ValidationError(validation_errors)


class RegisterTemplateVersion(models.Model):
    """Immutable-in-practice schema and print configuration for a template."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nacrt'
        PUBLISHED = 'published', 'Objavljeno'
        RETIRED = 'retired', 'Povučeno'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        RegisterTemplate, verbose_name='Predložak', on_delete=models.PROTECT,
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
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
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

    def save(self, *args, **kwargs):
        self._validate_published_version_is_unchanged()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED:
            raise ValidationError(
                'Objavljena verzija predloška ne može se brisati.'
            )
        return super().delete(*args, **kwargs)


class RegisterBook(models.Model):
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_identifier = models.CharField(
        'Stabilni identifikator', max_length=160, blank=True
    )
    parish = models.ForeignKey(
        Parish, verbose_name='Župa', on_delete=models.PROTECT, related_name='register_books'
    )
    template_version = models.ForeignKey(
        RegisterTemplateVersion, verbose_name='Verzija predloška',
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
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
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


class RegisterBookYear(models.Model):
    """An explicitly opened year, including empty retroactive years."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Otvorena'
        LOCKED = 'locked', 'Zaključana'
        ARCHIVED = 'archived', 'Arhivirana'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register_book = models.ForeignKey(
        RegisterBook, verbose_name='Matična knjiga', on_delete=models.PROTECT,
        related_name='years',
    )
    year = models.PositiveSmallIntegerField('Godina')
    status = models.CharField(
        'Status', max_length=12, choices=Status.choices, default=Status.OPEN
    )
    next_entry_number = models.PositiveIntegerField('Sljedeći redni broj', default=1)

    class Meta:
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


class GeneralRegisterEntry(models.Model):
    """A non-sacramental entry in a parish register book."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_identifier = models.CharField('Stabilni identifikator', max_length=160)
    register_book_year = models.ForeignKey(
        RegisterBookYear,
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
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
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

class RegisterEntry(models.Model):
    """A register-book entry linked to the underlying sacramental event."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nacrt'
        CONFIRMED = 'confirmed', 'Potvrđeno'
        LOCKED = 'locked', 'Zaključano'
        CORRECTED = 'corrected', 'Ispravljeno'
        CANCELLED = 'cancelled', 'Poništeno'
        LEGACY_IMPORTED = 'legacy_imported', 'Uvezeno iz postojećeg sustava'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish = models.ForeignKey(
        Parish, verbose_name='Župa', on_delete=models.PROTECT,
        related_name='register_entries',
    )
    register_book_year = models.ForeignKey(
        RegisterBookYear, verbose_name='Godina knjige', on_delete=models.PROTECT,
        related_name='entries',
    )
    event = models.OneToOneField(
        SacramentalEvent, verbose_name='Događaj', on_delete=models.PROTECT,
        related_name='register_entry',
    )
    template_version = models.ForeignKey(
        RegisterTemplateVersion, verbose_name='Verzija predloška',
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
        null=True, blank=True, related_name='updated_register_entries',
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
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

    def _validate_locked_entry_is_unchanged(self):
        if self.pk:
            previous_status = type(self).objects.filter(pk=self.pk).values_list(
                'status', flat=True
            ).first()
            if previous_status == self.Status.LOCKED:
                raise ValidationError(
                    'Zaključani matični upis ne može se izravno mijenjati.'
                )

    def save(self, *args, **kwargs):
        self._validate_locked_entry_is_unchanged()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == self.Status.LOCKED:
            raise ValidationError('Zaključani matični upis ne može se brisati.')
        return super().delete(*args, **kwargs)
