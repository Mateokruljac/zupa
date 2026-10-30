"""Regresijski testovi provjere ovlasti na domenskim URL viewovima."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from pastoral.decorators import pastoral_login_required
from pastoral.domain_page_views import domain_page_view
from pastoral.services.permissions import can_access_page, role_permissions


class PagePermissionDecoratorTests(TestCase):
    """Slug stranice mora se provjeriti i kad je proslijeđen pozicijski."""

    @patch('pastoral.decorators.redirect', return_value='access-denied')
    @patch('pastoral.decorators.messages.error')
    def test_locked_page_passed_positionally_is_denied(self, _error, _redirect):
        @pastoral_login_required
        def protected_view(_request, page):
            return page

        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, role='upravitelj'),
            tenant_context=None,
            resolver_match=SimpleNamespace(url_name='blagajna'),
        )

        self.assertEqual(protected_view(request, 'blagajna'), 'access-denied')
        _redirect.assert_called_once_with('pastoral:app')

    @patch('pastoral.decorators.redirect', return_value='access-denied')
    @patch('pastoral.decorators.messages.error')
    def test_locked_domain_route_without_page_argument_is_denied(
        self,
        _error,
        _redirect,
    ):
        @pastoral_login_required
        def protected_view(_request):
            return 'sensitive-export'

        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, role='upravitelj'),
            tenant_context=None,
            resolver_match=SimpleNamespace(
                url_name='blagajna',
                kwargs={},
            ),
        )

        self.assertEqual(protected_view(request), 'access-denied')
        _redirect.assert_called_once_with('pastoral:app')


class DomainPageViewTests(TestCase):
    """Domenska fasada shared viewu predaje slug u provjerljivom obliku."""

    @patch('pastoral.views.admin_page_view', return_value='rendered')
    def test_page_slug_is_forwarded_as_keyword(self, admin_page_view):
        request = object()

        result = domain_page_view('blagajna')(request)

        self.assertEqual(result, 'rendered')
        admin_page_view.assert_called_once_with(request, page='blagajna')


class PermissionFallbackTests(TestCase):
    """Nepoznata uloga ili stranica ne smije dobiti župnikove ovlasti."""

    def test_unknown_role_has_no_modules(self):
        self.assertEqual(role_permissions('nepoznata-uloga'), [])
        self.assertFalse(can_access_page('blagajna', 'nepoznata-uloga'))

    def test_unknown_page_is_denied(self):
        self.assertFalse(can_access_page('nepoznata-stranica', 'zupnik'))
