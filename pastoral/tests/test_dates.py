from datetime import date, datetime

from django.test import SimpleTestCase

from pastoral.services.dates import parse_iso_date


class ParseIsoDateTests(SimpleTestCase):
    def test_accepts_date_datetime_and_iso_datetime(self):
        expected = date(2026, 8, 3)

        self.assertEqual(parse_iso_date(expected), expected)
        self.assertEqual(parse_iso_date(datetime(2026, 8, 3, 14, 30)), expected)
        self.assertEqual(parse_iso_date('2026-08-03T14:30:00+02:00'), expected)

    def test_invalid_or_empty_values_return_none(self):
        self.assertIsNone(parse_iso_date(None))
        self.assertIsNone(parse_iso_date(''))
        self.assertIsNone(parse_iso_date('nije-datum'))
        self.assertIsNone(parse_iso_date(object()))
