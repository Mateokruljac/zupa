"""Ulica ima naziv i grad, bez zone ili kvarta."""
import unittest

from zupa_vjernici.forms import StreetForm
from zupa_vjernici.models import Street
from zupa_vjernici.services.api_action_handlers.streets import upsert_street
from zupa_vjernici.services.family_card import family_card_snapshot
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
                    'luknoPaid': False,
                    'luknoAmount': 10,
                }],
            },
            2026,
        )
        self.assertEqual(card['luknoStatus'], 'unpaid')
        self.assertEqual(card['dataGaps'], ['teritorijalna pripadnost'])
