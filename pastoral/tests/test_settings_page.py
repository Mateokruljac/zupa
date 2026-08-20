import json

from admin_interface.models import Theme
from django.test import TestCase, override_settings
from django.urls import reverse

from control_plane.models import ParishMembership
from pastoral.models import Parish
from users.models import User


@override_settings(TENANCY_LEGACY_FALLBACK_ENABLED=False)
class SettingsPageRenderTests(TestCase):
    def setUp(self):
        self.parish = Parish.objects.create(
            slug='settings-page-test',
            settings={
                'name': 'Župa za provjeru postavki',
                'shortName': 'Testne postavke',
                'city': 'Zagreb',
            },
            data={},
        )
        self.user = User.objects.create_user(
            email='settings-page@example.test',
            password='Settings-Page-Test-938!',
            role='zupnik',
        )
        ParishMembership.objects.create(
            parish=self.parish,
            user=self.user,
            role=ParishMembership.Role.PASTOR,
        )
        self.client.force_login(self.user)

    def test_renders_only_parish_settings_form(self):
        response = self.client.get(
            reverse('pastoral:page', kwargs={'page': 'postavke'}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Podaci o župi')
        self.assertContains(response, 'class="settings-page-layout"')
        self.assertContains(response, 'class="settings-form__grid"', count=3)
        self.assertContains(response, 'data-hide-context-strip="1"')
        self.assertNotContains(response, 'Kanonski okvir')
        self.assertNotContains(response, 'Demo podaci')
        self.assertNotContains(response, 'Operativni fokus ovog ekrana')

    def test_saving_frontend_palette_updates_active_admin_theme(self):
        response = self.client.post(
            reverse('pastoral:save_theme'),
            data=json.dumps({
                'primaryColor': '#2d5a45',
                'accentColor': '#b8922a',
                'themePresetId': 'custom',
                'customTheme': True,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        admin_theme = Theme.objects.get(active=True)
        self.assertEqual(
            admin_theme.title,
            'Pastoral — tehnička administracija',
        )
        self.assertFalse(admin_theme.logo_visible)
        self.assertFalse(admin_theme.language_chooser_active)
        self.assertEqual(admin_theme.css_header_background_color, '#2D5A45')
        self.assertEqual(admin_theme.css_module_background_color, '#2D5A45')
        self.assertEqual(admin_theme.title_color, '#B8922A')
