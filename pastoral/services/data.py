"""Orm-only ParishDataService — Parish.data više nije izvor istine."""

import copy
from datetime import date, timedelta

from django.conf import settings
from django.db import transaction

from pastoral.models import Parish
from pastoral.fixtures.demo_data import DEMO_PARISH_DATA

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
    'defaultMassIntentionStipend': 0,
}


def _load_fixture():
    return copy.deepcopy(DEMO_PARISH_DATA)


class ParishDataService:
    def __init__(self, parish: Parish | None = None):
        self.parish = parish or self.get_or_create_parish()

    @classmethod
    def for_request(cls, request) -> 'ParishDataService':
        """Koristi parish s requesta ako ga middleware/view već razriješi."""
        return cls(getattr(request, 'tenant', None) or getattr(request, 'parish', None))

    def lock_for_update(self) -> None:
        """Zaključaj tenant red unutar aktivne transakcije prije read-modify-writea."""
        self.parish = Parish.objects.select_for_update().get(pk=self.parish.pk)

    @classmethod
    def get_or_create_parish(cls) -> Parish:
        parish, created = Parish.objects.get_or_create(
            slug=settings.PARISH_DEFAULT_SLUG,
            defaults={'settings': DEFAULT_SETTINGS, 'data': {}},
        )
        if created or (
            not parish.data
            and not cls(parish)._has_operational_rows()
        ):
            from sakramenti.services.baptism_records import (
                reconcile_baptism_records,
            )

            existing_settings = copy.deepcopy(parish.settings or {})
            parish_data_service = cls(parish)
            baptism_records = parish_data_service.reset_demo()
            reconcile_baptism_records(parish, baptism_records)
            if not created and existing_settings:
                parish.settings = existing_settings
                parish.save(update_fields=['settings', 'updated_at'])
            return parish
        if not parish.settings:
            parish.settings = DEFAULT_SETTINGS.copy()
            parish.save(update_fields=['settings'])
        return parish

    def _has_operational_rows(self) -> bool:
        from zupa_vjernici.models import Household, Street
        return (
            Street.objects.filter(parish=self.parish).exists()
            or Household.objects.filter(parish=self.parish).exists()
            or bool(self.parish.data)
        )

    def load(self) -> dict:
        from pastoral.services.api_actions import normalize_parish_data
        from pastoral.services.operational_store import load_operational_collections
        from sakramenti.services.baptism_records import (
            relational_baptisms_as_legacy_dictionaries,
        )
        from sakramenti.services.formation_records import (
            relational_formation_programs_as_dictionaries,
        )
        from sakramenti.services.marriage_records import (
            relational_weddings_as_dictionaries,
        )
        from sakramenti.services.funeral_records import (
            relational_funerals_as_dictionaries,
        )
        from sakramenti.services.anointing_records import (
            relational_anointings_as_dictionaries,
        )
        from isprave.services.register_book_records import (
            relational_register_books_as_dictionaries,
        )
        from isprave.services.general_register_records import (
            relational_general_entries_as_dictionaries,
        )

        parish_data = load_operational_collections(self.parish)

        parish_data['baptisms'] = relational_baptisms_as_legacy_dictionaries(
            self.parish
        )
        parish_data.update(
            relational_formation_programs_as_dictionaries(self.parish)
        )
        parish_data['weddings'] = relational_weddings_as_dictionaries(
            self.parish
        )
        parish_data['funerals'] = relational_funerals_as_dictionaries(
            self.parish
        )
        parish_data['anointing'] = relational_anointings_as_dictionaries(
            self.parish
        )
        parish_data['registryBooks'] = relational_register_books_as_dictionaries(
            self.parish
        )
        parish_data['registryEntries'] = relational_general_entries_as_dictionaries(
            self.parish
        )
        normalize_parish_data(parish_data)
        return parish_data

    def save(self, parish_data: dict) -> None:
        from pastoral.services.operational_store import save_operational_collections
        from sakramenti.services.formation_records import (
            reconcile_formation_programs,
        )
        from sakramenti.services.marriage_records import reconcile_wedding_records
        from sakramenti.services.funeral_records import reconcile_funeral_records
        from sakramenti.services.anointing_records import reconcile_anointing_records
        from isprave.services.register_book_records import reconcile_register_books
        from isprave.services.general_register_records import (
            reconcile_general_register_entries,
        )

        with transaction.atomic():
            save_operational_collections(self.parish, parish_data)
            reconcile_formation_programs(self.parish, parish_data)
            reconcile_wedding_records(
                self.parish,
                list(parish_data.get('weddings') or []),
            )
            reconcile_funeral_records(
                self.parish,
                list(parish_data.get('funerals') or []),
            )
            reconcile_anointing_records(
                self.parish,
                list(parish_data.get('anointing') or []),
            )
            reconcile_register_books(
                self.parish,
                list(parish_data.get('registryBooks') or []),
            )
            reconcile_general_register_entries(
                self.parish,
                list(parish_data.get('registryEntries') or []),
            )
            # Parish.data više nije izvor istine.
            self.parish.data = {}
            self.parish.save(update_fields=['data', 'updated_at'])

    def save_liturgical(self, parish_data: dict) -> None:
        from pastoral.services.operational_store import (
            save_liturgical_collections,
        )

        save_liturgical_collections(self.parish, parish_data)

    def save_financial(self, parish_data: dict) -> None:
        from pastoral.services.operational_store import (
            save_financial_collections,
        )

        save_financial_collections(self.parish, parish_data)

    def load_settings(self) -> dict:
        merged = {**DEFAULT_SETTINGS, **(self.parish.settings or {})}
        merged['_parishId'] = self.parish.slug
        return merged

    def save_settings(self, parish_settings: dict) -> None:
        self.parish.settings = {**parish_settings, '_parishId': self.parish.slug}
        self.parish.save(update_fields=['settings', 'updated_at'])

    def reset_demo(self) -> list[dict]:
        from pastoral.services.operational_store import save_operational_collections
        from sakramenti.services.baptism_records import reconcile_baptism_records
        from sakramenti.services.formation_records import (
            reconcile_formation_programs,
        )
        from sakramenti.services.marriage_records import reconcile_wedding_records
        from sakramenti.services.funeral_records import reconcile_funeral_records
        from sakramenti.services.anointing_records import reconcile_anointing_records
        from isprave.services.register_book_records import reconcile_register_books
        from isprave.services.general_register_records import (
            reconcile_general_register_entries,
        )

        demo_data = _load_fixture()
        baptism_records = demo_data.pop('baptisms', [])
        formation_data = {
            'firstCommunion': demo_data.pop('firstCommunion', []),
            'confirmations': demo_data.pop('confirmations', []),
        }
        wedding_records = demo_data.pop('weddings', [])
        funeral_records = demo_data.pop('funerals', [])
        anointing_records = demo_data.pop('anointing', [])
        register_book_records = demo_data.pop('registryBooks', [])
        general_register_entries = demo_data.pop('registryEntries', [])
        with transaction.atomic():
            reconcile_formation_programs(self.parish, formation_data)
            reconcile_wedding_records(self.parish, wedding_records)
            reconcile_funeral_records(self.parish, funeral_records)
            reconcile_anointing_records(self.parish, anointing_records)
            reconcile_register_books(self.parish, register_book_records)
            reconcile_general_register_entries(
                self.parish,
                general_register_entries,
            )
            reconcile_baptism_records(self.parish, baptism_records)
            save_operational_collections(self.parish, demo_data)
            self.parish.data = {}
            self.parish.settings = DEFAULT_SETTINGS.copy()
            self.parish.save()
        return baptism_records

    @staticmethod
    def today_iso() -> str:
        return date.today().isoformat()

    @staticmethod
    def add_days(number_of_days: int) -> str:
        return (date.today() + timedelta(days=number_of_days)).isoformat()

    def office_statistics(self, parish_data: dict | None = None) -> dict:
        if parish_data is None:
            parish_data = self.load()
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
        from phase_two.module_registry import (
            INTERPARISH_COLLABORATION_MODULE,
            OPERATIONS_CENTER_MODULE,
        )

        interparish_pending = 0
        if INTERPARISH_COLLABORATION_MODULE.is_available:
            interparish_pending = sum(
                1
                for interparish_request in parish_data.get(
                    'interparishRequests',
                    [],
                )
                if interparish_request.get('targetParishId') == self.parish.slug
                and interparish_request.get('status')
                in {'received', 'needs_info'}
            )

        operations_attention = 0
        if OPERATIONS_CENTER_MODULE.is_available:
            try:
                from phase_two.operations_center.services import (
                    operations_attention_count,
                )
            except ModuleNotFoundError:
                operations_attention = 0
            else:
                operations_attention = operations_attention_count(parish_data)
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
            'operations_attention': operations_attention,
        }

    def collect_reminders(self, parish_data: dict | None = None) -> list:
        from ured.services.reminders import collect_reminders
        if parish_data is None:
            parish_data = self.load()
        return collect_reminders(parish_data)
