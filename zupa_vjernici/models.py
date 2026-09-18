"""ORM modeli župe i vjernika (osobe, crkvena pripadnost)."""
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from core.models import FCTA, SCD1, SCD2, SCD2A


def normalize_person_search_text(value: str) -> str:
    """Return a predictable accent-insensitive value used only for searching."""
    decomposed_value = unicodedata.normalize('NFKD', value or '')
    characters_without_accents = (
        character
        for character in decomposed_value
        if not unicodedata.combining(character)
    )
    return ' '.join(''.join(characters_without_accents).casefold().split())


class ChurchSuiIuris(SCD1):
    """Katolička Crkva sui iuris kojoj osoba ili župa pripada."""

    unified_key_origin_fields = ('code',)

    class CanonicalTradition(models.TextChoices):
        LATIN = 'latin', 'Latinska'
        EASTERN = 'eastern', 'Istočna'

    code = models.SlugField('Stabilni kod', max_length=60, unique=True)
    official_name = models.CharField('Službeni naziv', max_length=200)
    short_name = models.CharField('Kratki naziv', max_length=120, blank=True)
    canonical_tradition = models.CharField(
        'Kanonska tradicija',
        max_length=16,
        choices=CanonicalTradition.choices,
        db_index=True,
    )
    default_liturgical_tradition = models.ForeignKey('liturgija.LiturgicalTradition',
        verbose_name='Zadana liturgijska tradicija',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='churches_sui_iuris',
    )

    class Meta:
        db_table = 'pastoral_churchsuiiuris'
        ordering = ('official_name',)
        verbose_name = 'Crkva sui iuris'
        verbose_name_plural = 'Crkve sui iuris'

    def __str__(self):
        return self.official_name


class EcclesiasticalJurisdiction(SCD1):
    """Biskupija, eparhija ili druga kontrolirana crkvena jurisdikcija."""

    unified_key_origin_fields = ('code',)

    class JurisdictionType(models.TextChoices):
        DIOCESE = 'diocese', 'Biskupija'
        ARCHDIOCESE = 'archdiocese', 'Nadbiskupija'
        EPARCHY = 'eparchy', 'Eparhija'
        ARCHEPARCHY = 'archeparchy', 'Arhieparhija'
        OTHER = 'other', 'Drugo'

    code = models.SlugField('Stabilni kod', max_length=80, unique=True)
    official_name = models.CharField('Službeni naziv', max_length=220)
    jurisdiction_type = models.CharField(
        'Vrsta jurisdikcije',
        max_length=20,
        choices=JurisdictionType.choices,
        db_index=True,
    )
    church_sui_iuris = models.ForeignKey('zupa_vjernici.ChurchSuiIuris',
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

    class Meta:
        db_table = 'pastoral_ecclesiasticaljurisdiction'
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


class Person(SCD1):
    """Jedinstvena osoba unutar provjerenog tenant opsega jedne župe."""

    unified_key_origin_fields = ('parish_id', 'normalized_surname', 'normalized_given_names')

    class Sex(models.TextChoices):
        FEMALE = 'female', 'Ženski'
        MALE = 'male', 'Muški'
        UNKNOWN = 'unknown', 'Nepoznato / nepotvrđeno'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Aktivna'
        MERGED = 'merged', 'Spojena'
        ARCHIVED = 'archived', 'Arhivirana'

    parish = models.ForeignKey('pastoral.Parish',
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

    class Meta:
        db_table = 'pastoral_person'
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


class ChurchEnrollment(SCD2):
    """Verzionirana i dokaziva pripadnost osobe Crkvi sui iuris."""

    unified_key_origin_fields = ('person_id', 'church_sui_iuris_id', 'valid_from')

    class Status(models.TextChoices):
        UNCONFIRMED = 'unconfirmed', 'Nepotvrđeno'
        CONFIRMED = 'confirmed', 'Potvrđeno'

    parish = models.ForeignKey('pastoral.Parish',
        verbose_name='Župa',
        on_delete=models.PROTECT,
        related_name='church_enrollments',
    )
    person = models.ForeignKey('zupa_vjernici.Person',
        verbose_name='Osoba',
        on_delete=models.PROTECT,
        related_name='church_enrollments',
    )
    church_sui_iuris = models.ForeignKey('zupa_vjernici.ChurchSuiIuris',
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

    class Meta:
        db_table = 'pastoral_churchenrollment'
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

# --- Operativni parish zapisi (bivši Parish.data) ---


class Street(SCD2A):
    """Ulica u teritoriju župe."""

    unified_key_origin_fields = ('parish_id', 'public_identifier')
    scd2_save_exclude_fields = ('notes', 'sort_order', 'payload')

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='streets',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=200)
    zone = models.CharField(max_length=120, blank=True)
    sort_order = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Household(SCD2A):
    """Kućanstvo / obitelj (legacy families)."""

    unified_key_origin_fields = ('parish_id', 'public_identifier')
    scd2_save_exclude_fields = (
        'phone',
        'email',
        'pastoral_notes',
        'last_visit_on',
        'tags',
        'payload',
        'preferred_mass',
    )

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='households',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    surname = models.CharField(max_length=160, blank=True)
    street = models.ForeignKey(
        Street,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='households',
    )
    street_public_identifier = models.CharField(max_length=64, blank=True)
    house_number = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=40, blank=True, default='aktivna')
    preferred_mass = models.CharField(max_length=40, blank=True)
    pastoral_notes = models.TextField(blank=True)
    origin_place = models.CharField(max_length=160, blank=True)
    last_visit_on = models.DateField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]
        ordering = ['surname', 'public_identifier']

    def __str__(self):
        return self.surname or self.public_identifier


class HouseholdMembership(SCD2):
    """Razdoblje pripadnosti osobe kućanstvu — nije identitet osobe."""

    unified_key_origin_fields = ('household_id', 'public_identifier')

    class SpouseSide(models.TextChoices):
        NONE = '', 'Nije bračni karton'
        HUSBAND = 'husband', 'Muž'
        WIFE = 'wife', 'Žena'

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    person = models.ForeignKey(
        'zupa_vjernici.Person',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='household_memberships',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    historical_name = models.CharField(max_length=160, blank=True)
    role = models.CharField(
        'Odnos u obitelji',
        max_length=80,
        blank=True,
        help_text='Slobodni tekst iz kartona (majka, sin, rođak…).',
    )
    spouse_side = models.CharField(
        max_length=12,
        choices=SpouseSide.choices,
        blank=True,
        default=SpouseSide.NONE,
    )
    lives_in_household = models.BooleanField(default=True)
    is_head = models.BooleanField(default=False)
    recorded_birth_year = models.CharField(max_length=20, blank=True)
    pastoral_roles = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('household', 'public_identifier')]
        ordering = ['sort_order', 'historical_name']
        verbose_name = 'Članstvo u kućanstvu'
        verbose_name_plural = 'Članstva u kućanstvu'

    def __str__(self):
        return self.historical_name or str(self.person_id or self.public_identifier)


class HouseholdContribution(FCTA):
    """Yearly lukno / gift status for one household (HouseholdContributionYear)."""

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name='contributions',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    year = models.PositiveIntegerField(default=0, db_index=True)
    lukno_paid = models.BooleanField(default=False)
    lukno_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lukno_paid_at = models.DateField(null=True, blank=True)
    church_donation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    donation_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [('household', 'public_identifier')]
        ordering = ['-year']


class PastoralVisit(FCTA):
    """Pastoralna posjeta."""

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='pastoral_visits',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    household = models.ForeignKey(
        Household,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visits',
    )
    family_public_identifier = models.CharField(max_length=64, blank=True)
    scheduled_on = models.DateField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    visit_type = models.CharField(max_length=80, blank=True)
    person_name = models.CharField(max_length=160, blank=True)
    address = models.CharField(max_length=255, blank=True)
    priest = models.CharField(max_length=160, blank=True)
    purpose = models.CharField(max_length=255, blank=True)
    report = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


HouseholdContributionYear = HouseholdContribution
