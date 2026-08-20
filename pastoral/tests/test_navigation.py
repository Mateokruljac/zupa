from django.test import SimpleTestCase

from pastoral.services.permissions import can_access_page, filter_nav


class SidebarNavigationTests(SimpleTestCase):
    def test_visits_page_is_accessible_from_sidebar(self):
        navigation_items = filter_nav(role='zupnik', current_page='dashboard')
        navigation_pages = [
            navigation_item.get('page')
            for navigation_item in navigation_items
            if navigation_item['type'] == 'link'
        ]

        self.assertIn('posjete', navigation_pages)
        self.assertTrue(can_access_page(page='posjete', role='zupnik'))
