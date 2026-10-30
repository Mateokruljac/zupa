"""Regresijski testovi zajedničkog legacy UI → ORM ugovora."""
from datetime import date
from decimal import Decimal
from unittest import TestCase

from core.utils import (
    _decimal_amount,
    _iso_or_empty,
    _parse_iso_date,
    decimal_amount,
    iso_or_empty,
    parse_iso_date,
)


class LegacyValueConversionTests(TestCase):
    """Potvrđuje tolerantna pravila koja koriste svi domenski adapteri."""

    def test_parse_iso_date_accepts_date_prefix_and_rejects_invalid_value(self):
        self.assertEqual(
            parse_iso_date('2026-10-28T08:30:00+01:00'),
            date(2026, 10, 28),
        )
        self.assertIsNone(parse_iso_date('nije-datum'))
        self.assertIsNone(parse_iso_date(''))

    def test_iso_or_empty_preserves_legacy_empty_string_contract(self):
        self.assertEqual(iso_or_empty(date(2026, 10, 28)), '2026-10-28')
        self.assertEqual(iso_or_empty(None), '')

    def test_decimal_amount_preserves_tolerant_zero_fallback(self):
        self.assertEqual(decimal_amount('12.50'), Decimal('12.50'))
        self.assertEqual(decimal_amount('nije-broj'), Decimal('0'))

    def test_legacy_and_public_import_names_share_the_same_contract(self):
        self.assertIs(_decimal_amount, decimal_amount)
        self.assertIs(_parse_iso_date, parse_iso_date)
        self.assertIs(_iso_or_empty, iso_or_empty)
