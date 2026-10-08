import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

from django_multitenant.schema import with_tenant_schema


class Tenant(TenantMixin):
    """Jedna župa = jedan PostgreSQL schema.

    Poslovni podaci žive u tenant schemi. Ovaj red i domena žive u `public`.
    """

    name = models.CharField('Naziv', max_length=255)
    created_on = models.DateTimeField('Kreirano', auto_now_add=True)
    auto_create_schema = True

    class Meta:
        db_table = 'tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenanti'

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    class Meta:
        db_table = 'domain'
        verbose_name = 'Domena'
        verbose_name_plural = 'Domene'

    def __str__(self):
        return self.domain


class UserManager(BaseUserManager):
    """Korisnici žive u `public` (SHARED), vidljivi iz tenant schema search_patha."""

    @with_tenant_schema
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    @with_tenant_schema
    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Zajednički AUTH_USER_MODEL — tablica `users_user` u public schemi.

    `django.contrib.admin` u SHARED_APPS referencira ovu tablicu (`LogEntry`).
    """

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
        verbose_name = 'Korisnik'
        verbose_name_plural = 'Korisnici'

    @with_tenant_schema
    def save(self, *args, **kwargs):
        self.unified_key = self.email or self.unified_key
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    @property
    def role_label(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
