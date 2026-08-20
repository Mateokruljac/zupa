from django.test import RequestFactory, SimpleTestCase

from pastoral.services.streets import streets_page_context


class StreetsPageContextTests(SimpleTestCase):
    def test_selected_street_includes_localized_map_urls(self):
        request = RequestFactory().get('/pages/ulice/', {'street': 'st1'})
        parish_data = {
            'streets': [{'id': 'st1', 'name': 'Vukovarska ulica'}],
            'families': [],
        }

        page_context = streets_page_context(
            parish_data,
            request,
            {'city': 'Slavonski Brod'},
        )

        self.assertEqual(
            page_context['street_map_query'],
            'Vukovarska ulica, Slavonski Brod, Hrvatska',
        )
        self.assertIn(
            'Vukovarska+ulica%2C+Slavonski+Brod%2C+Hrvatska',
            page_context['street_map_embed_url'],
        )
        self.assertIn(
            'Vukovarska+ulica%2C+Slavonski+Brod%2C+Hrvatska',
            page_context['street_map_external_url'],
        )

    def test_map_urls_are_empty_without_selected_street(self):
        request = RequestFactory().get('/pages/ulice/')

        page_context = streets_page_context(
            {'streets': [], 'families': []},
            request,
            {'city': 'Slavonski Brod'},
        )

        self.assertEqual(page_context['street_map_embed_url'], '')
        self.assertEqual(page_context['street_map_external_url'], '')
