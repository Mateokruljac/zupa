"""Projektna CLI provjera liturgijskog dana, inspirirana catholic-cli alatom."""
from __future__ import annotations

import json
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings

from pastoral.services.liturgical import LiturgicalService


class Command(BaseCommand):
    help = 'Prikaži hrvatski liturgijski dan iz hibridnog, Romcal ili LitCal izvora.'

    def add_arguments(self, parser):
        parser.add_argument('date', nargs='?', help='Datum u obliku YYYY-MM-DD (zadano: danas)')
        parser.add_argument(
            '--provider',
            choices=('hybrid', 'romcal', 'litcal'),
            default='hybrid',
            help='Izvor podataka (zadano: hybrid)',
        )
        parser.add_argument('--json', action='store_true', help='Ispiši puni JSON rezultat')
        parser.add_argument(
            '--with-hilp',
            action='store_true',
            help='Dohvati i HILP čitanja; može zahtijevati mrežu',
        )

    def handle(self, *args, **options):
        raw_date = options['date'] or date.today().isoformat()
        try:
            iso = date.fromisoformat(raw_date).isoformat()
        except ValueError as exc:
            raise CommandError('Datum mora biti valjani YYYY-MM-DD.') from exc

        with override_settings(
            LITURGICAL_PRIMARY_PROVIDER=options['provider'],
            LITURGICAL_ROMCAL_ENABLED=True,
        ):
            day = LiturgicalService().get_day(iso, with_hilp=options['with_hilp'])

        if options['json']:
            self.stdout.write(json.dumps(day, ensure_ascii=False, indent=2))
            return

        self.stdout.write(self.style.SUCCESS(f'{iso} — {day.get("title", "—")}'))
        if day.get('temporalTitle'):
            self.stdout.write(f'Liturgijsko vrijeme: {day["temporalTitle"]}')
        self.stdout.write(
            ' · '.join(filter(None, (
                day.get('rankLabel'), day.get('colorLabel'), day.get('subtitle'),
            )))
        )
        observances = day.get('observances') or []
        if len(observances) > 1:
            self.stdout.write('Slavlja dana:')
            for item in observances:
                marker = '*' if item.get('primary') else '-'
                self.stdout.write(
                    f'  {marker} {item.get("title")} — '
                    f'{item.get("rankLabel")}, {item.get("colorLabel")}'
                )
