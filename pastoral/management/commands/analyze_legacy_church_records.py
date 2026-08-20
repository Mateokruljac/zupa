"""Report migration risks in legacy JSON without changing parish data."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from pastoral.models import Parish
from pastoral.services.legacy_registry_analysis import (
    analyze_legacy_parish_records,
)


class Command(BaseCommand):
    help = (
        'Analizira stare JSON zapise osoba, sakramenata i matica. '
        'Naredba je isključivo read-only.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--parish',
            dest='parish_slug',
            help='Analiziraj samo župu s navedenim slugom.',
        )
        parser.add_argument(
            '--format',
            dest='output_format',
            choices=('text', 'json'),
            default='text',
            help='Format izvještaja.',
        )

    def handle(self, *args, **options):
        parish_slug = options.get('parish_slug')
        parishes = Parish.objects.order_by('slug')
        if parish_slug:
            parishes = parishes.filter(slug=parish_slug)
        selected_parishes = list(parishes)
        if not selected_parishes:
            raise CommandError('Nije pronađena nijedna župa za analizu.')

        reports = [
            analyze_legacy_parish_records(parish)
            for parish in selected_parishes
        ]
        if options['output_format'] == 'json':
            self.stdout.write(json.dumps(
                {'parishes': reports},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ))
            return

        for report in reports:
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"Župa: {report['parish_slug']}",
            ))
            for collection_name, collection_report in report['collections'].items():
                self.stdout.write(
                    f"  {collection_name}: {collection_report['record_count']} zapisa; "
                    f"bez ID-a {collection_report['missing_identifier_count']}; "
                    f"dupliciranih ID zapisa {collection_report['duplicate_identifier_record_count']}; "
                    f"nevaljanih datuma {collection_report['invalid_date_count']}; "
                    f"neprepoznatih statusa {collection_report['unrecognized_status_record_count']}"
                )
            personal_identifiers = report['personal_identifiers']
            self.stdout.write(
                '  OIB: '
                f"popunjeno {personal_identifiers['populated_count']}; "
                f"nevaljano {personal_identifiers['invalid_count']}; "
                f"zapisa u mogućim duplikatima {personal_identifiers['duplicate_record_count']}"
            )
            duplicate_identities = report['potential_duplicate_identities']
            review_message = (
                'potrebna je ljudska provjera.'
                if duplicate_identities['requires_human_review']
                else 'nema automatskih spajanja.'
            )
            self.stdout.write(
                '  Mogući duplikati osoba: '
                f"{duplicate_identities['potential_duplicate_group_count']} grupa / "
                f"{duplicate_identities['potential_duplicate_record_count']} zapisa; "
                f'{review_message}'
            )
