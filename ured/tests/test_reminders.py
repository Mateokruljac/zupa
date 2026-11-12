"""Regresijski testovi podsjetnika izvedenih iz obiteljskih uplata."""
from datetime import date
from unittest import TestCase
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from pastoral.templatetags.pastoral_tags import reminder_link
from pastoral.services.permissions import NAV
from pastoral.views import REMOVED_PAGE_REDIRECTS
from ured.services.reminders import collect_reminders
from ured.services.kalendar import calendar_page_context


class ContributionReminderTests(TestCase):
    def test_non_lukno_payment_does_not_create_lukno_reminder(self):
        reminders = collect_reminders({
            'families': [{
                'id': 'fam1',
                'status': 'neaktivna',
                'contributions': [{
                    'year': date.today().year,
                    'category': 'obiteljski_dar',
                    'luknoAmount': 100,
                    'luknoPaid': False,
                }],
            }],
        })

        self.assertNotIn('lukno', {item['category'] for item in reminders})


class ReminderLinkTests(SimpleTestCase):
    def test_family_fragment_is_appended_after_reversing_page_slug(self):
        self.assertEqual(
            reminder_link('obitelji#family=fam4'),
            f"{reverse('pastoral:page', kwargs={'page': 'obitelji'})}#family=fam4",
        )

    def test_query_string_and_fragment_are_both_preserved(self):
        self.assertEqual(
            reminder_link('obitelji?year=2026#family=fam4'),
            f"{reverse('pastoral:page', kwargs={'page': 'obitelji'})}?year=2026#family=fam4",
        )


class CalendarReminderMergeTests(SimpleTestCase):
    def test_calendar_context_exposes_reminder_view_and_task_link(self):
        request = RequestFactory().get('/pages/kalendar/', {'view': 'reminders'})
        with (
            patch('ured.services.kalendar.get_month_days', return_value={}),
            patch('ured.services.kalendar.get_day', return_value={}),
        ):
            context = calendar_page_context({
                'tasks': [{
                    'id': 'task1', 'title': 'Nazvati obitelj',
                    'due': date.today().isoformat(), 'done': False,
                }],
            }, request)

        self.assertEqual(context['calendar_view'], 'reminders')
        self.assertEqual(context['reminder_count'], 1)
        self.assertIn('view=tasks', context['reminders'][0]['href'])

    def test_sidebar_has_one_combined_calendar_entry(self):
        navigation_links = {
            item.get('page'): item.get('label')
            for item in NAV if item.get('type') == 'link'
        }

        self.assertNotIn('podsjetnici', navigation_links)
        self.assertEqual(navigation_links['kalendar'], 'Kalendar i obveze')
        self.assertEqual(REMOVED_PAGE_REDIRECTS['podsjetnici'], 'kalendar')
