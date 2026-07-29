
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
    with FIXTURE_PATH.open(encoding='utf-8') as f:
        return json.load(f)


class ParishDataService:
    def __init__(self, parish: Parish | None = None):
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
        from pastoral.services.api_actions import normalize_data
        data = copy.deepcopy(self.parish.data or {})
        normalize_data(data)
        return data

    def save(self, data: dict) -> None:
        self.parish.data = data
        self.parish.save(update_fields=['data', 'updated_at'])

    def load_settings(self) -> dict:
        merged = {**DEFAULT_SETTINGS, **(self.parish.settings or {})}
        merged['_parishId'] = settings.PARISH_DEFAULT_SLUG
        return merged

    def save_settings(self, settings_dict: dict) -> None:
        self.parish.settings = {**settings_dict, '_parishId': settings.PARISH_DEFAULT_SLUG}
        self.parish.save(update_fields=['settings', 'updated_at'])

    def reset_demo(self) -> None:
        self.parish.data = _load_fixture()
        self.parish.settings = DEFAULT_SETTINGS.copy()
        self.parish.save()

    @staticmethod
    def today_iso() -> str:
        return date.today().isoformat()

    @staticmethod
    def add_days(n: int) -> str:
        return (date.today() + timedelta(days=n)).isoformat()

    def office_stats(self, data: dict | None = None) -> dict:
        data = data or self.load()
        today = self.today_iso()
        year = date.today().year
        intentions = data.get('intentions', [])
        tasks = data.get('tasks', [])
        families = data.get('families', [])
        lukno_unpaid = 0
        for fam in families:
            contribs = fam.get('contributions', [])
            row = next((c for c in contribs if c.get('year') == year), None)
            if row and not row.get('luknoPaid'):
                lukno_unpaid += 1
        overdue = sum(1 for t in tasks if not t.get('done') and (t.get('due') or '9999') < today)
        due_today = sum(1 for t in tasks if not t.get('done') and t.get('due') == today)
        unpaid_nakane = sum(1 for n in intentions if not n.get('paid'))
        nova_prijave = sum(1 for s in data.get('publicSubmissions', []) if s.get('status') == 'nova')
        reminders_count = len(self.collect_reminders(data))
        return {
            'unpaid_nakane': unpaid_nakane,
            'today_nakane': sum(1 for n in intentions if n.get('date') == today),
            'open_tasks': sum(1 for t in tasks if not t.get('done')),
            'overdue_tasks': overdue,
            'due_today_tasks': due_today,
            'lukno_unpaid': lukno_unpaid,
            'debts_unpaid': unpaid_nakane + lukno_unpaid + sum(
                1 for d in data.get('parishDebts', []) if not d.get('paid')
            ),
            'visits_due': sum(1 for v in data.get('visits', []) if not v.get('done')),
            'reminders_count': reminders_count,
            'nova_prijave': nova_prijave,
        }

    def collect_reminders(self, data: dict | None = None) -> list:
        from pastoral.services.reminders import collect_reminders
        data = data or self.load()
        return collect_reminders(data)
