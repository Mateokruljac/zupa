import uuid
import unicodedata
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


def otp_challenge_expiry():
    return timezone.now() + timedelta(
        minutes=getattr(settings, 'OTP_TTL_MINUTES', 10),
    )


def normalize_person_search_text(value: str) -> str:
    """Return a predictable accent-insensitive value used only for searching."""
    decomposed_value = unicodedata.normalize('NFKD', value or '')
    characters_without_accents = (
        character
        for character in decomposed_value
        if not unicodedata.combining(character)
    )
    return ' '.join(''.join(characters_without_accents).casefold().split())


class LiturgicalTradition(models.Model):
    """Kontrolirani globalni popis liturgijskih tradicija."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField('Stabilni kod', max_length=50, unique=True)
    name = models.CharField('Naziv', max_length=160)
    is_active = models.BooleanField('Aktivno', default=True, db_index=True)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Liturgijska tradicija'
        verbose_name_plural = 'Liturgijske tradicije'

    def __str__(self):
        return self.name


class ChurchSuiIuris(models.Model):
    """Katolička Crkva sui iuris kojoj osoba ili župa pripada."""

    class CanonicalTradition(models.TextChoices):
        LATIN = 'latin', 'Latinska'
        EASTERN = 'eastern', 'Istočna'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField('Stabilni kod', max_length=60, unique=True)
    official_name = models.CharField('Službeni naziv', max_length=200)
    short_name = models.CharField('Kratki naziv', max_length=120, blank=True)
    canonical_tradition = models.CharField(
        'Kanonska tradicija',
        max_length=16,
        choices=CanonicalTradition.choices,
        db_index=True,
    )
    default_liturgical_tradition = models.ForeignKey(
        LiturgicalTradition,
        verbose_name='Zadana liturgijska tradicija',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='churches_sui_iuris',
    )
    is_active = models.BooleanField('Aktivno', default=True, db_index=True)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('official_name',)
        verbose_name = 'Crkva sui iuris'
        verbose_name_plural = 'Crkve sui iuris'

    def __str__(self):
        return self.official_name


class EcclesiasticalJurisdiction(models.Model):
    """Biskupija, eparhija ili druga kontrolirana crkvena jurisdikcija."""

    class JurisdictionType(models.TextChoices):
        DIOCESE = 'diocese', 'Biskupija'
        ARCHDIOCESE = 'archdiocese', 'Nadbiskupija'
        EPARCHY = 'eparchy', 'Eparhija'
        ARCHEPARCHY = 'archeparchy', 'Arhieparhija'
        OTHER = 'other', 'Drugo'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField('Stabilni kod', max_length=80, unique=True)
    official_name = models.CharField('Službeni naziv', max_length=220)
    jurisdiction_type = models.CharField(
        'Vrsta jurisdikcije',
        max_length=20,
        choices=JurisdictionType.choices,
        db_index=True,
    )
    church_sui_iuris = models.ForeignKey(
        ChurchSuiIuris,
        verbose_name='Crkva sui iuris',
        on_delete=models.PROTECT,
        related_name='jurisdictions',
    )
    parent_jurisdiction = models.ForeignKey(
        'self',
        verbose_name='Nadređena jurisdikcija',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='child_jurisdictions',
    )
    is_active = models.BooleanField('Aktivno', default=True, db_index=True)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('official_name',)
        verbose_name = 'Crkvena jurisdikcija'
        verbose_name_plural = 'Crkvene jurisdikcije'

    def __str__(self):
        return self.official_name

    def clean(self):
        super().clean()
        validation_errors = {}
        if self.parent_jurisdiction_id == self.id:
            validation_errors['parent_jurisdiction'] = (
                'Jurisdikcija ne može biti nadređena sama sebi.'
            )
        elif (
            self.parent_jurisdiction_id
            and self.parent_jurisdiction.church_sui_iuris_id
            != self.church_sui_iuris_id
        ):
            validation_errors['parent_jurisdiction'] = (
                'Nadređena jurisdikcija mora pripadati istoj Crkvi sui iuris.'
            )
        if validation_errors:
            raise ValidationError(validation_errors)


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
    church_sui_iuris = models.ForeignKey(
        ChurchSuiIuris,
        verbose_name='Crkva sui iuris',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='parishes',
    )
    ecclesiastical_jurisdiction = models.ForeignKey(
        EcclesiasticalJurisdiction,
        verbose_name='Crkvena jurisdikcija',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='parishes',
    )
    default_liturgical_tradition = models.ForeignKey(
        LiturgicalTradition,
        verbose_name='Zadana liturgijska tradicija',
        on_delete=models.PROTECT,
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

    def clean(self):
        super().clean()
        if (
            self.ecclesiastical_jurisdiction_id
            and self.church_sui_iuris_id
            and self.ecclesiastical_jurisdiction.church_sui_iuris_id
            != self.church_sui_iuris_id
        ):
            raise ValidationError({
                'ecclesiastical_jurisdiction': (
                    'Jurisdikcija mora pripadati odabranoj Crkvi sui iuris.'
                ),
            })


class Person(models.Model):
    """Jedinstvena osoba unutar provjerenog tenant opsega jedne župe."""

    class Sex(models.TextChoices):
        FEMALE = 'female', 'Ženski'
        MALE = 'male', 'Muški'
        UNKNOWN = 'unknown', 'Nepoznato / nepotvrđeno'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Aktivna'
        MERGED = 'merged', 'Spojena'
        ARCHIVED = 'archived', 'Arhivirana'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish = models.ForeignKey(
        Parish,
        verbose_name='Župa',
        on_delete=models.PROTECT,
        related_name='persons',
    )
    given_names = models.CharField('Ime / imena', max_length=160)
    surname = models.CharField('Prezime', max_length=160)
    birth_surname = models.CharField('Rođeno prezime', max_length=160, blank=True)
    sex = models.CharField(
        'Spol',
        max_length=12,
        choices=Sex.choices,
        default=Sex.UNKNOWN,
    )
    date_of_birth = models.DateField('Datum rođenja', null=True, blank=True)
    place_of_birth = models.CharField('Mjesto rođenja', max_length=180, blank=True)
    father = models.ForeignKey(
        'self',
        verbose_name='Otac',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children_as_father',
    )
    mother = models.ForeignKey(
        'self',
        verbose_name='Majka',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children_as_mother',
    )
    normalized_given_names = models.CharField(
        max_length=160,
        editable=False,
        db_index=True,
    )
    normalized_surname = models.CharField(
        max_length=160,
        editable=False,
        db_index=True,
    )
    status = models.CharField(
        'Status',
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('surname', 'given_names', 'date_of_birth')
        indexes = (
            models.Index(
                fields=('parish', 'normalized_surname', 'normalized_given_names'),
                name='person_parish_name_lookup',
            ),
            models.Index(
                fields=('parish', 'date_of_birth'),
                name='person_parish_birth_lookup',
            ),
        )
        verbose_name = 'Osoba'
        verbose_name_plural = 'Osobe'

    def __str__(self):
        return f'{self.given_names} {self.surname}'.strip()

    def clean(self):
        super().clean()
        relationship_errors = {}
        for field_name in ('father', 'mother'):
            related_person = getattr(self, field_name, None)
            if related_person and related_person.parish_id != self.parish_id:
                relationship_errors[field_name] = (
                    'Roditelj mora pripadati istoj župi kao osoba.'
                )
            if related_person and related_person.pk == self.pk:
                relationship_errors[field_name] = 'Osoba ne može biti vlastiti roditelj.'
        if relationship_errors:
            raise ValidationError(relationship_errors)

    def save(self, *args, **kwargs):
        self.normalized_given_names = normalize_person_search_text(self.given_names)
        self.normalized_surname = normalize_person_search_text(self.surname)
        selected_update_fields = kwargs.get('update_fields')
        if selected_update_fields is not None:
            kwargs['update_fields'] = set(selected_update_fields) | {
                'normalized_given_names',
                'normalized_surname',
            }
        return super().save(*args, **kwargs)


class ChurchEnrollment(models.Model):
    """Verzionirana i dokaziva pripadnost osobe Crkvi sui iuris."""

    class Status(models.TextChoices):
        UNCONFIRMED = 'unconfirmed', 'Nepotvrđeno'
        CONFIRMED = 'confirmed', 'Potvrđeno'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish = models.ForeignKey(
        Parish,
        verbose_name='Župa',
        on_delete=models.PROTECT,
        related_name='church_enrollments',
    )
    person = models.ForeignKey(
        Person,
        verbose_name='Osoba',
        on_delete=models.PROTECT,
        related_name='church_enrollments',
    )
    church_sui_iuris = models.ForeignKey(
        ChurchSuiIuris,
        verbose_name='Crkva sui iuris',
        on_delete=models.PROTECT,
        related_name='person_enrollments',
    )
    valid_from = models.DateField('Vrijedi od', null=True, blank=True)
    valid_until = models.DateField('Vrijedi do', null=True, blank=True)
    enrollment_basis = models.CharField('Temelj pripadnosti', max_length=200, blank=True)
    decree_reference = models.CharField('Referenca dekreta', max_length=200, blank=True)
    previous_enrollment = models.ForeignKey(
        'self',
        verbose_name='Prethodna pripadnost',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='following_enrollments',
    )
    status = models.CharField(
        'Status',
        max_length=12,
        choices=Status.choices,
        default=Status.UNCONFIRMED,
        db_index=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Evidentirao',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='recorded_church_enrollments',
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        ordering = ('person', '-valid_from', '-created_at')
        constraints = (
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_from__isnull=True)
                | Q(valid_until__gte=F('valid_from')),
                name='enrollment_valid_period',
            ),
            models.UniqueConstraint(
                fields=('person',),
                condition=Q(valid_until__isnull=True, status='confirmed'),
                name='one_current_confirmed_enrollment',
            ),
        )
        indexes = (
            models.Index(
                fields=('parish', 'status'),
                name='enrollment_parish_status',
            ),
        )
        verbose_name = 'Pripadnost Crkvi sui iuris'
        verbose_name_plural = 'Pripadnosti Crkvi sui iuris'

    def __str__(self):
        return f'{self.person} · {self.church_sui_iuris}'

    def clean(self):
        super().clean()
        validation_errors = {}
        if self.person_id and self.person.parish_id != self.parish_id:
            validation_errors['person'] = 'Osoba mora pripadati odabranoj župi.'
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            validation_errors['valid_until'] = 'Završni datum ne smije biti prije početnog.'
        if self.previous_enrollment_id:
            if self.previous_enrollment_id == self.id:
                validation_errors['previous_enrollment'] = (
                    'Zapis ne može kao prethodnika navesti sam sebe.'
                )
            elif self.previous_enrollment.person_id != self.person_id:
                validation_errors['previous_enrollment'] = (
                    'Prethodna pripadnost mora pripadati istoj osobi.'
                )
        if validation_errors:
            raise ValidationError(validation_errors)


class RegistryAuditEvent(models.Model):
    """Nepromenjivi tenant-svjestan trag osjetljivih matičnih radnji."""

    class Outcome(models.TextChoices):
        SUCCESS = 'success', 'Uspjeh'
        DENIED = 'denied', 'Odbijeno'
        FAILURE = 'failure', 'Greška'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish = models.ForeignKey(
        Parish,
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

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError('Audit događaj je nepromjenjiv.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Audit događaj se ne smije brisati.')


class OtpChallenge(models.Model):
    """Jednokratni, vremenski ograničen izazov za prijavu."""

    email = models.EmailField(db_index=True)
    # Polje zadržava postojeći naziv zbog kompatibilnosti, ali od migracije
    # 0028 sadrži isključivo salted hash, nikada čitljiv OTP kod.
    code = models.CharField(max_length=128)
    role = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=otp_challenge_expiry, db_index=True)
    used = models.BooleanField(default=False)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)

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


# Registry models live in a separate module so this file remains readable. Importing
# them here keeps Django's conventional ``pastoral.models`` discovery intact.
from .registry_models import (  # noqa: E402, F401
    AnointingDetails,
    BaptismDetails,
    EventParticipant,
    FormationCandidate,
    FormationProgramYear,
    FuneralDetails,
    GeneralRegisterEntry,
    MarriageDetails,
    RegisterBook,
    RegisterBookYear,
    RegisterEntry,
    RegisterTemplate,
    RegisterTemplateVersion,
    SacramentalEvent,
)
