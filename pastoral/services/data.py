
import copy
import json
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings

from pastoral.models import Parish

FIXTURE_PATH = Path(__file__).resolve().parent.parent / 'fixtures' / 'demo_data.json'

DEFAULT_SETTINGS = {
    '_parishId': 'bdm-slavonski-brod',
    'name': 'Župa Blažene Djevice Marije',
    'shortName': 'Bl. Djevice Marije',
    'city': 'Slavonski Brod',
    'diocese': 'Đakovačko-osječka nadbiskupija',
    'pastor': 'vlč. Krunoslav Karas',
    'phone': '+385 35 000 000',
    'email': 'ured@zupa-bdm-sb.hr',
    'theme': {'primary': '#5c2e3a', 'accent': '#b8922a'},
    'primaryColor': '#5c2e3a',
    'accentColor': '#b8922a',
    'colorScheme': 'light',
}


def _load_fixture():
    with FIXTURE_PATH.open(encoding='utf-8') as fixture_file:
        return json.load(fixture_file)


class ParishDataService:
    def __init__(self, parish: Parish | None = None):
        if parish is None:
            from control_plane.tenant_context import get_current_tenant_context
            context = get_current_tenant_context()
            if context is not None:
                parish = Parish.objects.get(pk=context.parish_pk)
        self.parish = parish or self.get_or_create_parish()

    @classmethod
    def get_or_create_parish(cls) -> Parish:
        parish, created = Parish.objects.get_or_create(
            slug=settings.PARISH_DEFAULT_SLUG,
            defaults={'settings': DEFAULT_SETTINGS, 'data': _load_fixture()},
        )
        if created:
            return parish
        if not parish.data:
            parish.data = _load_fixture()
            parish.save(update_fields=['data'])
        if not parish.settings:
            parish.settings = DEFAULT_SETTINGS.copy()
            parish.save(update_fields=['settings'])
        return parish

    def load(self) -> dict:
        from pastoral.services.api_actions import normalize_parish_data
        parish_data = copy.deepcopy(self.parish.data or {})
        normalize_parish_data(parish_data)
        return parish_data

    def save(self, parish_data: dict) -> None:
        self.parish.data = parish_data
        self.parish.save(update_fields=['data', 'updated_at'])

    def load_settings(self) -> dict:
        merged = {**DEFAULT_SETTINGS, **(self.parish.settings or {})}
        merged['_parishId'] = self.parish.slug
        return merged

    def save_settings(self, parish_settings: dict) -> None:
        self.parish.settings = {**parish_settings, '_parishId': self.parish.slug}
        self.parish.save(update_fields=['settings', 'updated_at'])

    def reset_demo(self) -> None:
        self.parish.data = _load_fixture()
        self.parish.settings = DEFAULT_SETTINGS.copy()
        self.parish.save()

    @staticmethod
    def today_iso() -> str:
        return date.today().isoformat()

    @staticmethod
    def add_days(number_of_days: int) -> str:
        return (date.today() + timedelta(days=number_of_days)).isoformat()

    def office_statistics(self, parish_data: dict | None = None) -> dict:
        from pastoral.services.operations import operations_attention_count

        parish_data = parish_data or self.load()
        today = self.today_iso()
        current_year = date.today().year
        intentions = parish_data.get('intentions', [])
        tasks = parish_data.get('tasks', [])
        households = parish_data.get('families', [])
        unpaid_annual_contribution_count = 0
        for household in households:
            annual_contributions = household.get('contributions', [])
            current_year_contribution = next(
                (
                    contribution
                    for contribution in annual_contributions
                    if contribution.get('year') == current_year
                ),
                None,
            )
            if current_year_contribution and not current_year_contribution.get('luknoPaid'):
                unpaid_annual_contribution_count += 1
        overdue_task_count = sum(
            1
            for task in tasks
            if not task.get('done') and (task.get('due') or '9999') < today
        )
        tasks_due_today_count = sum(
            1
            for task in tasks
            if not task.get('done') and task.get('due') == today
        )
        unpaid_intention_count = sum(
            1 for intention in intentions if not intention.get('paid')
        )
        new_submission_count = sum(
            1
            for submission in parish_data.get('publicSubmissions', [])
            if submission.get('status') == 'nova'
        )
        reminder_count = len(self.collect_reminders(parish_data))
        interparish_pending = sum(
            1
            for interparish_request in parish_data.get('interparishRequests', [])
            if interparish_request.get('targetParishId') == self.parish.slug
            and interparish_request.get('status') in {'received', 'needs_info'}
        )
        return {
            'unpaid_nakane': unpaid_intention_count,
            'today_nakane': sum(
                1 for intention in intentions if intention.get('date') == today
            ),
            'open_tasks': sum(1 for task in tasks if not task.get('done')),
            'overdue_tasks': overdue_task_count,
            'due_today_tasks': tasks_due_today_count,
            'lukno_unpaid': unpaid_annual_contribution_count,
            'debts_unpaid': (
                unpaid_intention_count
                + unpaid_annual_contribution_count
                + sum(
                    1
                    for parish_debt in parish_data.get('parishDebts', [])
                    if not parish_debt.get('paid')
                )
            ),
            'visits_due': sum(
                1
                for pastoral_visit in parish_data.get('visits', [])
                if not pastoral_visit.get('done')
            ),
            'reminders_count': reminder_count,
            'nova_prijave': new_submission_count,
            'interparish_pending': interparish_pending,
            'operations_attention': operations_attention_count(parish_data),
        }

    def collect_reminders(self, parish_data: dict | None = None) -> list:
        from pastoral.services.reminders import collect_reminders
        parish_data = parish_data or self.load()
        return collect_reminders(parish_data)
