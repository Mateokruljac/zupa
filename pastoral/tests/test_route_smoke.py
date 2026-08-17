from django.test import TestCase
from django.urls import reverse


class ActiveRouteSmokeTests(TestCase):
    def test_root_redirects_to_login(self):
        response = self.client.get(reverse('pastoral:index'))

        self.assertRedirects(response, reverse('pastoral:login'))

    def test_login_page_renders(self):
        response = self.client.get(reverse('pastoral:login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prijava')

    def test_app_requires_login(self):
        response = self.client.get(reverse('pastoral:app'))

        self.assertRedirects(
            response,
            f"{reverse('pastoral:login')}?next={reverse('pastoral:app')}",
        )

    def test_legacy_login_url_redirects_to_active_login(self):
        response = self.client.get('/login.html')

        self.assertRedirects(response, reverse('pastoral:login'))
