"""Regression tests for HILP enrichment."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zupa.settings.local')

import django

django.setup()

from liturgija.services.liturgical import _enrich_with_hilp, get_day  # noqa: E402


class EnrichWithHilpTests(unittest.TestCase):
    def test_does_not_merge_readings(self):
        day = {
            'date': '2024-01-07',
            'empty': False,
            'readings': [],
            'hilpUrl': 'https://example.invalid/old',
        }
        hilp = {
            'readings': [{'label': 'Evanđelje', 'text': 'Tekst', 'reference': 'Mt 1'}],
            'gospelThought': 'Misao',
            'readingRefs': 'Mt 1',
            'liturgicalWeekHr': '1. tjedan',
            'psalterWeekHr': '1. tjedan psaltira',
            'hilpUrl': 'https://example.invalid/new',
        }
        with patch('liturgija.services.liturgical.fetch_hilp_day', return_value=hilp):
            result = _enrich_with_hilp(day)
        self.assertEqual(result['readings'], [])
        self.assertNotIn('readingsSource', result)
        self.assertEqual(result['gospelThought'], 'Misao')
        self.assertEqual(result['readingRefs'], 'Mt 1')
        self.assertEqual(result['seasonWeek'], '1. tjedan')
        self.assertEqual(result['psalterWeekHr'], '1. tjedan psaltira')
        self.assertEqual(result['hilpUrl'], 'https://example.invalid/new')

    def test_keeps_existing_readings(self):
        day = {
            'date': '2024-01-07',
            'empty': False,
            'readings': [{'label': 'Lokalno', 'value': 'Iz 1'}],
        }
        hilp = {
            'readings': [{'label': 'HILP', 'reference': 'Mt 1'}],
            'readingRefs': 'Mt 1',
        }
        with patch('liturgija.services.liturgical.fetch_hilp_day', return_value=hilp):
            result = _enrich_with_hilp(day)
        self.assertEqual(result['readings'][0]['label'], 'Lokalno')
        self.assertNotIn('readingRefs', result)

    def test_network_miss_returns_original(self):
        day = {'date': '2024-01-07', 'empty': False, 'title': 'Sv. Ivan'}
        with patch('liturgija.services.liturgical.fetch_hilp_day', return_value=None):
            result = _enrich_with_hilp(day)
        self.assertEqual(result, day)


class GetDayTests(unittest.TestCase):
    def test_empty_day_skips_hilp(self):
        empty = {'date': '2024-01-07', 'empty': True, 'title': 'Nema unosa'}
        with patch(
            'liturgija.services.liturgical.stored_calendar_day',
            return_value=empty,
        ), patch('liturgija.services.liturgical.fetch_hilp_day') as fetch:
            result = get_day('2024-01-07')
        fetch.assert_not_called()
        self.assertEqual(result, empty)


if __name__ == '__main__':
    unittest.main()
