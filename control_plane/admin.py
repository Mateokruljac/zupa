from django.contrib import admin, messages
from django.utils import timezone

from .models import (
    ControlPlaneAuditEvent,
    Diocese,
    LicenseDecision,
    LicenseEntitlement,
    LicenseGrant,
    ManualPayment,
    ParishMembership,
    TenantDatabase,
)


class AuditAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return bool(obj is None and super().has_change_permission(request, obj))

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Diocese)
class DioceseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'active', 'updated_at')
    list_filter = ('active',)
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'name', 'code', 'active', 'created_at', 'updated_at')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ParishMembership)
class ParishMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'parish', 'role', 'status', 'valid_from', 'valid_until')
    list_filter = ('status', 'role', 'parish')
    search_fields = ('user__email', 'user__name', 'parish__slug')
    autocomplete_fields = ('user', 'parish', 'approved_by', 'revoked_by')
    readonly_fields = ('id', 'created_at', 'updated_at', 'revoked_at', 'revoked_by')
    fields = (
        'id', 'parish', 'user', 'role', 'status', 'permission_set',
        'valid_from', 'valid_until', 'approved_by',
        'revoked_by', 'revoked_at', 'revocation_reason',
        'created_at', 'updated_at',
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TenantDatabase)
class TenantDatabaseAdmin(admin.ModelAdmin):
    list_display = (
        'alias', 'parish', 'provider', 'deployment_stamp', 'region',
        'status', 'schema_version', 'secret_configured',
    )
    list_filter = ('status', 'provider', 'deployment_stamp', 'region')
    search_fields = ('alias', 'parish__slug', 'database_name', 'resource_id')
    autocomplete_fields = ('parish',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Tenant', {'fields': ('id', 'parish', 'alias', 'status')}),
        ('Smještaj', {
            'fields': (
                'provider', 'deployment_stamp', 'region',
                'database_name', 'resource_id', 'secret_ref',
            ),
            'description': 'secret_ref je samo referenca na secrets manager. Lozinka i connection string ovdje su zabranjeni.',
        }),
        ('Operativno stanje', {
            'fields': (
                'schema_version', 'last_migrated_at',
                'last_backup_at', 'last_restore_test_at',
                'created_at', 'updated_at',
            ),
        }),
    )

    @admin.display(boolean=True, description='Secret ref')
    def secret_configured(self, obj):
        return bool(obj.secret_ref)

    def has_delete_permission(self, request, obj=None):
        return False


class LicenseEntitlementInline(admin.TabularInline):
    model = LicenseEntitlement
    extra = 0
    fields = ('code', 'enabled', 'configuration', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


@admin.register(LicenseGrant)
class LicenseGrantAdmin(admin.ModelAdmin):
    list_display = (
        'parish', 'status', 'plan_code', 'valid_from', 'valid_until',
        'grace_until', 'security_suspended', 'approved_by',
    )
    list_filter = ('status', 'plan_code', 'security_suspended', 'valid_until')
    search_fields = ('parish__slug', 'license_code', 'plan_code')
    autocomplete_fields = ('parish', 'approved_by')
    readonly_fields = (
        'id', 'license_code', 'approved_by', 'approved_at',
        'version', 'created_at', 'updated_at',
    )
    fields = (
        'id', 'license_code', 'parish', 'status', 'plan_code',
        'valid_from', 'valid_until', 'grace_until', 'seat_limit',
        'terms_version', 'security_suspended', 'suspension_reason',
        'approved_by', 'approved_at', 'version', 'created_at', 'updated_at',
    )
    inlines = (LicenseEntitlementInline,)
    actions = ('activate_from_verified_payment',)

    @admin.action(description='Aktiviraj odabrane licence uz provjerenu uplatu')
    def activate_from_verified_payment(self, request, queryset):
        activated = 0
        rejected = 0
        for grant in queryset.select_related('parish'):
            payment = (
                ManualPayment.objects
                .filter(
                    parish=grant.parish,
                    status=ManualPayment.Status.VERIFIED,
                    coverage_from__lte=grant.valid_from,
                    coverage_until__gte=grant.valid_until,
                )
                .order_by('-value_date')
                .first()
            )
            if grant.status != LicenseGrant.Status.PENDING or payment is None:
                rejected += 1
                continue
            grant.status = LicenseGrant.Status.ACTIVE
            grant.approved_by = request.user
            grant.approved_at = timezone.now()
            grant.version += 1
            grant.save(update_fields=(
                'status', 'approved_by', 'approved_at', 'version', 'updated_at',
            ))
            LicenseDecision.objects.create(
                grant=grant,
                action=LicenseDecision.Action.ACTIVATE,
                actor=request.user,
                reason='Aktivacija nakon ručne provjere uplate.',
                metadata={'payment_id': str(payment.id)},
            )
            ControlPlaneAuditEvent.objects.create(
                parish=grant.parish,
                actor=request.user,
                event_type='license.activated',
                target_type='control_plane.LicenseGrant',
                target_id=str(grant.id),
                metadata={'payment_id': str(payment.id)},
            )
            activated += 1
        if activated:
            self.message_user(request, f'Aktivirano licenci: {activated}.', messages.SUCCESS)
        if rejected:
            self.message_user(
                request,
                f'Preskočeno licenci: {rejected}. Potrebna je pending licenca i provjerena uplata koju je potvrdila druga osoba.',
                messages.WARNING,
            )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ManualPayment)
class ManualPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'value_date', 'parish', 'amount', 'currency', 'payer_name',
        'status', 'recorded_by', 'verified_by',
    )
    list_filter = ('status', 'currency', 'value_date', 'parish')
    search_fields = ('parish__slug', 'payer_name', 'bank_reference', 'statement_reference')
    autocomplete_fields = ('parish',)
    readonly_fields = (
        'id', 'recorded_by', 'verified_by', 'verified_at',
        'created_at', 'updated_at',
    )
    fields = (
        'id', 'parish', 'amount', 'currency', 'value_date', 'payer_name',
        'bank_reference', 'statement_reference', 'coverage_from', 'coverage_until',
        'status', 'recorded_by', 'verified_by', 'verified_at', 'notes',
        'created_at', 'updated_at',
    )
    actions = ('verify_selected_payments',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
            obj.status = ManualPayment.Status.RECORDED
        obj.full_clean()
        super().save_model(request, obj, form, change)
        ControlPlaneAuditEvent.objects.create(
            parish=obj.parish,
            actor=request.user,
            event_type='payment.updated' if change else 'payment.recorded',
            target_type='control_plane.ManualPayment',
            target_id=str(obj.id),
            metadata={'status': obj.status},
        )

    @admin.action(description='Potvrdi odabrane evidentirane uplate')
    def verify_selected_payments(self, request, queryset):
        verified = 0
        rejected = 0
        for payment in queryset.select_related('parish', 'recorded_by'):
            if (
                payment.status != ManualPayment.Status.RECORDED
                or payment.recorded_by_id == request.user.id
            ):
                rejected += 1
                continue
            payment.status = ManualPayment.Status.VERIFIED
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.full_clean()
            payment.save(update_fields=(
                'status', 'verified_by', 'verified_at', 'updated_at',
            ))
            ControlPlaneAuditEvent.objects.create(
                parish=payment.parish,
                actor=request.user,
                event_type='payment.verified',
                target_type='control_plane.ManualPayment',
                target_id=str(payment.id),
            )
            verified += 1
        if verified:
            self.message_user(request, f'Potvrđeno uplata: {verified}.', messages.SUCCESS)
        if rejected:
            self.message_user(
                request,
                f'Preskočeno uplata: {rejected}. Evidentiranu uplatu mora potvrditi druga osoba.',
                messages.WARNING,
            )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LicenseEntitlement)
class LicenseEntitlementAdmin(admin.ModelAdmin):
    list_display = ('code', 'grant', 'enabled', 'updated_at')
    list_filter = ('enabled', 'code')
    search_fields = ('code', 'grant__parish__slug')
    autocomplete_fields = ('grant',)
    readonly_fields = ('id', 'created_at', 'updated_at')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LicenseDecision)
class LicenseDecisionAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ('occurred_at', 'grant', 'action', 'actor', 'reason')
    list_filter = ('action', 'occurred_at')
    search_fields = ('grant__parish__slug', 'actor__email', 'reason')
    readonly_fields = ('id', 'grant', 'action', 'actor', 'reason', 'metadata', 'occurred_at')
    fields = readonly_fields


@admin.register(ControlPlaneAuditEvent)
class ControlPlaneAuditEventAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ('occurred_at', 'event_type', 'parish', 'actor', 'outcome', 'target_type')
    list_filter = ('outcome', 'event_type', 'occurred_at')
    search_fields = ('event_type', 'parish__slug', 'actor__email', 'target_id', 'correlation_id')
    readonly_fields = (
        'id', 'parish', 'actor', 'event_type', 'target_type', 'target_id',
        'outcome', 'correlation_id', 'metadata', 'occurred_at',
    )
    fields = readonly_fields
