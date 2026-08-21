from datetime import date

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from control_plane.models import ParishMembership
from pastoral.models import Parish
from pastoral.services.dashboard import (
    _attach_todays_intentions_to_masses,
    calculate_parish_population_statistics,
)
from users.models import User


class ParishPopulationStatisticsTests(SimpleTestCase):
    def test_counts_only_explainable_population_metrics(self):
        parish_data = {
            'streets': [{'id': 's1'}, {'id': 's2'}],
            'parishDirectory': [{'id': 'p1'}, {'id': 'p2'}, {'id': 'p3'}],
            'families': [
                {
                    'id': 'f1',
                    'status': 'aktivna',
                    'streetId': 's1',
                    'phone': '091 111 222',
                    'createdAt': '2026-03-12',
                    'contributions': [
                        {'year': 2025, 'luknoPaid': False},
                        {'year': 2026, 'luknoPaid': True},
                    ],
                    'members': [
                        {'id': 'm1', 'birthYear': 1985, 'relation': 'majka'},
                        {'id': 'm2', 'birthYear': 2015, 'relation': 'kći'},
                    ],
                },
                {
                    'id': 'f2',
                    'status': 'neaktivna',
                    'streetId': '',
                    'email': '',
                    'createdAt': '2024-01-01',
                    'contributions': [
                        {'year': 2025, 'luknoPaid': False},
                    ],
                    'members': [{'id': 'm3', 'birthYear': 1950, 'relation': 'samac'}],
                },
                {
                    'id': 'f3',
                    'status': 'aktivna',
                    'streetId': 's2',
                    'email': 'obitelj@example.test',
                    'createdAt': '2025-11-01',
                    'contributions': [
                        {'year': 2025, 'luknoPaid': True},
                    ],
                    'members': [],
                },
                {
                    'id': 'f4',
                    'status': 'aktivna',
                    'streetId': 's1',
                    'phone': '091',
                    'members': [
                        {'relation': 'otac'},
                        {'relation': 'majka'},
                        {'relation': 'sin'},
                        {'relation': 'kći'},
                        {'relation': 'dijete'},
                        {'relation': 'sin'},
                    ],
                },
                {
                    'id': 'f5',
                    'status': 'aktivna',
                    'streetId': 's2',
                    'email': 'par@example.test',
                    'members': [
                        {'relation': 'suprug'},
                        {'relation': 'supruga'},
                    ],
                },
            ],
        }

        population_statistics = calculate_parish_population_statistics(
            parish_data,
            reference_date=date(2026, 8, 5),
        )

        self.assertEqual(population_statistics['streets'], 2)
        self.assertEqual(population_statistics['households'], 5)
        self.assertEqual(population_statistics['active_households'], 4)
        self.assertEqual(population_statistics['persons'], 11)
        self.assertEqual(population_statistics['parishioners'], 10)
        self.assertEqual(population_statistics['deanery_parishes'], 3)
        self.assertEqual(population_statistics['households_with_contact'], 4)
        self.assertEqual(population_statistics['contact_coverage_percent'], 80)
        self.assertEqual(population_statistics['single_person_households'], 1)
        self.assertEqual(population_statistics['households_without_children'], 1)
        self.assertEqual(population_statistics['households_with_one_child'], 1)
        self.assertEqual(population_statistics['households_with_two_children'], 0)
        self.assertEqual(population_statistics['households_with_three_children'], 0)
        self.assertEqual(population_statistics['households_with_more_children'], 1)
        self.assertEqual(population_statistics['households_without_street'], 1)
        self.assertEqual(population_statistics['empty_households'], 1)
        self.assertEqual(population_statistics['previous_year'], 2025)
        self.assertEqual(population_statistics['current_year'], 2026)
        self.assertEqual(population_statistics['previous_year_lukno_unpaid'], 1)
        self.assertEqual(population_statistics['households_added_this_year'], 1)
        self.assertNotIn('minors', population_statistics)
        self.assertNotIn('households_with_minors', population_statistics)

    def test_children_are_counted_by_relation_not_age(self):
        population_statistics = calculate_parish_population_statistics({
            'families': [{
                'status': 'aktivna',
                'members': [
                    {'name': 'Roditelj', 'relation': 'majka'},
                    {'name': 'Odraslo dijete', 'relation': 'sin', 'birthYear': 1990},
                ],
            }],
        }, reference_date=date(2026, 8, 5))

        self.assertEqual(population_statistics['households_with_one_child'], 1)
        self.assertEqual(population_statistics['households_without_children'], 0)

    def test_households_without_created_at_are_not_counted_as_new(self):
        population_statistics = calculate_parish_population_statistics({
            'families': [{
                'status': 'aktivna',
                'members': [],
            }],
        }, reference_date=date(2026, 8, 5))

        self.assertEqual(population_statistics['households_added_this_year'], 0)

    def test_attaches_intentions_to_matching_mass_times(self):
        todays_masses = [
            {'time': '07:30', 'location': 'Župna crkva'},
            {'time': '18:00', 'location': 'Župna crkva'},
        ]
        todays_intentions = [
            {'massTime': '07:30', 'intentionFor': 'Za zdravlje'},
            {'massTime': '07:30', 'intentionFor': 'Za pokojne'},
            {'massTime': '11:00', 'intentionFor': 'Bez mise u rasporedu'},
        ]

        _attach_todays_intentions_to_masses(todays_masses, todays_intentions)

        self.assertEqual(
            [intention['intentionFor'] for intention in todays_masses[0]['intentions']],
            ['Za zdravlje', 'Za pokojne'],
        )
        self.assertEqual(todays_masses[1]['intentions'], [])


@override_settings(TENANCY_LEGACY_FALLBACK_ENABLED=False)
class DashboardRenderTests(TestCase):
    def setUp(self):
        self.parish = Parish.objects.create(
            slug='dashboard-test',
            settings={
                'name': 'Župa za provjeru',
                'shortName': 'Testna župa',
                'city': 'Zagreb',
            },
            data={
                'streets': [{'id': 's1', 'name': 'Testna ulica'}],
                'families': [{
                    'id': 'f1',
                    'surname': 'Horvat',
                    'status': 'aktivna',
                    'streetId': 's1',
                    'phone': '091 111 222',
                    'members': [
                        {'id': 'm1', 'name': 'Ana', 'birthYear': 1985},
                        {'id': 'm2', 'name': 'Iva', 'birthYear': 2015},
                    ],
                }],
                'tasks': [],
                'intentions': [{
                    'id': 'i1',
                    'date': date.today().isoformat(),
                    'massTime': '07:30',
                    'intentionFor': 'Za zdravlje obitelji',
                    'requestedBy': 'Horvat',
                }],
                'massSchedule': [{
                    'id': 'ms1',
                    'time': '07:30',
                    'location': 'Župna crkva',
                    'weekdays': [0, 1, 2, 3, 4, 5, 6],
                }],
            },
        )
        self.user = User.objects.create_user(
            email='dashboard@example.test',
            password='Dashboard-Test-938!',
            role='zupnik',
        )
        ParishMembership.objects.create(
            parish=self.parish,
            user=self.user,
            role=ParishMembership.Role.PASTOR,
        )
        self.client.force_login(self.user)

    def test_dashboard_renders_useful_explainable_statistics(self):
        response = self.client.get(reverse('pastoral:app'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Osnovni pregled zajednice')
        self.assertContains(response, 'Župljani')
        self.assertContains(response, 'Lukno')
        self.assertContains(response, 'Nove obitelji')
        self.assertContains(response, 'Sastav kućanstava')
        self.assertContains(response, 'Samačka kućanstva')
        self.assertContains(response, 'Bez djece')
        self.assertContains(response, 'S više djece')
        self.assertContains(response, 'Za zdravlje obitelji')
        self.assertNotContains(response, 'Osobe u sustavu')
        self.assertNotContains(response, 'maloljet')
        self.assertNotContains(response, 'Spremnost dana')
        self.assertNotContains(response, 'Financijski puls')
        self.assertNotContains(response, 'Dnevna evidencija')
