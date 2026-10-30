"""Regresijski testovi filtera stranice javnih prijava."""
from datetime import date
from types import SimpleNamespace
from unittest import TestCase

from ured.services.public_submissions_page import public_submissions_context


class PublicSubmissionsContextTests(TestCase):
    """Neispravan query string ne smije srušiti administracijsku stranicu."""

    def test_invalid_import_year_falls_back_to_current_year(self):
        request = SimpleNamespace(GET={'year': 'nije-godina'})

        context = public_submissions_context(
            {'publicSubmissions': []},
            request,
        )

        self.assertEqual(context['import_year'], date.today().year)
