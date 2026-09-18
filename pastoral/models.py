"""Jezgra pastoral shella — župa i OTP."""
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)

import uuid

from core.models import FCTA, SCD1, SCD2, ContentHashedModel


def otp_challenge_expiry():
    return timezone.now() + timedelta(
        minutes=getattr(settings, 'OTP_TTL_MINUTES', 10),
    )



class UUIDTimestampedModel(FCTA):
    """Compatibility alias: UUID fact/dimension timestamps come from FCTA."""

    class Meta:
        abstract = True


class Diocese(SCD1):
    unified_key_origin_fields = ('code',)

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Biskupija'
        verbose_name_plural = 'Biskupije'

    def __str__(self):
        return self.name


class Parish(ContentHashedModel):
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
        'pastoral.Diocese',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parishes',
    )
    church_sui_iuris = models.ForeignKey('zupa_vjernici.ChurchSuiIuris',
        verbose_name='Crkva sui iuris',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='parishes',
    )
    ecclesiastical_jurisdiction = models.ForeignKey('zupa_vjernici.EcclesiasticalJurisdiction',
        verbose_name='Crkvena jurisdikcija',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='parishes',
    )
    default_liturgical_tradition = models.ForeignKey('liturgija.LiturgicalTradition',
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
    unified_key = models.CharField(
        'Jedinstveni ključ',
        max_length=512,
        blank=True,
        db_index=True,
    )
    is_active = models.BooleanField('Aktivno', default=True, db_index=True)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    unified_key_origin_fields = ('slug',)

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


    def save(self, *args, **kwargs):
        if self.slug:
            self.unified_key = self.slug
        self.is_active = self.lifecycle_status == self.LifecycleStatus.ACTIVE
        return super().save(*args, **kwargs)


class OtpChallenge(ContentHashedModel):
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
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def content_hash_field_names(self) -> tuple[str, ...]:
        return ('email', 'role', 'used', 'failed_attempts', 'locked_at')


class PhaseTwoRecord(FCTA):
    """ORM spremište za kolekcije faze 2 (legacy payload po ključu)."""

    parish = models.ForeignKey(
        Parish,
        on_delete=models.CASCADE,
        related_name='phase_two_records',
    )
    collection_key = models.CharField(max_length=80, db_index=True)
    public_identifier = models.CharField(max_length=120, blank=True, db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'collection_key', 'public_identifier')]
        indexes = [
            models.Index(fields=['parish', 'collection_key']),
        ]

class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(ContentHashedModel, AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    ROLE_CHOICES = [
        ('zupnik', 'Župnik'),
        ('vikar', 'Vikar'),
        ('upravitelj', 'Župni upravitelj'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(max_length=254, unique=True, db_index=True)
    name = models.CharField(max_length=100, db_index=True, blank=True, default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='zupnik')
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    address = models.CharField(max_length=100, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, default='')
    unified_key = models.CharField(
        'Jedinstveni ključ',
        max_length=512,
        blank=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Ažurirano', auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users_user'

    def save(self, *args, **kwargs):
        self.unified_key = self.email or self.unified_key
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    @property
    def role_label(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)



class ParishMembership(SCD2):
    unified_key_origin_fields = ('parish_id', 'user_id')
    class Role(models.TextChoices):
        PASTOR = 'zupnik', 'Župnik'
        ASSOCIATE = 'vikar', 'Župnik suradnik / vikar'
        MANAGER = 'upravitelj', 'Župni upravitelj'
        OFFICE = 'ured', 'Župni ured'
        FINANCE = 'financije', 'Financije'
        AUDITOR = 'revizor', 'Revizor'
        DIOCESE_VIEWER = 'biskupija', 'Biskupijski preglednik'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Aktivno'
        SUSPENDED = 'suspended', 'Suspendirano'
        REVOKED = 'revoked', 'Opozvano'

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.PROTECT,
        related_name='memberships',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='parish_memberships',
    )
    role = models.CharField(max_length=24, choices=Role.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    permission_set = models.JSONField(default=dict, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='approved_parish_memberships',
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='revoked_parish_memberships',
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ('parish', 'user__email')
        verbose_name = 'Članstvo u župi'
        verbose_name_plural = 'Članstva u župama'
        constraints = (
            models.UniqueConstraint(
                fields=('parish', 'user'),
                name='control_unique_parish_user_membership',
            ),
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F('valid_from')),
                name='control_membership_valid_period',
            ),
        )
        indexes = (
            models.Index(fields=('parish', 'status'), name='control_mem_parish_status'),
            models.Index(fields=('user', 'status'), name='control_mem_user_status'),
        )

    def __str__(self):
        return f'{self.user} · {self.parish} · {self.get_role_display()}'

    def is_valid_at(self, moment=None):
        moment = moment or timezone.now()
        return (
            self.status == self.Status.ACTIVE
            and self.valid_from <= moment
            and (self.valid_until is None or self.valid_until >= moment)
        )