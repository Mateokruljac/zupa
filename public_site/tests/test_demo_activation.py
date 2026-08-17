from datetime import date, timedelta
from io import BytesIO
import tempfile
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from control_plane.models import LicenseEntitlement, LicenseGrant, ParishMembership
from pastoral.models import Parish
from public_site.models import (
    ParishWebsite, ParishWebsiteMedia, PublicContentPublication, WebsiteBuild,
)
from public_site.snapshots import content_source_key
from public_site.services import (
    activate_public_website,
    complete_demo_build,
    delete_website_media,
    publish_demo_website,
    reset_demo_website,
    update_content_publication,
)


@override_settings(PUBLIC_WEBSITE_DEMO_AUTO_ACTIVATE=True)
class PublicWebsiteDemoActivationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='demo-web@example.test',
            password='test-password',
        )
        self.parish = Parish.objects.create(
            slug='demo-web-zupa',
            settings={'name': 'Župa sv. Testa'},
        )
        self.grant = LicenseGrant.objects.create(
            parish=self.parish,
            license_code=uuid.uuid4(),
            status=LicenseGrant.Status.ACTIVE,
            valid_from=date(2026, 1, 1),
            valid_until=date(2027, 12, 31),
            grace_until=date(2028, 1, 31),
            approved_by=self.user,
        )
        ParishMembership.objects.create(
            parish=self.parish,
            user=self.user,
            role=ParishMembership.Role.PASTOR,
        )

    def test_activation_enables_entitlement_and_starts_build(self):
        website, build = activate_public_website(parish=self.parish, actor=self.user)

        self.assertEqual(website.status, ParishWebsite.Status.PROVISIONING)
        self.assertEqual(build.status, WebsiteBuild.Status.RUNNING)
        self.assertEqual(build.progress, 35)
        self.assertTrue(LicenseEntitlement.objects.get(
            grant=self.grant,
            code='public_website',
        ).enabled)

    def test_demo_can_complete_and_publish(self):
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        website.refresh_from_db()
        self.assertEqual(website.status, ParishWebsite.Status.DRAFT)

        publish_demo_website(website=website, actor=self.user)
        website.refresh_from_db()
        self.assertEqual(website.status, ParishWebsite.Status.LIVE)
        self.assertIsNotNone(website.published_at)

        response = self.client.get(f'/zupa/{website.subdomain}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Raspored svetih misa')
        self.assertContains(response, 'Javni obrasci')
        self.assertContains(response, 'Život u slikama')
        self.assertContains(response, 'marija-hero.webp')
        self.assertContains(response, 'marija-vitraj.webp')

    def test_each_template_choice_is_exposed_as_a_distinct_public_variant(self):
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        publish_demo_website(website=website, actor=self.user)

        for template_key in (
            ParishWebsite.Template.CLASSIC,
            ParishWebsite.Template.WARM,
            ParishWebsite.Template.MODERN,
        ):
            with self.subTest(template_key=template_key):
                website.template_key = template_key
                website.save(update_fields=('template_key', 'updated_at'))
                publish_demo_website(website=website, actor=self.user)
                response = self.client.get(f'/zupa/{website.subdomain}/')
                self.assertContains(response, f'class="template-{template_key}"')
                self.assertContains(response, f'data-template="{template_key}"')

    def test_public_site_exposes_accessible_visitor_theme_control(self):
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        publish_demo_website(website=website, actor=self.user)

        response = self.client.get(f'/zupa/{website.subdomain}/')

        self.assertContains(response, 'public_site/js/theme.js')
        self.assertContains(response, 'data-theme-toggle')
        self.assertContains(response, 'Tema: Sustav. Promijeni temu.')

    def test_saved_draft_configuration_does_not_replace_published_site(self):
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        website.template_key = ParishWebsite.Template.CLASSIC
        website.site_name = 'Objavljeni naziv'
        publish_demo_website(website=website, actor=self.user)

        website.template_key = ParishWebsite.Template.MODERN
        website.site_name = 'Naziv u skici'
        website.publication_status = ParishWebsite.PublicationStatus.DRAFT
        website.save(update_fields=('template_key', 'site_name', 'publication_status', 'updated_at'))

        public_response = self.client.get(f'/zupa/{website.subdomain}/')
        self.assertContains(public_response, 'Objavljeni naziv')
        self.assertContains(public_response, 'template-classic')
        self.assertNotContains(public_response, 'Naziv u skici')

        self.client.force_login(self.user)
        preview_response = self.client.get(f'/zupa/{website.subdomain}/pregled/')
        self.assertContains(preview_response, 'Naziv u skici')
        self.assertContains(preview_response, 'template-modern')
        self.assertContains(preview_response, 'Pregled prije objave')

    def test_draft_and_scheduled_content_are_filtered_from_public_site(self):
        announcement = {
            'id': 'announcement-workflow',
            'title': 'Kontrolirana obavijest',
            'body': 'Sadržaj pod kontrolom objave',
            'at': '2026-08-03',
        }
        event = {
            'id': 'event-workflow',
            'title': 'Zakazano događanje',
            'date': '2026-08-10',
            'place': 'Dvorana',
        }
        self.parish.data = {'announcements': [announcement], 'events': [event]}
        self.parish.save(update_fields=('data',))
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        publish_demo_website(website=website, actor=self.user)
        update_content_publication(
            website=website,
            actor=self.user,
            kind=PublicContentPublication.Kind.ANNOUNCEMENT,
            source_key=content_source_key('announcement', announcement),
            source_label=announcement['title'],
            status=PublicContentPublication.Status.DRAFT,
        )
        update_content_publication(
            website=website,
            actor=self.user,
            kind=PublicContentPublication.Kind.EVENT,
            source_key=content_source_key('event', event),
            source_label=event['title'],
            status=PublicContentPublication.Status.SCHEDULED,
            scheduled_for=timezone.now() + timedelta(days=1),
        )

        public_response = self.client.get(f'/zupa/{website.subdomain}/')
        self.assertNotContains(public_response, announcement['title'])
        self.assertNotContains(public_response, event['title'])

        self.client.force_login(self.user)
        preview_response = self.client.get(f'/zupa/{website.subdomain}/pregled/')
        self.assertContains(preview_response, announcement['title'])
        self.assertContains(preview_response, event['title'])
        self.assertContains(preview_response, 'Skica')
        self.assertContains(preview_response, 'Zakazano')

    def test_preview_is_hidden_from_user_outside_parish(self):
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        other = get_user_model().objects.create_user(
            email='other-parish@example.test', password='test-password',
        )
        self.client.force_login(other)

        response = self.client.get(f'/zupa/{website.subdomain}/pregled/')

        self.assertEqual(response.status_code, 404)

    def test_frontend_activation_button_starts_production(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['active_tenant_id'] = str(self.parish.tenant_id)
        session.save()

        response = self.client.post('/pages/web-stranica/', {
            'action': 'activate_public_website',
        })

        self.assertRedirects(response, '/pages/web-stranica/')
        website = ParishWebsite.objects.get(parish=self.parish)
        self.assertEqual(website.status, ParishWebsite.Status.PROVISIONING)
        self.assertTrue(website.builds.filter(
            status=WebsiteBuild.Status.RUNNING,
            progress=35,
        ).exists())

    def test_demo_can_be_reset_for_next_presentation(self):
        activate_public_website(parish=self.parish, actor=self.user)

        reset_demo_website(parish=self.parish, actor=self.user)

        self.assertFalse(ParishWebsite.objects.filter(parish=self.parish).exists())
        self.assertFalse(LicenseEntitlement.objects.filter(
            grant=self.grant,
            code='public_website',
        ).exists())

    def test_public_snapshot_exposes_only_public_content(self):
        self.parish.data = {
            'massSchedule': [{
                'id': 'm1', 'day': 'Nedjelja', 'weekdays': [0],
                'time': '09:00', 'location': 'Župna crkva',
            }],
            'announcements': [
                {'title': 'Javna obavijest', 'body': 'Vidljivi sadržaj', 'at': '2026-08-03'},
                {'title': 'Interna obavijest', 'body': 'Ne smije biti vidljivo', 'public': False},
            ],
            'events': [
                {'title': 'Javni susret', 'date': '2026-08-10', 'place': 'Dvorana'},
                {'title': 'Privatni sastanak', 'date': '2026-08-11', 'type': 'privatno'},
            ],
            'families': [{'surname': 'Tajna obitelj'}],
        }
        self.parish.save(update_fields=('data',))
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        publish_demo_website(website=website, actor=self.user)

        response = self.client.get(f'/zupa/{website.subdomain}/')

        self.assertContains(response, 'Javna obavijest')
        self.assertContains(response, 'Javni susret')
        self.assertContains(response, '09:00')
        self.assertNotContains(response, 'Interna obavijest')
        self.assertNotContains(response, 'Privatni sastanak')
        self.assertNotContains(response, 'Tajna obitelj')

    def test_tenant_scoped_public_form_is_available(self):
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        publish_demo_website(website=website, actor=self.user)

        response = self.client.get(
            f'/zupa/{website.subdomain}/obrasci/prijava-krsenje/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prijava za krštenje')
        self.assertContains(response, 'Župa sv. Testa')

    def test_frontend_upload_optimizes_and_publishes_gallery_image(self):
        website, _ = activate_public_website(parish=self.parish, actor=self.user)
        complete_demo_build(website=website, actor=self.user)
        publish_demo_website(website=website, actor=self.user)
        self.client.force_login(self.user)
        session = self.client.session
        session['active_tenant_id'] = str(self.parish.tenant_id)
        session.save()

        source = BytesIO()
        Image.new('RGB', (1200, 800), '#5c6f91').save(source, 'JPEG', quality=95)
        upload = SimpleUploadedFile('procesija.jpg', source.getvalue(), content_type='image/jpeg')

        with tempfile.TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            response = self.client.post('/pages/web-stranica/', {
                'action': 'upload_website_media',
                'media_kind': 'gallery',
                'gallery-image': upload,
                'gallery-alt_text': 'Procesija ispred župne crkve',
                'gallery-caption': 'Župna procesija',
            })

            self.assertEqual(response.status_code, 302, response.content.decode(errors='replace'))
            self.assertEqual(response.url, '/pages/web-stranica/')
            media = ParishWebsiteMedia.objects.get(website=website)
            self.assertTrue(media.image.name.endswith('.webp'))
            self.assertEqual((media.width, media.height), (1200, 800))
            self.assertLess(media.file_size, 8 * 1024 * 1024)

            public_response = self.client.get(f'/zupa/{website.subdomain}/')
            self.assertContains(public_response, 'Župna procesija')
            self.assertContains(public_response, media.image.url)

            stored_name = media.image.name
            storage = media.image.storage
            with self.captureOnCommitCallbacks(execute=True):
                self.assertTrue(delete_website_media(
                    website=website,
                    actor=self.user,
                    media_id=media.pk,
                ))
            self.assertFalse(storage.exists(stored_name))
