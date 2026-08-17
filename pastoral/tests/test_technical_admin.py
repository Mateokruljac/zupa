from django.contrib import admin
import json
from unittest.mock import patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from pastoral.models import (
    LiturgicalCalendarEntry,
    LiturgicalCalendarImport,
    OtpChallenge,
    Parish,
)
from pastoral.services.liturgical import _load_events
from users.admin import AdminUserCreationForm
from users.models import User


class TechnicalAdminTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email='technical-admin@example.test',
            password='Admin-Test-Password-938!',
        )
        self.pastoral_user = User.objects.create_user(
            email='pastoral-user@example.test',
            password='Pastoral-Test-Password-938!',
            role='zupnik',
        )

    def test_superuser_sees_reordered_technical_admin(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Župe i podatkovna jezgra')
        self.assertContains(response, 'Korisnici i ovlasti')
        self.assertContains(response, 'Sigurnost prijave')
        self.assertContains(response, 'Liturgijski kalendar')
        self.assertContains(response, 'Otvori Pastoral')

    def test_non_staff_user_cannot_enter_django_admin(self):
        self.client.force_login(self.pastoral_user)

        response = self.client.get(reverse('admin:index'))

        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('admin:index')}",
        )

    def test_only_staff_user_sees_technical_admin_link_in_pastoral(self):
        self.client.force_login(self.pastoral_user)
        response = self.client.get(reverse('pastoral:app'))
        self.assertNotContains(response, 'Tehnička administracija')

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('pastoral:app'))
        self.assertContains(response, 'Tehnička administracija')
        self.assertContains(response, reverse('admin:index'))

    def test_council_admin_page_renders_management_forms(self):
        self.client.force_login(self.pastoral_user)

        response = self.client.get(
            reverse('pastoral:page', kwargs={'page': 'vijeca'}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dodaj člana vijeća')
        self.assertContains(response, 'name="action" value="add_council_member"')
        self.assertContains(
            response,
            'name="action" value="schedule_council_meeting"',
        )

    def test_record_pages_render_missing_management_forms(self):
        self.client.force_login(self.pastoral_user)
        expected_action_by_page = {
            'obitelji': 'add_family',
            'krizma': 'add_confirmation_candidate',
            'prva-pricest': 'add_first_communion_candidate',
        }

        for page_slug, action_name in expected_action_by_page.items():
            with self.subTest(page=page_slug):
                response = self.client.get(
                    reverse('pastoral:page', kwargs={'page': page_slug}),
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    f'name="action" value="{action_name}"',
                )

    def test_otp_secret_is_not_rendered_in_admin(self):
        challenge = OtpChallenge.objects.create(
            email='otp@example.test',
            code='918273',
            role='zupnik',
        )
        self.client.force_login(self.superuser)

        changelist = self.client.get(reverse('admin:pastoral_otpchallenge_changelist'))
        detail = self.client.get(
            reverse('admin:pastoral_otpchallenge_change', args=(challenge.pk,)),
        )

        self.assertEqual(changelist.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertNotContains(changelist, challenge.code)
        self.assertNotContains(detail, challenge.code)

    def test_parish_cannot_be_deleted_from_admin(self):
        parish = Parish.objects.create(slug='admin-test')
        request = RequestFactory().get('/admin/pastoral/parish/')
        request.user = self.superuser

        model_admin = admin.site._registry[Parish]

        self.assertFalse(model_admin.has_delete_permission(request, parish))

    def test_admin_creation_form_hashes_password(self):
        form = AdminUserCreationForm(data={
            'email': 'new-staff@example.test',
            'name': 'Novi administrator',
            'role': 'zupnik',
            'password1': 'Another-Test-Password-592!',
            'password2': 'Another-Test-Password-592!',
            'is_active': True,
            'is_staff': True,
        })

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.check_password('Another-Test-Password-592!'))
        self.assertNotEqual(user.password, 'Another-Test-Password-592!')

    def test_admin_imports_valid_liturgical_calendar_file(self):
        self.client.force_login(self.superuser)
        calendar_file = SimpleUploadedFile(
            'litcal-2026.json',
            json.dumps({
                'litcal': [
                    {
                        'date': '2026-08-15',
                        'name': 'Assumption of the Blessed Virgin Mary',
                        'color': ['white'],
                        'grade': 6,
                        'event_key': 'Assumption',
                    },
                    {
                        'date': '2026-08-15',
                        'name': 'Saint Example',
                        'color': ['red'],
                        'grade': 2,
                        'event_key': 'SaintExample',
                    },
                ],
            }).encode('utf-8'),
            content_type='application/json',
        )

        response = self.client.post(
            reverse('admin:pastoral_liturgicalcalendarimport_add'),
            {
                'year': '2026',
                'provider': LiturgicalCalendarImport.Provider.LITCAL_VATICAN,
                'calendar_file': calendar_file,
            },
        )

        self.assertEqual(response.status_code, 302)
        calendar_import = LiturgicalCalendarImport.objects.get(year=2026)
        self.assertEqual(calendar_import.event_count, 2)
        self.assertEqual(calendar_import.source_file_name, 'litcal-2026.json')
        self.assertEqual(calendar_import.imported_by, self.superuser)
        self.assertEqual(len(calendar_import.checksum), 64)
        calendar_entries = LiturgicalCalendarEntry.objects.filter(
            calendar_import=calendar_import,
        )
        self.assertEqual(calendar_entries.count(), 2)
        primary_entry = calendar_entries.get(is_primary=True)
        self.assertEqual(primary_entry.date.isoformat(), '2026-08-15')
        self.assertEqual(primary_entry.priority, 6)
        self.assertEqual(
            primary_entry.liturgical_color,
            LiturgicalCalendarEntry.LiturgicalColor.WHITE,
        )

    def test_server_uses_admin_import_before_remote_calendar(self):
        imported_events = [
            {'date': '2032-01-01', 'name': 'Uvezeni blagdan', 'grade': 6},
        ]
        LiturgicalCalendarImport.objects.create(
            year=2032,
            provider=LiturgicalCalendarImport.Provider.LITCAL_VATICAN,
            events=imported_events,
            event_count=1,
        )
        cache.delete('litcal_va_raw_2032')

        with patch('pastoral.services.liturgical.urllib.request.urlopen') as remote_request:
            loaded_events = _load_events(2032)

        self.assertEqual(loaded_events, imported_events)
        remote_request.assert_not_called()

    def test_server_uses_bundled_calendar_before_remote_calendar(self):
        cache_key = 'litcal_va_raw_2026'
        cache.delete(cache_key)
        self.addCleanup(cache.delete, cache_key)

        with patch('pastoral.services.liturgical.urllib.request.urlopen') as remote_request:
            loaded_events = _load_events(2026)

        self.assertTrue(loaded_events)
        remote_request.assert_not_called()
