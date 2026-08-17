from django.test import SimpleTestCase

from pastoral.services.api_actions import (
    create_family,
    create_intention,
    delete_street,
    normalize_parish_data,
    toggle_intention_paid,
    upsert_family_member,
    upsert_street,
)


class SharedApiActionHelpersTests(SimpleTestCase):
    def test_normalizes_family_contributions_and_parishioners(self):
        parish_data = {
            'families': [{
                'id': 'family-1',
                'surname': 'Horvat',
                'status': 'aktivna',
                'phone': '091 111 222',
                'contributions': None,
                'members': [{'id': 'member-1', 'name': 'Ana Horvat'}],
            }],
        }

        normalized_parish_data = normalize_parish_data(parish_data)

        self.assertIs(normalized_parish_data, parish_data)
        self.assertEqual(len(parish_data['families'][0]['contributions']), 3)
        self.assertEqual(parish_data['parishioners'][0]['name'], 'Ana Horvat')
        self.assertEqual(parish_data['parishioners'][0]['family'], 'Horvat')


class IntentionApiActionsTests(SimpleTestCase):
    def test_creates_and_marks_intention_paid(self):
        parish_data = {'intentions': []}

        creation_result = create_intention(parish_data, {
            'date': '2026-08-14',
            'mass_time': '18:30',
            'intention_for': 'Pokojni Ivan',
            'requested_by': 'Obitelj Horvat',
            'stipend': '10',
        })
        intention_record = creation_result['item']
        payment_result = toggle_intention_paid(
            parish_data,
            {'id': intention_record['id']},
        )

        self.assertTrue(creation_result['ok'])
        self.assertEqual(intention_record['massTime'], '18:30')
        self.assertEqual(intention_record['intentionFor'], 'Pokojni Ivan')
        self.assertTrue(payment_result['item']['paid'])
        self.assertTrue(payment_result['item']['paymentId'].startswith('PAY-'))


class FamilyApiActionsTests(SimpleTestCase):
    def test_creates_family_and_synchronizes_new_member(self):
        parish_data = {'families': []}

        family_result = create_family(parish_data, {
            'surname': 'Kovač',
            'street_id': 'street-1',
            'address': 'Testna 1',
        })
        family = family_result['item']
        member_result = upsert_family_member(parish_data, {
            'family_id': family['id'],
            'name': 'Iva Kovač',
            'relation': 'kći',
            'birth_year': 2014,
        })

        self.assertTrue(family_result['ok'])
        self.assertTrue(member_result['ok'])
        self.assertEqual(family['streetId'], 'street-1')
        self.assertEqual(parish_data['parishioners'][0]['name'], 'Iva Kovač')
        self.assertEqual(parish_data['parishioners'][0]['family'], 'Kovač')


class StreetApiActionsTests(SimpleTestCase):
    def test_creates_updates_and_deletes_street(self):
        parish_data = {'streets': []}

        creation_result = upsert_street(parish_data, {
            'name': 'Ilica',
            'zone': 'Centar',
        })
        street = creation_result['item']
        update_result = upsert_street(parish_data, {
            'id': street['id'],
            'name': 'Ilica',
            'zone': 'Zapad',
        })
        deletion_result = delete_street(parish_data, {'id': street['id']})

        self.assertTrue(creation_result['ok'])
        self.assertEqual(update_result['item']['zone'], 'Zapad')
        self.assertTrue(deletion_result['ok'])
        self.assertEqual(parish_data['streets'], [])
