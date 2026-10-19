"""Ulica ima naziv i grad, bez zone ili kvarta."""
import unittest
from datetime import date, datetime
from types import SimpleNamespace

from core.models import OPEN_ENDED_VALID_TO
from zupa_vjernici.forms import StreetForm
from zupa_vjernici.models import Street
from zupa_vjernici.services.api_action_handlers.streets import upsert_street
from zupa_vjernici.services.family_card import family_card_snapshot
from zupa_vjernici.services.membership_timeline import build_membership_timeline
from zupa_vjernici.services.street_records import (
    street_as_legacy_record,
    street_field_defaults_from_legacy,
)


class StreetCityTests(unittest.TestCase):
    def test_form_asks_for_street_and_city(self):
        form = StreetForm()
        self.assertEqual(form.fields['name'].label, 'Ulica')
        self.assertEqual(form.fields['city'].label, 'Grad')
        self.assertNotIn('zone', form.fields)

    def test_model_stores_city_instead_of_zone(self):
        field_names = {field.name for field in Street._meta.fields}
        self.assertIn('city', field_names)
        self.assertNotIn('zone', field_names)

    def test_legacy_record_uses_city(self):
        street = Street(
            public_identifier='st1',
            name='Ilica',
            city='Zagreb',
            sort_order=1,
        )
        record = street_as_legacy_record(street)
        self.assertEqual(record['city'], 'Zagreb')
        self.assertNotIn('zone', record)
        self.assertEqual(
            street_field_defaults_from_legacy(record)['city'],
            'Zagreb',
        )

    def test_upsert_stores_city(self):
        parish_data = {'streets': []}
        result = upsert_street(parish_data, {'name': 'Ilica', 'city': 'Zagreb'})
        self.assertTrue(result['ok'])
        self.assertEqual(result['item']['city'], 'Zagreb')
        self.assertNotIn('zone', result['item'])


class FamilyCardSnapshotTests(unittest.TestCase):
    def test_snapshot_describes_only_the_open_card(self):
        card = family_card_snapshot(
            {'streets': [{'id': 'st1', 'name': 'Ilica'}]},
            {
                'id': 'fam4',
                'surname': 'Babić',
                'streetId': 'st1',
                'address': '12',
                'phone': '',
                'email': 'ana@example.com',
                'status': 'aktivna',
                'pastoralNotes': 'Posjetiti',
                'members': [{
                    'id': 'm1',
                    'givenName': 'Ana',
                    'surname': 'Babić',
                    'name': 'Ana Babić',
                    'relation': 'supruga/majka',
                    'birthDate': '1980-05-02',
                    'birthYear': 1980,
                }],
                'contributions': [{
                    'year': 2025,
                    'category': 'lukno',
                    'luknoPaid': True,
                    'luknoAmount': 20,
                }],
            },
            2026,
        )
        self.assertEqual(card['streetName'], 'Ilica')
        self.assertEqual(card['dataGaps'], ['telefon'])
        self.assertEqual(card['luknoStatus'], 'none')
        self.assertEqual(card['members'][0]['birthYear'], '1980')
        self.assertEqual(card['pastoralNotes'], 'Posjetiti')

    def test_current_year_without_payment_is_unpaid(self):
        card = family_card_snapshot(
            {'streets': []},
            {
                'id': 'fam4',
                'phone': '091',
                'email': 'ana@example.com',
                'streetId': 'st1',
                'members': [],
                'contributions': [{
                    'year': 2026,
                    'category': 'lukno',
                    'luknoPaid': False,
                    'luknoAmount': 10,
                }],
            },
            2026,
        )
        self.assertEqual(card['luknoStatus'], 'unpaid')
        self.assertEqual(card['dataGaps'], [])

    def test_gift_category_does_not_count_as_lukno_status(self):
        card = family_card_snapshot(
            {'streets': []},
            {
                'id': 'fam5',
                'phone': '091',
                'email': 'ana@example.com',
                'streetId': 'st1',
                'members': [],
                'contributions': [{
                    'year': 2026,
                    'category': 'obiteljski_dar',
                    'luknoPaid': False,
                    'luknoAmount': 300,
                    'luknoPaidAt': '2026-01-05',
                }],
            },
            2026,
        )
        self.assertEqual(card['luknoStatus'], 'none')
        self.assertEqual(card['contributions'][0]['categoryLabel'], 'Obiteljski dar')


class MembershipTimelineTests(unittest.TestCase):
    def test_builds_join_relation_change_and_leave(self):
        versions = [
            SimpleNamespace(
                public_identifier='m1',
                historical_name='Ana Babić',
                role='dijete',
                date_from=date(2020, 1, 1),
                date_to=date(2023, 5, 31),
                created_at=datetime(2020, 1, 1),
            ),
            SimpleNamespace(
                public_identifier='m1',
                historical_name='Ana Babić',
                role='odselio',
                date_from=date(2023, 6, 1),
                date_to=date(2024, 12, 31),
                created_at=datetime(2023, 6, 1),
            ),
        ]
        events = build_membership_timeline(versions)
        types = [event['type'] for event in events]
        self.assertEqual(types, ['left', 'relation_changed', 'joined'])
        relation_event = events[1]
        self.assertEqual(relation_event['detail'], 'dijete → odselio')
        self.assertEqual(events[0]['at'], '2025-01-01')
