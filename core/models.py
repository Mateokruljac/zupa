"""Abstract SCD / DIM / FACT bases shared by every parish model.

Physical primary key is `id` (the `record_id` of the source SCD pattern).
FCTA and SCD types use UUID; FCTB uses a big integer. `unified_key` is the
business key. Open SCD2 rows use `date_to = OPEN_ENDED_VALID_TO`.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.db import IntegrityError, models, transaction
from django.utils import timezone

UNIFIED_KEY_SEPARATOR = '::'
OPEN_ENDED_VALID_TO = date(9999, 12, 31)
CONTENT_HASH_LENGTH = 64

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
    'content_hash',
})


def _json_ready(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


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


class ContentHashedModel(models.Model):
    """SHA-256 of canonical business fields. Not unique."""

    content_hash = models.CharField(
        'Sadržajni hash',
        max_length=CONTENT_HASH_LENGTH,
        blank=True,
        editable=False,
        db_index=True,
    )

    class Meta:
        abstract = True

    def content_hash_field_names(self) -> tuple[str, ...]:
        return tuple(
            field.name
            for field in self._meta.concrete_fields
            if field.name not in {
                'id',
                'content_hash',
                'created_at',
                'updated_at',
                'date_from',
                'date_to',
            }
        )

    def build_content_hash(self) -> str:
        payload = {}
        for field_name in self.content_hash_field_names():
            payload[field_name] = _json_ready(getattr(self, field_name, None))
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(encoded.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        self.content_hash = self.build_content_hash()
        return super().save(*args, **kwargs)


class SCDD(models.Model):
    """Draft / staging row before it becomes a dimension or fact."""

    class Action(models.TextChoices):
        NEW = 'new', 'Novi'
        CLONE = 'cln', 'Klon'
        CHANGE = 'chg', 'Izmjena'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_id = models.CharField(
        'Akcija nacrta',
        max_length=3,
        choices=Action.choices,
        default=Action.NEW,
    )

    class Meta:
        abstract = True


class SCDR(models.Model):
    """Report / projection row. Do not treat as an office write model."""

    class Meta:
        abstract = True


class SCD1(ContentHashedModel):
    """Type-1 dimension: overwrite in place. DIM SCD1."""

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
    unified_key_origin_fields: tuple[str, ...] = ()

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


class SCD2(ContentHashedModel):
    """Type-2 dimension: close the current row and insert a new version. DIM SCD2."""

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
        stored_row.save(update_fields=['date_to', 'updated_at', 'content_hash'])
        self.pk = None
        self.id = uuid.uuid4()
        self.unified_key = stored_row.unified_key
        self.date_from = timezone.localdate()
        self.date_to = OPEN_ENDED_VALID_TO

    def __str__(self):
        return self.unified_key


class SCD2A(SCD2):
    """SCD2 dimension that can be deactivated without dropping history."""

    is_active = models.BooleanField(
        'Aktivno',
        choices=ACTIVE_FLAG_CHOICES,
        default=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class FCTA(ContentHashedModel):
    """Fact table with a UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        abstract = True


class FCTB(ContentHashedModel):
    """Fact table with a big-integer primary key."""

    id = models.BigAutoField(primary_key=True, editable=False)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    class Meta:
        abstract = True
