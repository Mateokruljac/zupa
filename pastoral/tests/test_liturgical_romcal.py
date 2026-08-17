import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from pastoral.api_views import liturgical_v1_day_api
from pastoral.services.liturgical import (
    LiturgicalService,
    map_litcal_day,
    merge_liturgical_days,
)
from pastoral.services.liturgical_audit import audit_liturgical_days
from pastoral.services.liturgical_romcal import (
    RomcalLiturgicalService,
    compare_liturgical_days,
)


class RomcalLiturgicalServiceTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = RomcalLiturgicalService()
        cls.days_2026 = cls.service.get_year_days(2026)

    def test_generates_complete_leap_safe_year(self):
        self.assertEqual(len(self.days_2026), 365)
        self.assertEqual(self.days_2026['2026-01-01']['calendar'], 'croatia')

    def test_easter_is_local_and_mapped_to_existing_schema(self):
        easter = self.days_2026['2026-04-05']

        self.assertEqual(easter['source'], 'romcal')
        self.assertEqual(easter['eventId'], 'easter_sunday')
        self.assertEqual(easter['title'], 'Uskrsna nedjelja')
        self.assertEqual(easter['color'], 'white')
        self.assertEqual(easter['sundayCycle'], 'A')
        self.assertEqual(easter['readings'], [])

    def test_croatian_proper_calendar_is_used(self):
        kazotic = self.days_2026['2026-08-03']

        self.assertEqual(kazotic['eventId'], 'augustine_kazotic_bishop')
        self.assertEqual(kazotic['calendarScope'], 'croatia')
        self.assertIn('Augustin Kažotić', kazotic['title'])
        self.assertEqual(len(kazotic['observances']), 2)
        by_id = {item['eventId']: item for item in kazotic['observances']}
        self.assertEqual(by_id['augustine_kazotic_bishop']['color'], 'red')
        self.assertTrue(by_id['augustine_kazotic_bishop']['primary'])
        self.assertEqual(by_id['ordinary_time_18_monday']['color'], 'green')
        self.assertFalse(by_id['ordinary_time_18_monday']['primary'])

    def test_corpus_christi_uses_croatian_thursday_date(self):
        day = self.days_2026['2026-06-04']

        self.assertEqual(day['eventId'], 'most_holy_body_and_blood_of_christ')

    def test_common_latin_titles_are_presented_with_offline_croatian_terms(self):
        maximilian_kolbe = self.days_2026['2026-08-14']
        ordinary_sunday = self.days_2026['2026-08-16']

        self.assertIn('prezbitera i mučenika', maximilian_kolbe['title'])
        self.assertEqual(ordinary_sunday['title'], '20. nedjelja kroz godinu')

    @override_settings(
        LITURGICAL_PRIMARY_PROVIDER='romcal',
        LITURGICAL_ROMCAL_ENABLED=True,
    )
    @patch('pastoral.services.liturgical_romcal.RomcalLiturgicalService.get_day')
    def test_feature_flag_can_make_romcal_primary(self, get_day):
        get_day.return_value = {'source': 'romcal', 'date': '2026-04-05'}

        result = LiturgicalService().get_day('2026-04-05', with_hilp=False)

        self.assertEqual(result['source'], 'romcal')
        get_day.assert_called_once_with('2026-04-05')

    def test_comparison_reports_only_changed_fields(self):
        comparison = compare_liturgical_days(
            {'date': '2026-04-05', 'title': 'Uskrs', 'color': 'white'},
            {'date': '2026-04-05', 'title': 'Uskrsna nedjelja', 'color': 'white'},
        )

        self.assertFalse(comparison['matches'])
        self.assertEqual(set(comparison['differences']), {'title'})

    def test_hybrid_keeps_croatian_celebration_and_litcal_temporal_day(self):
        hybrid = merge_liturgical_days(
            {
                'source': 'romcal',
                'calendar': 'croatia',
                'eventId': 'augustine_kazotic_bishop',
                'title': 'Blaženi Augustin Kažotić, biskup i mučenik',
                'subtitle': 'Vrijeme kroz godinu',
                'celebrations': ['Ponedjeljak 18. tjedna vremena kroz godinu'],
                'readings': [],
            },
            {
                'source': 'litcal-va',
                'calendar': 'VA',
                'title': 'Ponedjeljak 18. tjedna običnog vremena',
                'readings': [{'label': 'Evanđelje', 'text': 'Mt 1, 1'}],
            },
        )

        self.assertEqual(hybrid['source'], 'romcal+litcal-va')
        self.assertIn('Augustin Kažotić', hybrid['title'])
        self.assertEqual(
            hybrid['temporalTitle'],
            'Ponedjeljak 18. tjedna vremena kroz godinu',
        )
        self.assertEqual(hybrid['readingsSource'], 'litcal-va')
        self.assertEqual(hybrid['sources']['celebration'], 'romcal/croatia')
        self.assertEqual(hybrid['celebrations'], [])

    @patch('pastoral.services.liturgical.translate_reading_ref')
    @patch('pastoral.services.liturgical_deep.translate_to_hr')
    def test_litcal_mapping_never_waits_for_remote_translation(
        self,
        remote_name_translation,
        remote_reading_translation,
    ):
        mapped_day = map_litcal_day(
            '2026-08-14',
            [{
                'date': '2026-08-14',
                'name': 'Nomen Latinum Ignotum',
                'liturgical_season_lcl': 'Tempus Ignotum',
                'readings': {'gospel': 'Lectio Ignota 1:1'},
                'grade': 2,
            }],
        )

        self.assertEqual(mapped_day['title'], 'Nomen Latinum Ignotum')
        self.assertEqual(mapped_day['readings'][0]['text'], 'Lectio Ignota 1:1')
        remote_name_translation.assert_not_called()
        remote_reading_translation.assert_not_called()

    @override_settings(
        LITURGICAL_PRIMARY_PROVIDER='hybrid',
        LITURGICAL_ROMCAL_ENABLED=True,
    )
    @patch('pastoral.services.liturgical.LiturgicalService._get_day_litcal')
    @patch('pastoral.services.liturgical_romcal.RomcalLiturgicalService.get_day')
    def test_hybrid_provider_calls_both_sources(self, romcal_day, litcal_day):
        romcal_day.return_value = {
            'source': 'romcal', 'date': '2026-08-03', 'title': 'Kažotić',
        }
        litcal_day.return_value = {
            'source': 'litcal-va', 'date': '2026-08-03', 'title': '18. tjedan',
        }

        result = LiturgicalService().get_day('2026-08-03', with_hilp=False)

        self.assertEqual(result['source'], 'romcal+litcal-va')
        romcal_day.assert_called_once_with('2026-08-03')
        litcal_day.assert_called_once_with('2026-08-03')

    @patch('pastoral.api_views.LiturgicalService.get_day')
    def test_v1_api_has_stable_envelope(self, get_day):
        get_day.return_value = {
            'source': 'romcal+litcal-va',
            'date': '2026-08-03',
            'observances': [
                {'title': 'Kažotić', 'color': 'red'},
                {'title': 'Svagdan', 'color': 'green'},
            ],
        }
        request = RequestFactory().get('/api/liturgical/v1/day/2026-08-03/')
        request.user = SimpleNamespace(is_authenticated=True)

        response = liturgical_v1_day_api(request, '2026-08-03')
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['schemaVersion'], '1.0')
        self.assertEqual(payload['provider'], 'romcal+litcal-va')
        self.assertEqual(len(payload['data']['observances']), 2)

    def test_audit_finds_multiple_observances_and_color_difference(self):
        report = audit_liturgical_days(
            {
                '2026-08-03': {
                    'title': 'Kažotić',
                    'color': 'red',
                    'rankLabel': 'Izborni spomen',
                    'translated': True,
                    'observances': [
                        {'title': 'Kažotić', 'colorLabel': 'Crvena', 'primary': True, 'translated': True},
                        {'title': 'Svagdan', 'colorLabel': 'Zelena', 'primary': False, 'translated': True},
                    ],
                },
            },
            {
                '2026-08-03': {
                    'source': 'litcal-va',
                    'title': 'Svagdan',
                    'color': 'green',
                    'rankLabel': 'Radni dan',
                },
            },
        )

        self.assertEqual(report['daysChecked'], 1)
        self.assertEqual(report['summary']['multipleObservances'], 1)
        self.assertEqual(report['summary']['sourceDifferences'], 1)
        self.assertEqual(report['sourceDifferences'][0]['differences']['color'], {
            'romcal': 'red', 'litcal': 'green',
        })
