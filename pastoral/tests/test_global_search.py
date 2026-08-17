from django.test import SimpleTestCase

from pastoral.services.global_search import global_search


class GlobalSearchTests(SimpleTestCase):
    def test_finds_household_without_changing_result_contract(self):
        parish_data = {
            'families': [{
                'id': 'family-1',
                'surname': 'Horvat',
                'address': 'Ilica 1',
                'phone': '091 111 222',
                'members': [{'name': 'Ana Horvat'}],
            }],
        }

        search_results = global_search(parish_data, 'ana', 1)

        self.assertEqual(search_results, [{
            'type': 'Obitelj',
            'label': 'Horvat',
            'sub': 'Ilica 1 · Ana Horvat',
            'href': 'obitelji?family=family-1',
        }])

    def test_ignores_search_query_shorter_than_two_characters(self):
        self.assertEqual(global_search({}, 'a'), [])
