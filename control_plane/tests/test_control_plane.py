from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from control_plane.models import (
    ControlPlaneAuditEvent,
    LicenseGrant,
    ManualPayment,
    ParishMembership,
    TenantDatabase,
)
from control_plane.services.licenses import LicenseAccess, evaluate_license
from control_plane.tenant_context import (
    TenantContext,
    reset_current_tenant_context,
    set_current_tenant_context,
)
from pastoral.models import Parish
from pastoral.services.data import ParishDataService
from users.models import User


class ControlPlaneModelTests(TestCase):
    def setUp(self):
        self.parish = Parish.objects.create(
            slug='tenant-a',
            settings={'name': 'Župa A'},
            data={'tasks': [{'id': 'a-task'}]},
        )
        self.user = User.objects.create_user(
            email='tenant-a@example.test',
            password='Control-Plane-Test-938!',
            role='zupnik',
        )

    def make_grant(self, **overrides):
        values = {
            'parish': self.parish,
            'status': LicenseGrant.Status.ACTIVE,
            'valid_from': date(2026, 1, 1),
            'valid_until': date(2026, 12, 31),
            'grace_until': date(2027, 1, 30),
        }
        values.update(overrides)
        return LicenseGrant.objects.create(**values)

    def test_user_can_have_only_one_membership_record_per_parish(self):
        ParishMembership.objects.create(
            parish=self.parish,
            user=self.user,
            role=ParishMembership.Role.PASTOR,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ParishMembership.objects.create(
                parish=self.parish,
                user=self.user,
                role=ParishMembership.Role.ASSOCIATE,
            )

    def test_license_access_state_machine(self):
        grant = self.make_grant()

        self.assertEqual(evaluate_license(grant, date(2026, 6, 1)), LicenseAccess.FULL)
        self.assertEqual(evaluate_license(grant, date(2027, 1, 10)), LicenseAccess.FULL)
        self.assertEqual(evaluate_license(grant, date(2027, 2, 1)), LicenseAccess.READ_ONLY)

        grant.security_suspended = True
        self.assertEqual(evaluate_license(grant, date(2026, 6, 1)), LicenseAccess.DENIED)

        grant.security_suspended = False
        grant.status = LicenseGrant.Status.PENDING
        self.assertEqual(
            evaluate_license(grant, date(2026, 6, 1)),
            LicenseAccess.ONBOARDING_ONLY,
        )

    def test_same_person_cannot_record_and_verify_payment(self):
        payment = ManualPayment(
            parish=self.parish,
            amount='120.00',
            value_date=date(2026, 8, 3),
            payer_name='Župa A',
            recorded_by=self.user,
            verified_by=self.user,
            status=ManualPayment.Status.VERIFIED,
        )

        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_tenant_database_rejects_embedded_connection_string(self):
        tenant_database = TenantDatabase(
            parish=self.parish,
            alias='tenant-a',
            secret_ref='postgresql://user:password@example.test/database',
        )

        with self.assertRaises(ValidationError):
            tenant_database.full_clean()

    def test_control_plane_audit_event_is_immutable(self):
        event = ControlPlaneAuditEvent.objects.create(
            parish=self.parish,
            actor=self.user,
            event_type='test.event',
        )
        event.event_type = 'tampered.event'

        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()


class TenantContextIntegrationTests(TestCase):
    def setUp(self):
        self.parish_a = Parish.objects.create(
            slug='tenant-a',
            settings={'name': 'Župa A', 'shortName': 'A'},
            data={'tasks': [{'id': 'a-task'}]},
        )
        self.parish_b = Parish.objects.create(
            slug='tenant-b',
            settings={'name': 'Župa B', 'shortName': 'B'},
            data={'tasks': [{'id': 'b-task'}]},
        )
        self.user = User.objects.create_user(
            email='member@example.test',
            password='Tenant-Context-Test-938!',
            role='zupnik',
        )

    @override_settings(TENANCY_LEGACY_FALLBACK_ENABLED=False)
    def test_single_membership_selects_correct_parish_for_existing_frontend(self):
        ParishMembership.objects.create(
            parish=self.parish_b,
            user=self.user,
            role=ParishMembership.Role.ASSOCIATE,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('pastoral:app'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Župa B')
        self.assertContains(response, 'Župnik suradnik / vikar')
        self.assertEqual(
            self.client.session['active_tenant_id'],
            str(self.parish_b.tenant_id),
        )

    @override_settings(TENANCY_LEGACY_FALLBACK_ENABLED=False)
    def test_authenticated_user_without_membership_is_denied(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('pastoral:app'))

        self.assertEqual(response.status_code, 403)

    @override_settings(TENANCY_LEGACY_FALLBACK_ENABLED=False)
    def test_technical_admin_does_not_require_parish_membership(self):
        superuser = User.objects.create_superuser(
            email='platform-admin@example.test',
            password='Platform-Admin-Test-938!',
        )
        self.client.force_login(superuser)

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Licence i ručne uplate')

    def test_parish_data_service_uses_verified_context(self):
        context = TenantContext(
            tenant_id=self.parish_b.tenant_id,
            parish_pk=self.parish_b.pk,
            database_alias=None,
            membership_id=None,
            actor_id=self.user.id,
            role=ParishMembership.Role.PASTOR,
        )
        token = set_current_tenant_context(context)
        try:
            service = ParishDataService()
            data = service.load()
        finally:
            reset_current_tenant_context(token)

        self.assertEqual(service.parish, self.parish_b)
        self.assertEqual(data['tasks'][0]['id'], 'b-task')

