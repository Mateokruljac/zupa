import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class UUIDTimestampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Diocese(UUIDTimestampedModel):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Biskupija'
        verbose_name_plural = 'Biskupije'

    def __str__(self):
        return self.name


class ParishMembership(UUIDTimestampedModel):
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


class TenantDatabase(UUIDTimestampedModel):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planirano'
        PROVISIONING = 'provisioning', 'Provisioning'
        READY = 'ready', 'Spremno'
        MAINTENANCE = 'maintenance', 'Održavanje'
        FAILED = 'failed', 'Greška'
        RETIRED = 'retired', 'Umirovljeno'

    parish = models.OneToOneField(
        'pastoral.Parish',
        on_delete=models.PROTECT,
        related_name='tenant_database',
    )
    alias = models.SlugField(unique=True)
    provider = models.CharField(max_length=40, default='postgresql')
    deployment_stamp = models.CharField(max_length=80, blank=True)
    database_name = models.CharField(max_length=128, blank=True)
    resource_id = models.CharField(max_length=255, blank=True)
    secret_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text='Referenca na secrets manager; nikada lozinka ili connection string.',
    )
    region = models.CharField(max_length=80, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
        db_index=True,
    )
    schema_version = models.CharField(max_length=64, blank=True)
    last_migrated_at = models.DateTimeField(null=True, blank=True)
    last_backup_at = models.DateTimeField(null=True, blank=True)
    last_restore_test_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('alias',)
        verbose_name = 'Tenant baza'
        verbose_name_plural = 'Tenant baze'

    def __str__(self):
        return f'{self.parish} · {self.alias}'

    def clean(self):
        super().clean()
        lowered = self.secret_ref.lower()
        if '://' in lowered or 'password=' in lowered or 'pwd=' in lowered:
            raise ValidationError({'secret_ref': 'Upišite samo referencu na tajnu, ne connection string.'})


class LicenseGrant(UUIDTimestampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Na čekanju'
        ACTIVE = 'active', 'Aktivno'
        SUSPENDED = 'suspended', 'Suspendirano'
        TERMINATED = 'terminated', 'Prekinuto'

    license_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.PROTECT,
        related_name='license_grants',
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    valid_from = models.DateField()
    valid_until = models.DateField()
    grace_until = models.DateField()
    plan_code = models.SlugField(default='standard')
    seat_limit = models.PositiveIntegerField(null=True, blank=True)
    terms_version = models.CharField(max_length=32, default='1')
    security_suspended = models.BooleanField(default=False, db_index=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='approved_license_grants',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ('-valid_until', '-created_at')
        verbose_name = 'Licenca'
        verbose_name_plural = 'Licence'
        constraints = (
            models.CheckConstraint(
                condition=Q(valid_until__gte=F('valid_from')),
                name='control_license_valid_period',
            ),
            models.CheckConstraint(
                condition=Q(grace_until__gte=F('valid_until')),
                name='control_license_grace_period',
            ),
        )
        indexes = (
            models.Index(fields=('parish', 'status', 'valid_until'), name='control_license_lookup'),
        )

    def __str__(self):
        return f'{self.parish} · {self.valid_from:%d.%m.%Y}–{self.valid_until:%d.%m.%Y}'


class ManualPayment(UUIDTimestampedModel):
    class Status(models.TextChoices):
        RECORDED = 'recorded', 'Evidentirano'
        VERIFIED = 'verified', 'Provjereno'
        REJECTED = 'rejected', 'Odbijeno'
        REVERSED = 'reversed', 'Stornirano'

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.PROTECT,
        related_name='manual_payments',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    value_date = models.DateField()
    payer_name = models.CharField(max_length=200)
    bank_reference = models.CharField(max_length=140, blank=True)
    statement_reference = models.CharField(max_length=255, blank=True)
    coverage_from = models.DateField(null=True, blank=True)
    coverage_until = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.RECORDED,
        db_index=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_manual_payments',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='verified_manual_payments',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-value_date', '-created_at')
        verbose_name = 'Ručna uplata'
        verbose_name_plural = 'Ručne uplate'
        constraints = (
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name='control_payment_positive_amount',
            ),
            models.CheckConstraint(
                condition=(
                    Q(coverage_from__isnull=True, coverage_until__isnull=True)
                    | Q(
                        coverage_from__isnull=False,
                        coverage_until__isnull=False,
                        coverage_until__gte=F('coverage_from'),
                    )
                ),
                name='control_payment_coverage_period',
            ),
        )
        indexes = (
            models.Index(fields=('parish', 'status', 'value_date'), name='control_payment_lookup'),
        )

    def __str__(self):
        return f'{self.parish} · {self.amount} {self.currency} · {self.value_date:%d.%m.%Y}'

    def clean(self):
        super().clean()
        if self.verified_by_id and self.verified_by_id == self.recorded_by_id:
            raise ValidationError('Ista osoba ne može evidentirati i potvrditi uplatu.')


class LicenseEntitlement(UUIDTimestampedModel):
    grant = models.ForeignKey(
        LicenseGrant,
        on_delete=models.PROTECT,
        related_name='entitlements',
    )
    code = models.SlugField()
    enabled = models.BooleanField(default=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('grant', 'code')
        verbose_name = 'Licencno pravo'
        verbose_name_plural = 'Licencna prava'
        constraints = (
            models.UniqueConstraint(
                fields=('grant', 'code'),
                name='control_unique_grant_entitlement',
            ),
        )

    def __str__(self):
        return f'{self.grant.parish} · {self.code}'


class ImmutableEventModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError('Audit događaj je nepromjenjiv.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Audit događaj se ne smije brisati.')


class LicenseDecision(ImmutableEventModel):
    class Action(models.TextChoices):
        ACTIVATE = 'activate', 'Aktivacija'
        RENEW = 'renew', 'Obnova'
        SUSPEND = 'suspend', 'Suspenzija'
        REINSTATE = 'reinstate', 'Ponovna aktivacija'
        TERMINATE = 'terminate', 'Prekid'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant = models.ForeignKey(
        LicenseGrant,
        on_delete=models.PROTECT,
        related_name='decisions',
    )
    action = models.CharField(max_length=16, choices=Action.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='license_decisions',
    )
    reason = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-occurred_at',)
        verbose_name = 'Odluka o licenci'
        verbose_name_plural = 'Odluke o licencama'

    def __str__(self):
        return f'{self.grant.parish} · {self.get_action_display()} · {self.occurred_at:%d.%m.%Y}'


class ControlPlaneAuditEvent(ImmutableEventModel):
    class Outcome(models.TextChoices):
        SUCCESS = 'success', 'Uspjeh'
        DENIED = 'denied', 'Odbijeno'
        FAILURE = 'failure', 'Greška'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='control_audit_events',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='control_audit_events',
    )
    event_type = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    outcome = models.CharField(
        max_length=16,
        choices=Outcome.choices,
        default=Outcome.SUCCESS,
        db_index=True,
    )
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-occurred_at',)
        verbose_name = 'Control-plane audit događaj'
        verbose_name_plural = 'Control-plane audit događaji'
        indexes = (
            models.Index(fields=('parish', 'occurred_at'), name='control_audit_parish_time'),
            models.Index(fields=('actor', 'occurred_at'), name='control_audit_actor_time'),
        )

    def __str__(self):
        return f'{self.event_type} · {self.get_outcome_display()} · {self.occurred_at:%d.%m.%Y %H:%M}'

