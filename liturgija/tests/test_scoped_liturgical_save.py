"""Regression: liturgical action bus persists via ORM (no blob replace save)."""
import os
import unittest
import uuid
from unittest.mock import MagicMock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zupa.settings.local')

import django

django.setup()

from pastoral.services.api_actions import dispatch_action  # noqa: E402


class DispatchOrmPersistTests(unittest.TestCase):
    def test_upsert_mass_schedule_does_not_call_save_liturgical(self):
        parish_data = {
            'intentions': [{'id': 'keep-me'}],
            'massSchedule': [],
            'massExceptions': [],
            'zupniListicIssues': [],
        }
        service = MagicMock()
        service.load.return_value = parish_data
        service.load_settings.return_value = {}
        slot_id = uuid.uuid4()
        slot = MagicMock(
            id=slot_id,
            day_label='Nedjelja',
            mass_time='10:00',
            weekdays=[],
            location='',
            notes='',
            valid_from=None,
            valid_until=None,
            no_mass=False,
        )

        with patch(
            'pastoral.services.api_actions.transaction.atomic',
            return_value=MagicMock(
                __enter__=MagicMock(return_value=None),
                __exit__=MagicMock(return_value=False),
            ),
        ), patch('liturgija.api_actions.MassScheduleSlot') as slot_model:
            slot_model.return_value = slot
            slot_model.objects.filter.return_value.first.return_value = None
            slot_model.objects.all.return_value = [slot]
            result = dispatch_action(
                'upsert_mass_schedule',
                {'fields': {'day': 'Nedjelja', 'time': '10:00'}},
                service,
            )

        self.assertTrue(result['ok'])
        service.save_liturgical.assert_not_called()
        self.assertEqual(result['data']['intentions'], [{'id': 'keep-me'}])
        self.assertTrue(result['dataPartial'])


if __name__ == '__main__':
    unittest.main()
