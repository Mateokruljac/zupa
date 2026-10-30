"""Regresijski testovi sastavljanja financijskih potraživanja."""
from unittest import TestCase

from financije.services.debts import collect_receivables


class ContributionReceivableTests(TestCase):
    def test_explicit_zero_lukno_does_not_become_default_debt(self):
        receivables = collect_receivables({
            'luknoDefaultAmount': 150,
            'families': [{
                'id': 'fam1',
                'contributions': [{
                    'year': 2026,
                    'category': 'lukno',
                    'luknoAmount': 0,
                    'luknoPaid': False,
                }],
            }],
        })

        self.assertEqual(receivables, [])
