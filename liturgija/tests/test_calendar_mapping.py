"""Regression tests for calendar day mapping and catalog localization."""
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zupa.settings.local')

import django

django.setup()

from liturgija.services.liturgical_day_catalog import localize_celebration  # noqa: E402
from liturgija.services.liturgical_imports import (  # noqa: E402
    _localized_event,
    _map_stored_calendar_day,
)


class LocalizeCelebrationTests(unittest.TestCase):
    def test_empty_name(self):
        self.assertEqual(localize_celebration(''), ('', '', False))

    def test_unknown_latin_kept(self):
        name, color, found = localize_celebration('CompletelyUnknownCelebrationXYZ')
        self.assertEqual(name, 'CompletelyUnknownCelebrationXYZ')
        self.assertEqual(color, '')
        self.assertFalse(found)


class LocalizedEventTests(unittest.TestCase):
    def test_falls_back_to_source_color(self):
        name, original, color, found = _localized_event({
            'title': 'UnknownLatinTitleXYZ',
            'date': '2024-01-01',
            'color': ['green'],
            'grade': 0,
        })
        self.assertEqual(original, 'UnknownLatinTitleXYZ')
        self.assertEqual(name, 'UnknownLatinTitleXYZ')
        self.assertEqual(color, 'green')
        self.assertFalse(found)


class MapStoredCalendarDayTests(unittest.TestCase):
    def test_empty_day_shape(self):
        day = _map_stored_calendar_day('2024-01-07', [])
        self.assertTrue(day['empty'])
        self.assertEqual(day['title'], 'Nema unosa')
        self.assertEqual(day['date'], '2024-01-07')
        self.assertIn('hilpUrl', day)

    def test_primary_and_secondary_observances(self):
        primary = SimpleNamespace(
            id=1,
            name='Nedjelja',
            priority=5,
            priority_label='Nedjelja',
            liturgical_color='green',
            is_primary=True,
            readings=[{'label': 'Evanđelje', 'value': 'Mt 1,1-10'}],
        )
        secondary = SimpleNamespace(
            id=2,
            name='Sv. Ivan',
            priority=2,
            priority_label='Spomen',
            liturgical_color='white',
            is_primary=False,
            readings=[],
        )
        day = _map_stored_calendar_day('2024-01-07', [primary, secondary])
        self.assertFalse(day['empty'])
        self.assertEqual(day['title'], 'Nedjelja')
        self.assertEqual(day['color'], 'green')
        self.assertEqual(len(day['observances']), 2)
        self.assertEqual(day['celebrations'], ['Sv. Ivan'])
        self.assertTrue(day['observances'][0]['primary'])
        self.assertFalse(day['observances'][1]['primary'])
        self.assertEqual(day['readings'], [{'label': 'Evanđelje', 'value': 'Mt 1,1-10'}])


if __name__ == '__main__':
    unittest.main()
