from datetime import date

from django.db import migrations


def parse_required_date(raw_value, parish_slug, source_identifier):
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: opći zapis {source_identifier} nema valjan datum.'
        ) from error


def cutover_general_register_entries(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    RegisterBook = apps.get_model('pastoral', 'RegisterBook')
    RegisterBookYear = apps.get_model('pastoral', 'RegisterBookYear')
    GeneralRegisterEntry = apps.get_model('pastoral', 'GeneralRegisterEntry')

    for parish in Parish.objects.all():
        parish_data = dict(parish.data or {})
        source_entries = list(parish_data.get('registryEntries') or [])
        source_identifiers = [
            str(source_entry.get('id') or '').strip()
            for source_entry in source_entries
        ]
        if any(not identifier for identifier in source_identifiers):
            raise RuntimeError(
                f'Župa {parish.slug}: opći matični zapis nema stabilni identifikator.'
            )
        if len(source_identifiers) != len(set(source_identifiers)):
            raise RuntimeError(
                f'Župa {parish.slug}: identifikatori općih matičnih zapisa se ponavljaju.'
            )

        for source_entry in source_entries:
            source_identifier = str(source_entry['id']).strip()
            book_identifier = str(source_entry.get('bookId') or '').strip()
            try:
                register_book = RegisterBook.objects.get(
                    parish=parish,
                    public_identifier=book_identifier,
                )
            except RegisterBook.DoesNotExist as error:
                raise RuntimeError(
                    f'Župa {parish.slug}: knjiga {book_identifier!r} za opći zapis ne postoji.'
                ) from error
            record_date = parse_required_date(
                source_entry.get('recordDate'),
                parish.slug,
                source_identifier,
            )
            registry_year = int(source_entry.get('year') or record_date.year)
            if record_date.year != registry_year:
                raise RuntimeError(
                    f'Župa {parish.slug}: datum općeg zapisa {source_identifier} ne pripada godini knjige.'
                )
            register_book_year, _ = RegisterBookYear.objects.get_or_create(
                register_book=register_book,
                year=registry_year,
            )
            GeneralRegisterEntry.objects.create(
                public_identifier=source_identifier,
                register_book_year=register_book_year,
                registry_reference=str(
                    source_entry.get('registryNo') or ''
                ).strip(),
                subject_name=str(source_entry.get('subjectName') or '').strip(),
                record_date=record_date,
                place=str(source_entry.get('place') or '').strip(),
                responsible_name=str(
                    source_entry.get('celebrant') or ''
                ).strip(),
                operational_status=str(
                    source_entry.get('status') or 'upisano'
                ).strip(),
            )

        migrated_count = GeneralRegisterEntry.objects.filter(
            register_book_year__register_book__parish=parish,
            public_identifier__in=source_identifiers,
        ).count()
        if migrated_count != len(source_entries):
            raise RuntimeError(
                f'Župa {parish.slug}: broj migriranih općih zapisa nije jednak izvornom broju.'
            )

        parish_data.pop('registryEntries', None)
        parish.data = parish_data
        parish.save(update_fields=('data',))


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0026_generalregisterentry'),
    ]

    operations = [
        migrations.RunPython(
            cutover_general_register_entries,
            migrations.RunPython.noop,
        ),
    ]
