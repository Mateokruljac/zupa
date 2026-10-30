"""Regresijski testovi podsjetnika izvedenih iz obiteljskih uplata."""
from datetime import date
from unittest import TestCase

from ured.services.reminders import collect_reminders


class ContributionReminderTests(TestCase):
    def test_non_lukno_payment_does_not_create_lukno_reminder(self):
        reminders = collect_reminders({
            'families': [{
                'id': 'fam1',
                'status': 'neaktivna',
                'contributions': [{
                    'year': date.today().year,
                    'category': 'obiteljski_dar',
                    'luknoAmount': 100,
                    'luknoPaid': False,
                }],
            }],
        })

        self.assertNotIn('lukno', {item['category'] for item in reminders})
