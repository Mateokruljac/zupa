"""ORM modeli sakramenata i sakramentalne priprave."""
import uuid

from core.models import FCTA, FCTB, SCD1
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django_multitenant.schema import with_tenant_schema


class SacramentalEvent(FCTA):
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

    public_identifier = models.CharField(
        'Stabilni identifikator',
        max_length=160,
        blank=True,
        help_text='Stabilni identifikator koji koriste URL-ovi i korisničko sučelje.',
    )
    parish = models.ForeignKey('pastoral.Parish', verbose_name='Župa', on_delete=models.PROTECT,
        related_name='sacramental_events',
    )
    event_type = models.CharField(
        'Vrsta sakramenta', max_length=24, choices=EventType.choices, db_index=True
    )
    event_date = models.DateField('Datum', null=True, blank=True, db_index=True)
    place_name = models.CharField('Mjesto', max_length=200, blank=True)
    celebrating_parish = models.ForeignKey('pastoral.Parish', verbose_name='Župa slavlja', on_delete=models.PROTECT,
        null=True, blank=True, related_name='celebrated_sacramental_events',
    )
    minister = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Služitelj', on_delete=models.PROTECT,
        null=True, blank=True, related_name='ministered_sacramental_events',
    )
    minister_name = models.CharField('Povijesni naziv služitelja', max_length=200, blank=True)
    liturgical_tradition = models.ForeignKey('liturgija.LiturgicalTradition', verbose_name='Liturgijska tradicija',
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
        null=True, blank=True,         related_name='updated_sacramental_events',
    )

    class Meta:
        db_table = 'pastoral_sacramentalevent'
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

    @with_tenant_schema
    def _validate_locked_event_is_unchanged(self):
        if self.pk:
            previous_status = type(self).objects.filter(pk=self.pk).values_list(
                'status', flat=True
            ).first()
            if previous_status == self.Status.LOCKED:
                raise ValidationError(
                    'Zaključani sakramentalni događaj ne može se izravno mijenjati.'
                )

    @with_tenant_schema
    def save(self, *args, **kwargs):
        self._validate_locked_event_is_unchanged()
        return super().save(*args, **kwargs)

    @with_tenant_schema
    def delete(self, *args, **kwargs):
        if self.status == self.Status.LOCKED:
            raise ValidationError('Zaključani sakramentalni događaj ne može se brisati.')
        return super().delete(*args, **kwargs)


class EventParticipant(FCTA):
    """A person or an unparsed historical name participating in an event."""

    class Role(models.TextChoices):
        RECIPIENT = 'recipient', 'Primatelj'
        PARENT = 'parent', 'Roditelj'
        GODPARENT = 'godparent', 'Kum / kuma'
        SPONSOR = 'sponsor', 'Kum / kuma (krizma)'
        SPOUSE = 'spouse', 'Zaručnik / zaručnica'
        WITNESS = 'witness', 'Svjedok'

    parish = models.ForeignKey('pastoral.Parish', verbose_name='Župa', on_delete=models.PROTECT,
        related_name='sacramental_event_participants',
    )
    event = models.ForeignKey('sakramenti.SacramentalEvent', verbose_name='Događaj', on_delete=models.PROTECT,
        related_name='participants',
    )
    person = models.ForeignKey('zupa_vjernici.Person', verbose_name='Osoba', on_delete=models.PROTECT,
        null=True, blank=True, related_name='sacramental_participations',
    )
    role = models.CharField('Uloga', max_length=20, choices=Role.choices, db_index=True)
    historical_name = models.CharField(
        'Povijesni zapis imena', max_length=300, blank=True,
        help_text='Čuva izvorni tekst kada osobe nije sigurno automatski razdvojiti.',
    )
    snapshot_given_names = models.CharField('Ime u trenutku sakramenta', max_length=160, blank=True)
    snapshot_surname = models.CharField('Prezime u trenutku sakramenta', max_length=160, blank=True)
    snapshot_sex = models.CharField('Spol u trenutku sakramenta', max_length=12, blank=True)
    snapshot_date_of_birth = models.DateField('Datum rođenja u trenutku sakramenta', null=True, blank=True)
    snapshot_place_of_birth = models.CharField('Mjesto rođenja u trenutku sakramenta', max_length=180, blank=True)
    parent_side = models.CharField('Strana roditelja', max_length=12, blank=True)
    display_order = models.PositiveSmallIntegerField('Redoslijed prikaza', default=0)

    class Meta:
        db_table = 'pastoral_eventparticipant'
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

    @with_tenant_schema
    def save(self, *args, **kwargs):
        linked_person = self.person if self.person_id else None
        if linked_person and not self.snapshot_given_names and not self.snapshot_surname:
            self.snapshot_given_names = linked_person.given_names
            self.snapshot_surname = linked_person.surname
            self.snapshot_sex = linked_person.sex
            self.snapshot_date_of_birth = linked_person.date_of_birth
            self.snapshot_place_of_birth = linked_person.place_of_birth
            if not self.historical_name:
                self.historical_name = str(linked_person)
        return super().save(*args, **kwargs)


class BaptismDetails(FCTB):
    """Data used only by baptism events."""

    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Krštenje', on_delete=models.PROTECT,
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
        db_table = 'pastoral_baptismdetails'
        verbose_name = 'Podaci o krštenju'
        verbose_name_plural = 'Podaci o krštenjima'

    def __str__(self):
        return str(self.event)

    def clean(self):
        super().clean()
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.BAPTISM:
            raise ValidationError({'event': 'Podaci o krštenju mogu pripadati samo krštenju.'})


class MarriageDetails(FCTB):
    """Operational details specific to a marriage preparation and celebration."""

    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Vjenčanje', on_delete=models.PROTECT,
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
        db_table = 'pastoral_marriagedetails'
        verbose_name = 'Podaci o vjenčanju'
        verbose_name_plural = 'Podaci o vjenčanjima'

    def __str__(self):
        return self.couple_display_name

    def clean(self):
        super().clean()
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.MARRIAGE:
            raise ValidationError({'event': 'Podaci o vjenčanju mogu pripadati samo vjenčanju.'})


class FuneralDetails(FCTB):
    """Operational and pastoral details specific to a funeral."""

    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Pogreb', on_delete=models.PROTECT,
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
        db_table = 'pastoral_funeraldetails'
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


class AnointingDetails(FCTB):
    """Operational details for an anointing appointment, without financial data."""

    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Pomazanje', on_delete=models.PROTECT,
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
        db_table = 'pastoral_anointingdetails'
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


class FormationProgramYear(SCD1):
    """One parish preparation cycle for First Communion or Confirmation."""

    class ProgramType(models.TextChoices):
        FIRST_COMMUNION = 'first_communion', 'Prva pričest'
        CONFIRMATION = 'confirmation', 'Krizma'

    unified_key_origin_fields = ('parish_id', 'program_type', 'year')

    public_identifier = models.CharField(
        'Stabilni identifikator',
        max_length=160,
        default=uuid.uuid4,
        help_text='Identifikator koji koriste postojeći URL-ovi i korisničko sučelje.',
    )
    parish = models.ForeignKey('pastoral.Parish', verbose_name='Župa', on_delete=models.PROTECT,
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

    class Meta:
        db_table = 'pastoral_formationprogramyear'
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


class FormationCandidate(FCTA):
    """Operational candidate record, separate from a confirmed sacramental fact."""

    public_identifier = models.CharField('Stabilni identifikator', max_length=160)
    program_year = models.ForeignKey('sakramenti.FormationProgramYear', verbose_name='Godina priprave',
        on_delete=models.PROTECT, related_name='candidates',
    )
    person = models.ForeignKey('zupa_vjernici.Person', verbose_name='Osoba', on_delete=models.PROTECT,
        null=True, blank=True, related_name='formation_candidates',
    )
    sacramental_event = models.OneToOneField('sakramenti.SacramentalEvent',
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

    class Meta:
        db_table = 'pastoral_formationcandidate'
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
