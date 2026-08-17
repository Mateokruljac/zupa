from django.test import TestCase

from pastoral.services.documents import load_templates, render_template
from users.models import User


class DocumentPrintingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='document-print@example.test',
            password='Document-Print-Test-938!',
            role='zupnik',
        )

    def test_every_catalog_template_renders_inside_standard_a4_shell(self):
        self.client.force_login(self.user)

        for template in load_templates():
            with self.subTest(template=template['id']):
                payload = {
                    'action': 'print_document',
                    'template_id': template['id'],
                    **{f'field_{field}': f'Vrijednost {field}' for field in template.get('fields', [])},
                }
                response = self.client.post('/pages/formulari/', payload)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'css/print-document.css')
                self.assertContains(response, 'class="print-sheet"')
                self.assertContains(response, 'class="document-letterhead"')
                self.assertContains(response, 'class="document-footer"')
                self.assertContains(response, f'data-document-template="{template["id"]}"')

    def test_all_catalog_templates_resolve_placeholders(self):
        for template in load_templates():
            values = {field: f'Vrijednost {field}' for field in template.get('fields', [])}

            rendered = render_template(template['id'], values)

            self.assertNotIn('{{', rendered, template['id'])
            self.assertNotIn('}}', rendered, template['id'])
