from datetime import date

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from control_plane.models import ParishMembership
from pastoral.models import Parish
from pastoral.services.dashboard import calculate_parish_population_statistics
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
                    'members': [
                        {'id': 'm1', 'birthYear': 1985},
                        {'id': 'm2', 'birthYear': 2015},
                    ],
                },
                {
                    'id': 'f2',
                    'status': 'neaktivna',
                    'streetId': '',
                    'email': '',
                    'members': [{'id': 'm3', 'birthYear': 1950}],
                },
                {
                    'id': 'f3',
                    'status': 'aktivna',
                    'streetId': 's2',
                    'email': 'obitelj@example.test',
                    'members': [],
                },
            ],
        }

        population_statistics = calculate_parish_population_statistics(
            parish_data,
            reference_date=date(2026, 8, 5),
        )

        self.assertEqual(population_statistics['streets'], 2)
        self.assertEqual(population_statistics['households'], 3)
        self.assertEqual(population_statistics['active_households'], 2)
        self.assertEqual(population_statistics['persons'], 3)
        self.assertEqual(population_statistics['parishioners'], 2)
        self.assertEqual(population_statistics['deanery_parishes'], 3)
        self.assertEqual(population_statistics['households_with_contact'], 2)
        self.assertEqual(population_statistics['contact_coverage_percent'], 67)
        self.assertEqual(population_statistics['single_person_households'], 1)
        self.assertEqual(population_statistics['households_with_minors'], 1)
        self.assertEqual(population_statistics['households_without_minors'], 1)
        self.assertEqual(population_statistics['minors'], 1)
        self.assertEqual(population_statistics['households_without_street'], 1)
        self.assertEqual(population_statistics['empty_households'], 1)

    def test_unknown_birth_year_is_not_guessed_as_minor(self):
        population_statistics = calculate_parish_population_statistics({
            'families': [{
                'status': 'aktivna',
                'members': [{'name': 'Nepoznata dob', 'relation': 'sin'}],
            }],
        }, reference_date=date(2026, 8, 5))

        self.assertEqual(population_statistics['minors'], 0)
        self.assertEqual(population_statistics['households_with_minors'], 0)
        self.assertEqual(population_statistics['households_without_minors'], 1)


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
                'intentions': [],
                'massSchedule': [],
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
        self.assertContains(response, 'Osobe u sustavu')
        self.assertContains(response, 'Sastav kućanstava')
        self.assertNotContains(response, 'Spremnost dana')
        self.assertNotContains(response, 'Financijski puls')
