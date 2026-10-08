"""Regression tests for liturgija mass-schedule resolution (no DB)."""
import unittest

from liturgija.services.mass_schedule import (
    format_mass_schedule_html,
    get_masses_for_date,
    has_scheduled_mass,
)


class GetMassesForDateTests(unittest.TestCase):
    def test_weekday_match_from_weekdays_list(self):
        # 2024-01-07 was a Sunday (JS dow 0).
        data = {
            'massSchedule': [
                {'id': 'ms1', 'day': 'Nedjelja', 'time': '10:00', 'weekdays': [0]},
                {'id': 'ms2', 'day': 'Pon–Pet', 'time': '07:30', 'weekdays': [1, 2, 3, 4, 5]},
            ],
            'massExceptions': [],
        }
        slots = get_masses_for_date(data, '2024-01-07')
        self.assertEqual([s['time'] for s in slots], ['10:00'])

    def test_weekday_fallback_from_day_label(self):
        data = {
            'massSchedule': [
                {'id': 'ms1', 'day': 'Nedjelja', 'time': '11:00'},
            ],
            'massExceptions': [],
        }
        slots = get_masses_for_date(data, '2024-01-07')
        self.assertEqual([s['time'] for s in slots], ['11:00'])

    def test_validity_window(self):
        data = {
            'massSchedule': [
                {
                    'id': 'ms1',
                    'day': 'Nedjelja',
                    'time': '10:00',
                    'weekdays': [0],
                    'validFrom': '2024-02-01',
                    'validUntil': '2024-02-29',
                },
            ],
            'massExceptions': [],
        }
        self.assertEqual(get_masses_for_date(data, '2024-01-07'), [])
        self.assertEqual(
            [s['time'] for s in get_masses_for_date(data, '2024-02-04')],
            ['10:00'],
        )
        self.assertEqual(get_masses_for_date(data, '2024-03-03'), [])

    def test_no_mass_period_clears_day(self):
        data = {
            'massSchedule': [
                {'id': 'ms1', 'day': 'Nedjelja', 'time': '10:00', 'weekdays': [0]},
                {
                    'id': 'ms2',
                    'day': 'Nedjelja',
                    'weekdays': [0],
                    'noMass': True,
                    'validFrom': '2024-01-01',
                    'validUntil': '2024-01-31',
                },
            ],
            'massExceptions': [],
        }
        self.assertEqual(get_masses_for_date(data, '2024-01-07'), [])

    def test_cancel_all_exception(self):
        data = {
            'massSchedule': [
                {'id': 'ms1', 'day': 'Nedjelja', 'time': '10:00', 'weekdays': [0]},
            ],
            'massExceptions': [
                {'date': '2024-01-07', 'cancelAll': True},
            ],
        }
        self.assertEqual(get_masses_for_date(data, '2024-01-07'), [])

    def test_cancel_times_exception(self):
        data = {
            'massSchedule': [
                {'id': 'ms1', 'day': 'Nedjelja', 'time': '07:30', 'weekdays': [0]},
                {'id': 'ms2', 'day': 'Nedjelja', 'time': '10:00', 'weekdays': [0]},
            ],
            'massExceptions': [
                {'date': '2024-01-07', 'cancelTimes': ['07:30']},
            ],
        }
        self.assertEqual(
            [s['time'] for s in get_masses_for_date(data, '2024-01-07')],
            ['10:00'],
        )

    def test_slots_sorted_by_time(self):
        data = {
            'massSchedule': [
                {'id': 'ms2', 'day': 'Nedjelja', 'time': '18:00', 'weekdays': [0]},
                {'id': 'ms1', 'day': 'Nedjelja', 'time': '07:30', 'weekdays': [0]},
            ],
            'massExceptions': [],
        }
        self.assertEqual(
            [s['time'] for s in get_masses_for_date(data, '2024-01-07')],
            ['07:30', '18:00'],
        )


class HasScheduledMassTests(unittest.TestCase):
    def test_true_when_slot_exists(self):
        data = {
            'massSchedule': [
                {'id': 'ms1', 'day': 'Nedjelja', 'time': '10:00', 'weekdays': [0]},
            ],
            'massExceptions': [],
        }
        self.assertTrue(has_scheduled_mass(data, '2024-01-07', '10:00'))
        self.assertFalse(has_scheduled_mass(data, '2024-01-07', '11:00'))

    def test_invalid_date_is_false(self):
        self.assertFalse(has_scheduled_mass({'massSchedule': []}, 'not-a-date', '10:00'))


class FormatMassScheduleHtmlTests(unittest.TestCase):
    def test_empty_schedule_message(self):
        html = format_mass_schedule_html({'massSchedule': []})
        self.assertIn('nije unesen', html)

    def test_renders_day_and_time(self):
        html = format_mass_schedule_html({
            'massSchedule': [
                {'day': 'Nedjelja', 'time': '10:00'},
            ],
        })
        self.assertIn('Nedjelja', html)
        self.assertIn('10:00', html)


if __name__ == '__main__':
    unittest.main()
