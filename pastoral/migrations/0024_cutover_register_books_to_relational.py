from datetime import date

from django.db import migrations


EVENT_TYPE_BY_REGISTRY_TYPE = {
    'krštenja': 'baptism',
    'vjenčanja': 'marriage',
    'umrli': 'funeral',
    'krizma': 'confirmation',
}


def parse_optional_date(raw_value, parish_slug):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan datum zadnjeg unosa {raw_value!r}.'
        ) from error


def get_template_version(models, registry_type):
    event_type = EVENT_TYPE_BY_REGISTRY_TYPE.get(registry_type)
    if event_type is None:
        return None
    register_template, _ = models['RegisterTemplate'].objects.get_or_create(
        code=f'{event_type}-register-compatibility',
        defaults={
            'event_type': event_type,
            'name': f'Kompatibilni predložak: {registry_type}',
            'owner_scope': 'system',
            'is_official': False,
            'is_active': True,
        },
    )
    template_version, _ = models['RegisterTemplateVersion'].objects.get_or_create(
        template=register_template,
        version_number=1,
        defaults={
            'status': 'draft',
            'field_schema': [],
            'validation_schema': {'official_form_approved': False},
            'terminology': {},
            'print_configuration': {'enabled': False},
        },
    )
    return template_version


def find_reusable_book(models, parish, registry_type):
    event_type = EVENT_TYPE_BY_REGISTRY_TYPE.get(registry_type)
    if event_type is None:
        return None
    return models['RegisterBook'].objects.filter(
        parish=parish,
        public_identifier='',
        template_version__template__event_type=event_type,
    ).first()


def cutover_register_books(apps, schema_editor):
    model_names = (
        'Parish', 'RegisterBook', 'RegisterBookYear', 'RegisterTemplate',
        'RegisterTemplateVersion', 'SacramentalEvent',
    )
    models = {
        model_name: apps.get_model('pastoral', model_name)
        for model_name in model_names
    }

    for parish in models['Parish'].objects.all():
        parish_data = dict(parish.data or {})
        source_books = list(parish_data.get('registryBooks') or [])
        source_identifiers = [
            str(source_book.get('id') or '').strip()
            for source_book in source_books
        ]
        if any(not identifier for identifier in source_identifiers):
            raise RuntimeError(
                f'Župa {parish.slug}: matična knjiga nema stabilni identifikator.'
            )
        if len(source_identifiers) != len(set(source_identifiers)):
            raise RuntimeError(
                f'Župa {parish.slug}: identifikatori matičnih knjiga se ponavljaju.'
            )

        for source_book in source_books:
            registry_type = str(source_book.get('type') or 'ostalo').strip()
            if registry_type not in {*EVENT_TYPE_BY_REGISTRY_TYPE, 'ostalo'}:
                registry_type = 'ostalo'
            public_identifier = str(source_book['id']).strip()
            template_version = get_template_version(models, registry_type)
            register_book = find_reusable_book(models, parish, registry_type)
            if register_book is None:
                register_book = models['RegisterBook'].objects.create(
                    parish=parish,
                    template_version=template_version,
                    title=str(source_book.get('title') or 'Matična knjiga').strip(),
                )
            elif register_book.template_version_id:
                template_version = register_book.template_version

            last_entry_date = parse_optional_date(
                source_book.get('lastEntry'), parish.slug
            )
            register_book.public_identifier = public_identifier
            register_book.registry_type = registry_type
            register_book.template_version = template_version
            register_book.title = str(
                source_book.get('title') or 'Matična knjiga'
            ).strip()
            register_book.location = str(source_book.get('location') or '').strip()
            register_book.custodian = str(source_book.get('custodian') or '').strip()
            register_book.status = 'active'
            register_book.operational_status = str(
                source_book.get('status') or ''
            ).strip()
            register_book.last_entry_date = last_entry_date
            register_book.last_entry_reference = str(
                source_book.get('lastNo') or ''
            ).strip()
            register_book.notes = str(source_book.get('notes') or '').strip()
            register_book.save()

            available_years = {
                int(configured_year)
                for configured_year in source_book.get('years') or []
                if str(configured_year).isdigit()
            }
            if last_entry_date:
                available_years.add(last_entry_date.year)
            event_type = EVENT_TYPE_BY_REGISTRY_TYPE.get(registry_type)
            if event_type:
                available_years.update(
                    event_date.year
                    for event_date in models['SacramentalEvent'].objects.filter(
                        parish=parish,
                        event_type=event_type,
                        event_date__isnull=False,
                    ).values_list('event_date', flat=True)
                )
            for registry_year in available_years:
                models['RegisterBookYear'].objects.get_or_create(
                    register_book=register_book,
                    year=registry_year,
                )

        migrated_count = models['RegisterBook'].objects.filter(
            parish=parish,
            public_identifier__in=source_identifiers,
        ).count()
        if migrated_count != len(source_books):
            raise RuntimeError(
                f'Župa {parish.slug}: broj migriranih matičnih knjiga nije jednak izvornom broju.'
            )

        parish_data.pop('registryBooks', None)
        parish.data = parish_data
        parish.save(update_fields=('data',))


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0023_alter_registerbook_template_version'),
    ]

    operations = [
        migrations.RunPython(cutover_register_books, migrations.RunPython.noop),
    ]
