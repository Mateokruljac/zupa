"""Regression tests for mass-schedule / listić API action handlers."""
import os
import unittest
import uuid
from unittest.mock import MagicMock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zupa.settings.local')

import django

django.setup()

from liturgija.api_actions import (  # noqa: E402
    delete_listic_issue,
    delete_mass_schedule,
    upsert_listic_issue,
    upsert_mass_schedule,
)


def _slot_mock(slot_id, *, day='Nedjelja', time='10:00'):
    slot = MagicMock()
    slot.id = slot_id
    slot.day_label = day
    slot.mass_time = time
    slot.weekdays = []
    slot.location = ''
    slot.notes = ''
    slot.valid_from = None
    slot.valid_until = None
    slot.no_mass = False
    return slot


class MassScheduleActionTests(unittest.TestCase):
    @patch('liturgija.api_actions.MassScheduleSlot')
    def test_upsert_and_delete_mass_schedule(self, slot_model):
        slot_id = uuid.uuid4()
        slot = _slot_mock(slot_id)
        slot_model.return_value = slot
        slot_model.objects.filter.return_value.first.return_value = None
        slot_model.objects.all.return_value = [slot]

        data = {'massSchedule': []}
        created = upsert_mass_schedule(
            data,
            {'fields': {'day': 'Nedjelja', 'time': '10:00'}},
        )
        self.assertTrue(created['ok'])
        self.assertEqual(created['item']['id'], str(slot_id))
        self.assertEqual(len(data['massSchedule']), 1)

        slot_model.objects.filter.return_value.first.return_value = slot
        slot.mass_time = '11:00'
        updated = upsert_mass_schedule(
            data,
            {'id': str(slot_id), 'fields': {'day': 'Nedjelja', 'time': '11:00'}},
        )
        self.assertTrue(updated['ok'])
        self.assertEqual(data['massSchedule'][0]['time'], '11:00')

        slot_model.objects.filter.return_value.first.return_value = None
        missing = upsert_mass_schedule(
            data,
            {'id': str(uuid.uuid4()), 'fields': {'time': '12:00'}},
        )
        self.assertEqual(missing, {'ok': False, 'error': 'not_found'})

        slot_model.objects.all.return_value = []
        deleted = delete_mass_schedule(data, {'id': str(slot_id)})
        self.assertTrue(deleted['ok'])
        self.assertEqual(data['massSchedule'], [])


class ListicActionTests(unittest.TestCase):
    @patch('liturgija.api_actions.BulletinIssue')
    def test_upsert_updates_existing_and_delete_removes(self, issue_model):
        issue_id = uuid.uuid4()
        issue_obj = MagicMock()
        issue_obj.id = issue_id
        issue_obj.week_start = __import__('datetime').date(2024, 1, 1)
        issue_obj.week_end = __import__('datetime').date(2024, 1, 7)
        issue_obj.title = 'Listić 1'
        issue_obj.status = 'izdan'
        issue_obj.layout = {}
        issue_obj.rendered_html = '<p>x</p>'
        issue_obj.created_at = None
        issue_obj.updated_at = None

        prepared = {
            'id': str(issue_id),
            'weekStart': '2024-01-01',
            'weekEnd': '2024-01-07',
            'title': 'Listić 1',
            'status': 'izdan',
            'layoutSnapshot': {'blocks': []},
            'renderedHtml': '<p>x</p>',
        }
        data = {'zupniListicIssues': [], 'intentions': [], 'massSchedule': []}

        with patch(
            'liturgija.services.zupni_listic.prepare_issue',
            return_value=prepared,
        ):
            issue_model.objects.filter.return_value.first.return_value = None
            issue_model.return_value = issue_obj
            issue_model.objects.all.return_value = [issue_obj]
            created = upsert_listic_issue(data, prepared, settings={})
            self.assertTrue(created['ok'])
            self.assertEqual(data['zupniListicIssues'][0]['id'], str(issue_id))

            issue_model.objects.filter.return_value.first.return_value = issue_obj
            issue_obj.title = 'Listić 1b'
            prepared['title'] = 'Listić 1b'
            updated = upsert_listic_issue(data, prepared, settings={})
            self.assertTrue(updated['ok'])
            self.assertEqual(len(data['zupniListicIssues']), 1)
            self.assertEqual(data['zupniListicIssues'][0]['title'], 'Listić 1b')

            issue_model.objects.all.return_value = []
            deleted = delete_listic_issue(data, {'id': str(issue_id)})
            self.assertTrue(deleted['ok'])
            self.assertEqual(data['zupniListicIssues'], [])


if __name__ == '__main__':
    unittest.main()
