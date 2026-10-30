"""Regresijski testovi pohrane javnih prijava prije slanja obavijesti."""
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from pastoral.view_modules.public_forms import _store_public_submission


class PublicSubmissionStorageTests(TestCase):
    """Read-modify-write pohrana mora koristiti parish red kao mutex."""

    @patch('pastoral.view_modules.public_forms.transaction.atomic')
    def test_submission_is_stored_while_parish_row_is_locked(self, atomic):
        atomic.return_value.__enter__.return_value = None
        atomic.return_value.__exit__.return_value = False
        parish_data_service = MagicMock()
        parish_data = {'publicSubmissions': [{'id': 'existing'}]}
        parish_data_service.load.return_value = parish_data
        submission = {'id': 'new'}

        _store_public_submission(parish_data_service, submission)

        self.assertEqual(
            parish_data_service.method_calls,
            [call.lock_for_update(), call.load(), call.save(parish_data)],
        )
        self.assertEqual(
            parish_data['publicSubmissions'],
            [submission, {'id': 'existing'}],
        )
