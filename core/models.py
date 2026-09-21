"""Zajedničke SCD/FACT baze za sve poslovne modele župe.

Ovaj modul je jedino mjesto na kojem žive `unified_key`, `date_from`/`date_to`
i `save_new`. Domenske aplikacije nasljeđuju tipove; ne smiju ponovno
implementirati verziranje.

Fizički PK je `id` (record_id uzorka). Otvoreni SCD2 red ima
`date_to = OPEN_ENDED_VALID_TO` (9999-12-31). SCD2 ažuriranje otkriva
promjenu usporedbom polja, ne hashom.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from django.db import IntegrityError, models, transaction
from django.utils import timezone

UNIFIED_KEY_SEPARATOR = '::'
OPEN_ENDED_VALID_TO = date(9999, 12, 31)

ACTIVE_FLAG_CHOICES = (
    (True, 'Aktivno'),
    (False, 'Neaktivno'),
)

SCD2_TECHNICAL_FIELD_NAMES = frozenset({
    'id',
    'pk',
    'unified_key',
    'created_at',
    'updated_at',
    'date_from',
    'date_to',
})


def current_version_unique(*field_names, name: str) -> models.UniqueConstraint:
    """Parcijalni UNIQUE: najviše jedan otvoreni SCD2 red za zadana polja.

    Povijesne verzije smiju dijeliti isti poslovni identifikator.
    Bez ovog ograničenja `save_new` bi mogao ostaviti dva trenutačna reda.
    """
    return models.UniqueConstraint(
        fields=field_names,
        condition=models.Q(date_to=OPEN_ENDED_VALID_TO),
        name=name,
    )


def build_unified_key(instance, origin_field_names: list[str] | tuple[str, ...] | None) -> str:
    if not origin_field_names:
        raise ValueError('unified_key origin field names are required.')
    parts = []
    for field_path in origin_field_names:
        parts.append(str(_value_at_field_path(instance, field_path)))
    return UNIFIED_KEY_SEPARATOR.join(parts)


def _value_at_field_path(instance, field_path: str):
    current = instance
    for attribute_name in field_path.split('__'):
        current = getattr(current, attribute_name, None)
        if current is None:
            return ''
    return current


def _concrete_tracked_field_names(model_class, extra_excluded_names=None) -> list[str]:
    excluded_names = set(SCD2_TECHNICAL_FIELD_NAMES)
    if extra_excluded_names:
        excluded_names.update(extra_excluded_names)
    tracked_names = []
    for field in model_class._meta.get_fields():
        if not getattr(field, 'concrete', False):
            continue
        if getattr(field, 'auto_created', False) and not getattr(field, 'primary_key', False):
            continue
        if field.name in excluded_names:
            continue
        tracked_names.append(field.name)
    return tracked_names


class SCD1(models.Model):
    """Dimenzija tipa 1: overwrite u mjestu (osoba, vijeće, šifrarnici)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unified_key = models.CharField(
        'Jedinstveni ključ',
        max_length=512,
        blank=True,
        db_index=True,
    )
    is_active = models.BooleanField(
        'Aktivno',
        choices=ACTIVE_FLAG_CHOICES,
        default=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        origin_fields = kwargs.pop('unified_key_origin_fields', None)
        self._refresh_unified_key(origin_fields)
        return super().save(*args, **kwargs)

    def save_new(self, unified_key_origin_fields=None, *args, **kwargs):
        self._refresh_unified_key(unified_key_origin_fields)
        super().save(*args, **kwargs)

    def _refresh_unified_key(self, origin_fields=None):
        field_names = origin_fields or self.unified_key_origin_fields
        if field_names:
            self.unified_key = build_unified_key(self, field_names)
        elif not self.unified_key:
            self.unified_key = str(self.id or uuid.uuid4())

    def __str__(self):
        return self.unified_key


class CurrentSCD2Manager(models.Manager):
    """Manager koji vraća samo otvorene SCD2 redove.

    `objects` i dalje vidi cijelu povijest. UI i operativni store moraju
    čitati ovaj manager; inače bi se ista ulica/obitelj pojavila više puta.
    """

    def get_queryset(self):
        return super().get_queryset().filter(date_to=OPEN_ENDED_VALID_TO)


class SCD2(models.Model):
    """Dimenzija tipa 2: materijalna izmjena zatvara stari red i otvara novi.

    Ne koristi se za osobe (to je SCD1) niti za činjenice poput krštenja.
    Djeca koja FK-om drže `id` roditelja moraju se nakon verzije preusmjeriti
    na novi otvoreni red — vidi `upsert_current_household`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unified_key = models.CharField(
        'Jedinstveni ključ',
        max_length=512,
        blank=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)
    date_from = models.DateField('Vrijedi od', default=date.today)
    date_to = models.DateField(
        'Vrijedi do',
        default=OPEN_ENDED_VALID_TO,
        db_index=True,
    )
    unified_key_origin_fields: tuple[str, ...] = ()
    scd2_save_exclude_fields: tuple[str, ...] = ()
    objects = models.Manager()
    current = CurrentSCD2Manager()

    class Meta:
        abstract = True
        constraints = (
            models.CheckConstraint(
                condition=models.Q(date_to__gte=models.F('date_from')),
                name='%(app_label)s_%(class)s_valid_period',
            ),
        )

    @property
    def is_current(self) -> bool:
        return self.date_to == OPEN_ENDED_VALID_TO

    def save(self, *args, **kwargs):
        origin_fields = kwargs.pop('unified_key_origin_fields', None)
        field_names = origin_fields or self.unified_key_origin_fields
        if field_names and (self._state.adding or not self.unified_key):
            self.unified_key = build_unified_key(self, field_names)
        elif not self.unified_key:
            self.unified_key = str(self.id or uuid.uuid4())
        return super().save(*args, **kwargs)

    def save_new(self, exclude=None, unified_key_origin_fields=None, *args, **kwargs):
        """Spremi SCD2 zapis po pravilu verzije, ne običnim overwriteom.

        Novi identitet: zabranjuje drugi otvoreni red s istim `unified_key`.
        Postojeći otvoreni red: ako su se poslovna polja promijenila, zatvara
        ga (`date_to = jučer`) i umeće novi PK s istim `unified_key`.
        """
        model_class = type(self)
        if not self._state.adding:
            excluded = tuple(exclude or ()) + self.scd2_save_exclude_fields
            self._close_and_version_if_changed(excluded)
            return super().save(*args, **kwargs)

        origin_fields = unified_key_origin_fields or self.unified_key_origin_fields
        if origin_fields:
            self.unified_key = build_unified_key(self, origin_fields)
        elif not self.unified_key:
            self.unified_key = str(self.id or uuid.uuid4())
        if model_class.objects.filter(
            unified_key=self.unified_key,
            date_to=OPEN_ENDED_VALID_TO,
        ).exists():
            raise IntegrityError(
                f'A current row already exists for unified_key={self.unified_key}.'
            )
        if not self.date_from:
            self.date_from = timezone.localdate()
        self.date_to = OPEN_ENDED_VALID_TO
        return super().save(*args, **kwargs)

    @transaction.atomic
    def _close_and_version_if_changed(self, extra_excluded_names=None):
        """Zaključava trenutačni red pa ga zatvara ako je sadržaj stvarno drugačiji.

        Polja u `scd2_save_exclude_fields` (npr. telefon, bilješke) namjerno
        ne pokreću novu verziju — to su ispravci tipfelera, ne povijest adrese.
        """
        model_class = type(self)
        stored_row = model_class.objects.select_for_update().get(pk=self.pk)
        if stored_row.date_to != OPEN_ENDED_VALID_TO:
            return
        tracked_field_names = _concrete_tracked_field_names(
            model_class,
            extra_excluded_names,
        )
        has_business_change = any(
            getattr(stored_row, field_name) != getattr(self, field_name)
            for field_name in tracked_field_names
        )
        if not has_business_change:
            return
        stored_row.date_to = timezone.localdate() - timedelta(days=1)
        stored_row.save(update_fields=['date_to', 'updated_at'])
        self.pk = None
        self.id = uuid.uuid4()
        self.unified_key = stored_row.unified_key
        self.date_from = timezone.localdate()
        self.date_to = OPEN_ENDED_VALID_TO

    def __str__(self):
        return self.unified_key


def upsert_current_scd2(model_class, lookup: dict, defaults: dict):
    """Nađe otvoreni SCD2 red ili ga kreira; materijalnu izmjenu verzira.

    Args:
        lookup:
            Poslovni identitet (npr. parish + public_identifier), nikad fizički `id`.
        defaults:
            Polja koja se upisuju na otvoreni red.

    Returns:
        Tuple (instancija, created). Ako je verzija zatvorila stari red,
        vraćena instanca ima novi `id`.

    Side effects:
        Može zatvoriti prethodni otvoreni red. Ne preusmjerava djecu s FK-om
        na stari `id` — to rade pozivatelji (`upsert_current_household`).
    """
    current_row = model_class.current.filter(**lookup).first()
    if current_row is None:
        instance = model_class(**lookup, **defaults)
        instance.save_new()
        return instance, True
    for field_name, field_value in defaults.items():
        setattr(current_row, field_name, field_value)
    current_row.save_new()
    return current_row, False


def close_current_scd2_rows(queryset) -> int:
    """Zatvara otvorene redove umjesto DELETE.

    Povijest ostaje čitljiva. SCD2A dodatno gasi `is_active`.
    Fizikalno brisanje bi prekinulo FK-ove i izgubilo trag adrese/članstva.
    """
    yesterday = timezone.localdate() - timedelta(days=1)
    closed = 0
    for row in queryset.filter(date_to=OPEN_ENDED_VALID_TO).iterator():
        row.date_to = yesterday
        if hasattr(row, 'is_active'):
            row.is_active = False
            row.save(update_fields=['date_to', 'is_active', 'updated_at'])
        else:
            row.save(update_fields=['date_to', 'updated_at'])
        closed += 1
    return closed


class SCD2A(SCD2):
    """SCD2 dimenzija koju možemo deaktivirati bez brisanja povijesti (ulica, kućanstvo)."""

    is_active = models.BooleanField(
        'Aktivno',
        choices=ACTIVE_FLAG_CHOICES,
        default=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class FCTA(models.Model):
    """Činjenica s UUID primarnim ključem (sakramenti, blagajna, zadaci)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        abstract = True


class FCTB(models.Model):
    """Činjenica s integer PK — samo kad je visok volumen opravdan (npr. liturgijski kalendar)."""

    id = models.BigAutoField(primary_key=True, editable=False)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        abstract = True
