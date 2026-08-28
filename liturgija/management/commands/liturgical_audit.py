"""Projektna naredba za usporedbu liturgijskih izvora."""
from __future__ import annotations

import calendar
import json
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from liturgija.services.liturgical import LiturgicalService
from liturgija.services.liturgical_audit import audit_liturgical_days
from liturgija.services.liturgical_romcal import RomcalLiturgicalService


class Command(BaseCommand):
    help = 'Usporedi Romcal Croatia i LitCal za odabrani mjesec.'

    def add_arguments(self, parser):
        parser.add_argument('year', nargs='?', type=int, default=date.today().year)
        parser.add_argument('--month', type=int, default=date.today().month)
        parser.add_argument('--json', action='store_true', help='Ispiši puni JSON izvještaj')

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        if month < 1 or month > 12:
            raise CommandError('Mjesec mora biti između 1 i 12.')

        prefix = f'{year}-{month:02d}-'
        romcal_days = {
            iso: day
            for iso, day in RomcalLiturgicalService().get_year_days(year).items()
            if iso.startswith(prefix)
        }
        litcal_service = LiturgicalService()
        _, last = calendar.monthrange(year, month)
        litcal_days = {
            iso: litcal_service.get_day_litcal(iso)
            for day_number in range(1, last + 1)
            if (iso := f'{year}-{month:02d}-{day_number:02d}')
        }
        report = audit_liturgical_days(romcal_days, litcal_days)

        if options['json']:
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
            return

        summary = report['summary']
        self.stdout.write(self.style.SUCCESS(
            f'Liturgijska revizija {year}-{month:02d}: {report["daysChecked"]} dana'
        ))
        self.stdout.write(f'Dani s više slavlja: {summary["multipleObservances"]}')
        self.stdout.write(f'Razlike između izvora: {summary["sourceDifferences"]}')
        self.stdout.write(f'Neprevedeni zapisi: {summary["untranslated"]}')
        self.stdout.write(f'Nedostajući podaci izvora: {summary["missingProviderData"]}')

        for item in report['multipleObservances']:
            labels = ', '.join(
                f'{entry["title"]} ({entry["colorLabel"]})'
                for entry in item['observances']
            )
            self.stdout.write(f'  {item["date"]}: {labels}')
