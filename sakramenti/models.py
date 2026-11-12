"""ORM modeli sakramenata i sakramentalne priprave."""
import hashlib
import json
import uuid
from datetime import date
from decimal import Decimal

from core.models import FCTA, FCTB, SCD1
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.db.models.functions import ExtractYear
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
    """Službeni sadržaj jednog upisa u maticu krštenih."""

    class ChildSex(models.TextChoices):
        SON = 'son', 'Sin'
        DAUGHTER = 'daughter', 'Kći'

    class IdentifierType(models.TextChoices):
        OIB = 'oib', 'OIB'
        JMBG = 'jmbg', 'JMBG'

    HASHED_FIELD_NAMES = (
        'entry_number', 'birth_date', 'baptism_date', 'child_first_name',
        'child_last_name', 'child_sex', 'baptism_place', 'identifier_type',
        'identifier_value', 'father_first_name', 'father_last_name',
        'father_religion', 'mother_first_name', 'mother_last_name',
        'mother_religion', 'parents_canonically_married',
        'residence_address', 'godparent_first_name', 'godparent_last_name',
        'minister_first_name', 'minister_last_name', 'minister_role',
        'confirmation_date', 'confirmation_place', 'confirmation_parish',
        'marriage_date', 'marriage_parish', 'spouse_first_name',
        'spouse_last_name', 'notes', 'physical_page',
    )

    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Krštenje', on_delete=models.PROTECT,
        related_name='baptism_details',
    )
    entry_number = models.PositiveIntegerField('Redni broj', null=True, blank=True)
    birth_date = models.DateField('Datum rođenja', null=True, blank=True)
    baptism_date = models.DateField('Datum krštenja', null=True, blank=True, db_index=True)
    baptism_year = models.GeneratedField(
        verbose_name='Godina krštenja',
        expression=ExtractYear('baptism_date'),
        output_field=models.PositiveSmallIntegerField(null=True),
        db_persist=True,
        db_index=True,
        editable=False,
    )
    child_first_name = models.CharField('Ime djeteta', max_length=160, default='')
    child_last_name = models.CharField('Prezime djeteta', max_length=160, default='')
    child_sex = models.CharField(
        'Sin ili kći', max_length=12, choices=ChildSex.choices, default=ChildSex.SON
    )
    baptism_place = models.CharField('Mjesto krštenja', max_length=200, default='')
    identifier_type = models.CharField(
        'Vrsta identifikatora', max_length=4, choices=IdentifierType.choices,
        null=True, blank=True,
    )
    identifier_value = models.CharField(
        'JMBG / OIB', max_length=13, null=True, blank=True, db_index=True
    )
    father_first_name = models.CharField('Ime oca', max_length=160, default='')
    father_last_name = models.CharField('Prezime oca', max_length=160, default='')
    father_religion = models.CharField('Vjera oca', max_length=120, default='')
    mother_first_name = models.CharField('Ime majke', max_length=160, default='')
    mother_last_name = models.CharField('Djevojačko prezime majke', max_length=160, default='')
    mother_religion = models.CharField('Vjera majke', max_length=120, default='')
    parents_canonically_married = models.BooleanField(
        'Roditelji kanonski vjenčani', default=True
    )
    residence_address = models.CharField('Adresa prebivališta', max_length=255, default='')
    godparent_first_name = models.CharField('Ime kuma / kume', max_length=160, default='')
    godparent_last_name = models.CharField('Prezime kuma / kume', max_length=160, default='')
    minister_first_name = models.CharField('Ime krstitelja', max_length=160, default='')
    minister_last_name = models.CharField('Prezime krstitelja', max_length=160, default='')
    minister_role = models.CharField('Služba krstitelja', max_length=120, default='')
    confirmation_date = models.DateField('Datum potvrde', null=True, blank=True)
    confirmation_place = models.CharField(
        'Mjesto potvrde', max_length=200, null=True, blank=True
    )
    confirmation_parish = models.CharField(
        'Župa potvrde', max_length=200, null=True, blank=True
    )
    marriage_date = models.DateField('Datum ženidbe', null=True, blank=True)
    marriage_parish = models.CharField(
        'Župa ženidbe', max_length=200, null=True, blank=True
    )
    spouse_first_name = models.CharField(
        'Ime supružnika', max_length=160, null=True, blank=True
    )
    spouse_last_name = models.CharField(
        'Prezime supružnika', max_length=160, null=True, blank=True
    )
    notes = models.TextField('Naknadni upisi i bilješke', null=True, blank=True)
    physical_page = models.CharField(
        'Stranica u fizičkoj matici', max_length=40, null=True, blank=True
    )
    content_hash = models.CharField(
        'Hash sadržaja', max_length=64, editable=False, db_index=True, default=''
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
        indexes = (
            models.Index(
                fields=('child_last_name', 'child_first_name'),
                name='baptism_child_name',
            ),
        )
        constraints = (
            models.CheckConstraint(
                condition=Q(birth_date__isnull=True) | Q(baptism_date__isnull=True)
                | Q(birth_date__lte=models.F('baptism_date')),
                name='baptism_birth_not_after_baptism',
            ),
            models.CheckConstraint(
                condition=(
                    Q(identifier_type__isnull=True, identifier_value__isnull=True)
                    | Q(identifier_type__isnull=False, identifier_value__isnull=False)
                ),
                name='baptism_identifier_pair',
            ),
        )
        verbose_name = 'Podaci o krštenju'
        verbose_name_plural = 'Podaci o krštenjima'

    def __str__(self):
        return str(self.event)

    def clean(self):
        super().clean()
        errors = {}
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.BAPTISM:
            errors['event'] = 'Podaci o krštenju mogu pripadati samo krštenju.'
        if self.birth_date and self.baptism_date and self.birth_date > self.baptism_date:
            errors['baptism_date'] = 'Datum krštenja ne može biti prije datuma rođenja.'
        identifier = (self.identifier_value or '').strip()
        if bool(self.identifier_type) != bool(identifier):
            errors['identifier_value'] = 'Vrsta i vrijednost identifikatora unose se zajedno.'
        elif self.identifier_type == self.IdentifierType.OIB and (
            len(identifier) != 11 or not identifier.isdigit()
        ):
            errors['identifier_value'] = 'OIB mora sadržavati 11 znamenki.'
        elif self.identifier_type == self.IdentifierType.JMBG and (
            len(identifier) != 13 or not identifier.isdigit()
        ):
            errors['identifier_value'] = 'JMBG mora sadržavati 13 znamenki.'
        if errors:
            raise ValidationError(errors)

    @staticmethod
    def _hash_value(value):
        if isinstance(value, (date, Decimal)):
            return str(value)
        return value

    def content_snapshot(self) -> dict:
        return {
            field_name: self._hash_value(getattr(self, field_name))
            for field_name in self.HASHED_FIELD_NAMES
        }

    def calculate_content_hash(self) -> str:
        canonical_payload = json.dumps(
            self.content_snapshot(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
        )
        return hashlib.sha256(canonical_payload.encode('utf-8')).hexdigest()

    @with_tenant_schema
    def save(self, *args, **kwargs):
        self.identifier_type = self.identifier_type or None
        self.identifier_value = (self.identifier_value or '').strip() or None
        previous_hash = None
        if self.pk:
            previous_hash = type(self).objects.filter(pk=self.pk).values_list(
                'content_hash', flat=True
            ).first()
        self.content_hash = self.calculate_content_hash()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = tuple(set(update_fields) | {'content_hash'})
        with transaction.atomic():
            result = super().save(*args, **kwargs)
            if previous_hash != self.content_hash:
                BaptismDetailsHistory.objects.create(
                    baptism_details=self,
                    event_id=self.event_id,
                    content_hash=self.content_hash,
                    snapshot=self.content_snapshot(),
                    changed_by_id=getattr(self.event, 'updated_by_id', None),
                    change_type=(
                        BaptismDetailsHistory.ChangeType.CREATED
                        if previous_hash is None
                        else BaptismDetailsHistory.ChangeType.UPDATED
                    ),
                )
        return result


class BaptismDetailsHistory(models.Model):
    """Nepromenjivi snapshot svake stvarne promjene matičnog upisa."""

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Kreirano'
        UPDATED = 'updated', 'Ažurirano'

    id = models.BigAutoField(primary_key=True)
    baptism_details = models.ForeignKey(
        BaptismDetails, verbose_name='Podaci o krštenju',
        on_delete=models.PROTECT, related_name='history',
    )
    event = models.ForeignKey(
        SacramentalEvent, verbose_name='Krštenje',
        on_delete=models.PROTECT, related_name='baptism_history',
    )
    change_type = models.CharField('Vrsta promjene', max_length=12, choices=ChangeType.choices)
    snapshot = models.JSONField('Snapshot podataka')
    content_hash = models.CharField('Hash sadržaja', max_length=64, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Promijenio',
        on_delete=models.PROTECT, null=True, blank=True,
        related_name='baptism_detail_changes',
    )
    created_at = models.DateTimeField('Vrijeme promjene', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'pastoral_baptismdetailshistory'
        ordering = ('-created_at', '-id')
        indexes = (
            models.Index(
                fields=('baptism_details', 'created_at'),
                name='baptism_history_record_time',
            ),
        )
        verbose_name = 'Povijest podataka o krštenju'
        verbose_name_plural = 'Povijest podataka o krštenjima'

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Povijesni zapis krštenja je nepromjenjiv.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Povijesni zapis krštenja ne smije se brisati.')


class MarriageDetails(FCTB):
    """Operational details specific to a marriage preparation and celebration."""

    HASHED_FIELD_NAMES = (
        'entry_number', 'physical_page', 'marriage_date', 'marriage_place',
        'groom_first_name', 'groom_last_name', 'groom_birth_place',
        'groom_birth_date', 'groom_oib', 'groom_religion',
        'groom_baptism_date', 'groom_baptism_parish',
        'groom_baptism_parish_address', 'groom_residence_address',
        'bride_first_name', 'bride_last_name', 'bride_birth_place',
        'bride_birth_date', 'bride_oib', 'bride_religion',
        'bride_baptism_date', 'bride_baptism_parish',
        'bride_baptism_parish_address', 'bride_residence_address',
        'groom_father_first_name', 'groom_father_last_name',
        'groom_mother_first_name', 'groom_mother_maiden_name',
        'bride_father_first_name', 'bride_father_last_name',
        'bride_mother_first_name', 'bride_mother_maiden_name',
        'groom_witness_first_name', 'groom_witness_last_name',
        'bride_witness_first_name', 'bride_witness_last_name',
        'officiant_first_name', 'officiant_last_name', 'officiant_role',
        'notes',
    )

    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Vjenčanje', on_delete=models.PROTECT,
        related_name='marriage_details',
    )
    entry_number = models.PositiveIntegerField('Redni broj', null=True, blank=True)
    physical_page = models.CharField('Stranica u fizičkoj knjizi', max_length=40, null=True, blank=True)
    marriage_date = models.DateField('Datum vjenčanja', null=True, blank=True)
    marriage_year = models.GeneratedField(
        verbose_name='Godina vjenčanja', expression=ExtractYear('marriage_date'),
        output_field=models.PositiveSmallIntegerField(null=True),
        db_persist=True, db_index=True, editable=False,
    )
    marriage_place = models.CharField('Mjesto vjenčanja', max_length=200, default='')
    groom_first_name = models.CharField('Ime zaručnika', max_length=160, default='')
    groom_last_name = models.CharField('Prezime zaručnika', max_length=160, default='')
    groom_birth_place = models.CharField('Mjesto rođenja zaručnika', max_length=200, default='')
    groom_birth_date = models.DateField('Datum rođenja zaručnika', null=True, blank=True)
    groom_oib = models.CharField('OIB zaručnika', max_length=11, null=True, blank=True, db_index=True)
    groom_religion = models.CharField('Vjera zaručnika', max_length=120, default='')
    groom_baptism_date = models.DateField('Datum krštenja zaručnika', null=True, blank=True)
    groom_baptism_parish = models.CharField('Župa krštenja zaručnika', max_length=200, default='')
    groom_baptism_parish_address = models.CharField('Adresa župe krštenja zaručnika', max_length=255, default='')
    groom_residence_address = models.CharField('Adresa prebivališta zaručnika', max_length=255, default='')
    bride_first_name = models.CharField('Ime zaručnice', max_length=160, default='')
    bride_last_name = models.CharField('Prezime zaručnice', max_length=160, default='')
    bride_birth_place = models.CharField('Mjesto rođenja zaručnice', max_length=200, default='')
    bride_birth_date = models.DateField('Datum rođenja zaručnice', null=True, blank=True)
    bride_oib = models.CharField('OIB zaručnice', max_length=11, null=True, blank=True, db_index=True)
    bride_religion = models.CharField('Vjera zaručnice', max_length=120, default='')
    bride_baptism_date = models.DateField('Datum krštenja zaručnice', null=True, blank=True)
    bride_baptism_parish = models.CharField('Župa krštenja zaručnice', max_length=200, default='')
    bride_baptism_parish_address = models.CharField('Adresa župe krštenja zaručnice', max_length=255, default='')
    bride_residence_address = models.CharField('Adresa prebivališta zaručnice', max_length=255, default='')
    groom_father_first_name = models.CharField('Ime oca zaručnika', max_length=160, default='')
    groom_father_last_name = models.CharField('Prezime oca zaručnika', max_length=160, default='')
    groom_mother_first_name = models.CharField('Ime majke zaručnika', max_length=160, default='')
    groom_mother_maiden_name = models.CharField('Djevojačko prezime majke zaručnika', max_length=160, default='')
    bride_father_first_name = models.CharField('Ime oca zaručnice', max_length=160, default='')
    bride_father_last_name = models.CharField('Prezime oca zaručnice', max_length=160, default='')
    bride_mother_first_name = models.CharField('Ime majke zaručnice', max_length=160, default='')
    bride_mother_maiden_name = models.CharField('Djevojačko prezime majke zaručnice', max_length=160, default='')
    groom_witness_first_name = models.CharField('Ime svjedoka zaručnika', max_length=160, default='')
    groom_witness_last_name = models.CharField('Prezime svjedoka zaručnika', max_length=160, default='')
    bride_witness_first_name = models.CharField('Ime svjedoka zaručnice', max_length=160, default='')
    bride_witness_last_name = models.CharField('Prezime svjedoka zaručnice', max_length=160, default='')
    officiant_first_name = models.CharField('Ime vjenčatelja', max_length=160, default='')
    officiant_last_name = models.CharField('Prezime vjenčatelja', max_length=160, default='')
    officiant_role = models.CharField('Služba vjenčatelja', max_length=120, default='')
    notes = models.TextField('Napomene', null=True, blank=True)
    content_hash = models.CharField('Hash sadržaja', max_length=64, editable=False, db_index=True, default='')
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
        indexes = (
            models.Index(fields=('groom_last_name', 'groom_first_name'), name='marriage_groom_name'),
            models.Index(fields=('bride_last_name', 'bride_first_name'), name='marriage_bride_name'),
        )
        constraints = (
            models.CheckConstraint(condition=Q(groom_birth_date__isnull=True) | Q(marriage_date__isnull=True) | Q(groom_birth_date__lte=models.F('marriage_date')), name='marriage_groom_birth_before'),
            models.CheckConstraint(condition=Q(bride_birth_date__isnull=True) | Q(marriage_date__isnull=True) | Q(bride_birth_date__lte=models.F('marriage_date')), name='marriage_bride_birth_before'),
        )
        verbose_name = 'Podaci o vjenčanju'
        verbose_name_plural = 'Podaci o vjenčanjima'

    def __str__(self):
        return self.couple_display_name

    def clean(self):
        super().clean()
        errors = {}
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.MARRIAGE:
            errors['event'] = 'Podaci o vjenčanju mogu pripadati samo vjenčanju.'
        for field_name, label in (('groom_oib', 'OIB zaručnika'), ('bride_oib', 'OIB zaručnice')):
            value = (getattr(self, field_name) or '').strip()
            if value and (len(value) != 11 or not value.isdigit()):
                errors[field_name] = f'{label} mora sadržavati 11 znamenki.'
        if self.groom_birth_date and self.marriage_date and self.groom_birth_date > self.marriage_date:
            errors['groom_birth_date'] = 'Datum rođenja ne može biti nakon vjenčanja.'
        if self.bride_birth_date and self.marriage_date and self.bride_birth_date > self.marriage_date:
            errors['bride_birth_date'] = 'Datum rođenja ne može biti nakon vjenčanja.'
        if errors:
            raise ValidationError(errors)

    def content_snapshot(self):
        return {name: BaptismDetails._hash_value(getattr(self, name)) for name in self.HASHED_FIELD_NAMES}

    def calculate_content_hash(self):
        payload = json.dumps(self.content_snapshot(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    @with_tenant_schema
    def save(self, *args, **kwargs):
        self.groom_oib = (self.groom_oib or '').strip() or None
        self.bride_oib = (self.bride_oib or '').strip() or None
        previous_hash = type(self).objects.filter(pk=self.pk).values_list('content_hash', flat=True).first() if self.pk else None
        self.content_hash = self.calculate_content_hash()
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = tuple(set(kwargs['update_fields']) | {'content_hash'})
        with transaction.atomic():
            result = super().save(*args, **kwargs)
            if previous_hash != self.content_hash:
                MarriageDetailsHistory.objects.create(
                    marriage_details=self, event_id=self.event_id,
                    change_type=MarriageDetailsHistory.ChangeType.CREATED if previous_hash is None else MarriageDetailsHistory.ChangeType.UPDATED,
                    snapshot=self.content_snapshot(), content_hash=self.content_hash,
                    changed_by_id=getattr(self.event, 'updated_by_id', None),
                )
        return result


class MarriageDetailsHistory(models.Model):
    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Kreirano'
        UPDATED = 'updated', 'Ažurirano'

    id = models.BigAutoField(primary_key=True)
    marriage_details = models.ForeignKey(MarriageDetails, on_delete=models.PROTECT, related_name='history', verbose_name='Podaci o vjenčanju')
    event = models.ForeignKey(SacramentalEvent, on_delete=models.PROTECT, related_name='marriage_history', verbose_name='Vjenčanje')
    change_type = models.CharField('Vrsta promjene', max_length=12, choices=ChangeType.choices)
    snapshot = models.JSONField('Snapshot podataka')
    content_hash = models.CharField('Hash sadržaja', max_length=64, db_index=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='marriage_detail_changes', verbose_name='Promijenio')
    created_at = models.DateTimeField('Vrijeme promjene', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'pastoral_marriagedetailshistory'
        ordering = ('-created_at', '-id')
        indexes = (models.Index(fields=('marriage_details', 'created_at'), name='marriage_history_record_time'),)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Povijesni zapis vjenčanja je nepromjenjiv.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Povijesni zapis vjenčanja ne smije se brisati.')


class FuneralDetails(FCTB):
    """Operational and pastoral details specific to a funeral."""

    class Sex(models.TextChoices):
        MALE = 'male', 'Muško'
        FEMALE = 'female', 'Žensko'

    class IdentifierType(models.TextChoices):
        OIB = 'oib', 'OIB'
        JMBG = 'jmbg', 'JMBG'

    HASHED_FIELD_NAMES = (
        'entry_number', 'physical_page', 'death_date', 'death_place',
        'first_name', 'last_name', 'sex', 'birth_place', 'birth_date',
        'identifier_type', 'identifier_value', 'spouse_first_name',
        'spouse_last_name', 'father_first_name', 'father_last_name',
        'mother_first_name', 'mother_last_name', 'residence_address',
        'received_confession', 'received_anointing', 'received_communion',
        'burial_place', 'burial_date', 'minister_first_name',
        'minister_last_name', 'cause_of_death', 'notes',
    )

    event = models.OneToOneField('sakramenti.SacramentalEvent', verbose_name='Pogreb', on_delete=models.PROTECT,
        related_name='funeral_details',
    )
    entry_number = models.PositiveIntegerField('Redni broj', null=True, blank=True)
    physical_page = models.CharField('Stranica u fizičkoj knjizi', max_length=40, null=True, blank=True)
    death_date = models.DateField('Datum smrti', null=True, blank=True)
    death_year = models.GeneratedField(
        verbose_name='Godina smrti', expression=ExtractYear('death_date'),
        output_field=models.PositiveSmallIntegerField(null=True),
        db_persist=True, db_index=True, editable=False,
    )
    death_place = models.CharField('Mjesto smrti', max_length=200, default='')
    first_name = models.CharField('Ime osobe', max_length=160, default='')
    last_name = models.CharField('Prezime osobe', max_length=160, default='')
    sex = models.CharField(
        'Spol', max_length=8, choices=Sex.choices, null=True, blank=True
    )
    birth_place = models.CharField('Mjesto rođenja', max_length=200, default='')
    birth_date = models.DateField('Datum rođenja', null=True, blank=True)
    identifier_type = models.CharField('Vrsta identifikatora', max_length=4, choices=IdentifierType.choices, null=True, blank=True)
    identifier_value = models.CharField('JMBG / OIB', max_length=13, null=True, blank=True, db_index=True)
    spouse_first_name = models.CharField('Ime supružnika', max_length=160, null=True, blank=True)
    spouse_last_name = models.CharField('Prezime supružnika', max_length=160, null=True, blank=True)
    father_first_name = models.CharField('Ime oca', max_length=160, default='')
    father_last_name = models.CharField('Prezime oca', max_length=160, default='')
    mother_first_name = models.CharField('Ime majke', max_length=160, default='')
    mother_last_name = models.CharField('Prezime majke', max_length=160, default='')
    residence_address = models.CharField('Adresa prebivališta', max_length=255, default='')
    received_confession = models.BooleanField('Ispovijed', default=False)
    received_anointing = models.BooleanField('Bolesničko pomazanje', default=False)
    received_communion = models.BooleanField('Pričest', default=False)
    burial_place = models.CharField('Mjesto pokopa', max_length=240, default='')
    burial_date = models.DateField('Datum pokopa', null=True, blank=True)
    minister_first_name = models.CharField('Ime crkvenog službenika', max_length=160, default='')
    minister_last_name = models.CharField('Prezime crkvenog službenika', max_length=160, default='')
    cause_of_death = models.CharField('Uzrok smrti', max_length=255, null=True, blank=True)
    notes = models.TextField('Bilješke', null=True, blank=True)
    content_hash = models.CharField('Hash sadržaja', max_length=64, editable=False, db_index=True, default='')
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
        indexes = (models.Index(fields=('last_name', 'first_name'), name='funeral_person_name'),)
        constraints = (
            models.CheckConstraint(
                condition=Q(birth_date__isnull=True) | Q(death_date__isnull=True) | Q(birth_date__lte=models.F('death_date')),
                name='funeral_birth_not_after_death',
            ),
            models.CheckConstraint(
                condition=Q(identifier_type__isnull=True, identifier_value__isnull=True) | Q(identifier_type__isnull=False, identifier_value__isnull=False),
                name='funeral_identifier_pair',
            ),
        )
        verbose_name = 'Podaci o pogrebu'
        verbose_name_plural = 'Podaci o pogrebima'

    def __str__(self):
        recipient = self.event.participants.filter(
            role=EventParticipant.Role.RECIPIENT
        ).first()
        return recipient.historical_name if recipient else str(self.event)

    def clean(self):
        super().clean()
        errors = {}
        if self.event_id and self.event.event_type != SacramentalEvent.EventType.FUNERAL:
            errors['event'] = 'Podaci o pogrebu mogu pripadati samo pogrebu.'
        if self.birth_date and self.death_date and self.birth_date > self.death_date:
            errors['death_date'] = 'Datum smrti ne može biti prije datuma rođenja.'
        identifier = (self.identifier_value or '').strip()
        if bool(self.identifier_type) != bool(identifier):
            errors['identifier_value'] = 'Vrsta i vrijednost identifikatora unose se zajedno.'
        elif self.identifier_type == self.IdentifierType.OIB and (len(identifier) != 11 or not identifier.isdigit()):
            errors['identifier_value'] = 'OIB mora sadržavati 11 znamenki.'
        elif self.identifier_type == self.IdentifierType.JMBG and (len(identifier) != 13 or not identifier.isdigit()):
            errors['identifier_value'] = 'JMBG mora sadržavati 13 znamenki.'
        if errors:
            raise ValidationError(errors)

    def content_snapshot(self):
        return {name: BaptismDetails._hash_value(getattr(self, name)) for name in self.HASHED_FIELD_NAMES}

    def calculate_content_hash(self):
        payload = json.dumps(self.content_snapshot(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    @with_tenant_schema
    def save(self, *args, **kwargs):
        self.identifier_type = self.identifier_type or None
        self.identifier_value = (self.identifier_value or '').strip() or None
        previous_hash = type(self).objects.filter(pk=self.pk).values_list('content_hash', flat=True).first() if self.pk else None
        self.content_hash = self.calculate_content_hash()
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = tuple(set(kwargs['update_fields']) | {'content_hash'})
        with transaction.atomic():
            result = super().save(*args, **kwargs)
            if previous_hash != self.content_hash:
                FuneralDetailsHistory.objects.create(
                    funeral_details=self, event_id=self.event_id,
                    change_type=FuneralDetailsHistory.ChangeType.CREATED if previous_hash is None else FuneralDetailsHistory.ChangeType.UPDATED,
                    snapshot=self.content_snapshot(), content_hash=self.content_hash,
                    changed_by_id=getattr(self.event, 'updated_by_id', None),
                )
        return result


class FuneralDetailsHistory(models.Model):
    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Kreirano'
        UPDATED = 'updated', 'Ažurirano'

    id = models.BigAutoField(primary_key=True)
    funeral_details = models.ForeignKey(FuneralDetails, on_delete=models.PROTECT, related_name='history', verbose_name='Podaci o umrlom')
    event = models.ForeignKey(SacramentalEvent, on_delete=models.PROTECT, related_name='funeral_history', verbose_name='Pogreb')
    change_type = models.CharField('Vrsta promjene', max_length=12, choices=ChangeType.choices)
    snapshot = models.JSONField('Snapshot podataka')
    content_hash = models.CharField('Hash sadržaja', max_length=64, db_index=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='funeral_detail_changes', verbose_name='Promijenio')
    created_at = models.DateTimeField('Vrijeme promjene', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'pastoral_funeraldetailshistory'
        ordering = ('-created_at', '-id')
        indexes = (
            models.Index(
                fields=('funeral_details', 'created_at'),
                name='funeral_history_record_time',
            ),
        )
        verbose_name = 'Povijest podataka o umrlom'
        verbose_name_plural = 'Povijest podataka o umrlima'

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Povijesni zapis umrlog je nepromjenjiv.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Povijesni zapis umrlog ne smije se brisati.')


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
