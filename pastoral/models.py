"""Jezgra pastoral shella — župa i OTP."""
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)

import uuid

from core.models import FCTA, SCD1, SCD2, OPEN_ENDED_VALID_TO
from zupa_vjernici.canonical import CanonicalTradition


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


class Parish(models.Model):
    """Jedna župa — tenant ureda.

    `canonical_tradition` razlikuje latinsku župu od župe Križevačke eparhije.
    Obred misa je `default_liturgical_tradition`, ne ovo polje.
    """

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
    canonical_tradition = models.CharField(
        'Kanonska tradicija',
        max_length=16,
        choices=CanonicalTradition.choices,
        default=CanonicalTradition.LATIN,
        db_index=True,
        help_text=(
            'Latinska za hrvatske biskupije; istočna za župe Križevačke eparhije.'
        ),
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
            and self.ecclesiastical_jurisdiction.canonical_tradition
            != self.canonical_tradition
        ):
            raise ValidationError({
                'ecclesiastical_jurisdiction': (
                    'Jurisdikcija mora biti iste kanonske tradicije kao župa.'
                ),
            })

    def canonical_tradition_for_events(self):
        """Vrijednost koju sakrament snima; prazno ostaje nepotvrđeno."""
        return self.canonical_tradition or 'unconfirmed'

    def save(self, *args, **kwargs):
        if self.slug:
            self.unified_key = self.slug
        self.is_active = self.lifecycle_status == self.LifecycleStatus.ACTIVE
        return super().save(*args, **kwargs)


class OtpChallenge(models.Model):
    """Jednokratni, vremenski ograničen izazov za prijavu.

    Stupac `code` drži salted hash OTP-a, nikad čitljiv kod.
    """

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


class User(AbstractBaseUser, PermissionsMixin):
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
                condition=Q(date_to=OPEN_ENDED_VALID_TO),
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