from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from pastoral.services.kalendar import calendar_page_context


class CalendarPageContextTests(SimpleTestCase):
    @patch('pastoral.services.kalendar.LiturgicalService')
    def test_preserves_calendar_context_contract_and_conflict_detection(
        self,
        liturgical_service_class,
    ):
        liturgical_service = liturgical_service_class.return_value
        liturgical_service.get_month_days.return_value = {
            '2026-08-15': {'title': 'Uznesenje Blažene Djevice Marije'},
        }
        liturgical_service.get_day.return_value = {
            'title': 'Uznesenje Blažene Djevice Marije',
        }
        request = RequestFactory().get(
            '/app/kalendar/',
            {'year': '2026', 'month': '8', 'date': '2026-08-15'},
        )
        parish_data = {
            'events': [
                {
                    'id': 'event-1',
                    'date': '2026-08-15',
                    'time': '10:00',
                    'place': 'Crkva',
                },
                {
                    'id': 'event-2',
                    'date': '2026-08-15',
                    'time': '10:00',
                    'place': 'crkva',
                },
            ],
            'tasks': [
                {
                    'id': 'task-done',
                    'due': '2026-08-14',
                    'priority': 'visoka',
                    'done': True,
                },
                {
                    'id': 'task-open',
                    'due': '2026-08-15',
                    'priority': 'srednja',
                    'done': False,
                },
            ],
        }

        context = calendar_page_context(parish_data, request)

        self.assertEqual(context['cal_year'], 2026)
        self.assertEqual(context['cal_month'], 8)
        self.assertEqual(context['cal_prev'], {'year': 2026, 'month': 7})
        self.assertEqual(context['cal_next'], {'year': 2026, 'month': 9})
        self.assertEqual(len(context['cal_cells']), 42)
        self.assertEqual(context['filter_date'], '2026-08-15')
        self.assertEqual(len(context['day_events']), 2)
        self.assertEqual([task['id'] for task in context['day_tasks']], ['task-open'])
        self.assertEqual(
            context['calendar_counts']['2026-08-15'],
            {'events': 2, 'tasks': 1},
        )
        self.assertEqual(len(context['calendar_conflicts']), 1)
        self.assertEqual(
            [task['id'] for task in context['tasks']],
            ['task-open', 'task-done'],
        )

    @patch('pastoral.services.kalendar.LiturgicalService')
    def test_invalid_month_is_clamped_without_changing_default_date(
        self,
        liturgical_service_class,
    ):
        liturgical_service_class.return_value.get_month_days.return_value = {}
        liturgical_service_class.return_value.get_day.return_value = {}
        request = RequestFactory().get(
            '/app/kalendar/',
            {'year': 'not-a-year', 'month': '99', 'date': 'today'},
        )

        context = calendar_page_context({}, request)

        self.assertEqual(context['cal_month'], 12)
        self.assertRegex(context['filter_date'], r'^\d{4}-\d{2}-\d{2}$')
