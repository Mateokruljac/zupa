from datetime import date, time

from django.db import migrations


def parse_optional_date(raw_value, parish_slug):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan datum pomazanja {raw_value!r}.'
        ) from error


def parse_optional_time(raw_value, parish_slug):
    if not raw_value:
        return None
    try:
        return time.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravno vrijeme pomazanja {raw_value!r}.'
        ) from error


def cutover_anointings(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    SacramentalEvent = apps.get_model('pastoral', 'SacramentalEvent')
    EventParticipant = apps.get_model('pastoral', 'EventParticipant')
    AnointingDetails = apps.get_model('pastoral', 'AnointingDetails')

    for parish in Parish.objects.select_related(
        'church_sui_iuris', 'default_liturgical_tradition'
    ):
        parish_data = dict(parish.data or {})
        anointing_records = list(parish_data.get('anointing') or [])
        source_identifiers = [
            str(anointing_record.get('id') or '').strip()
            for anointing_record in anointing_records
        ]
        if any(not identifier for identifier in source_identifiers):
            raise RuntimeError(
                f'Župa {parish.slug}: pomazanje nema stabilni identifikator.'
            )
        if len(source_identifiers) != len(set(source_identifiers)):
            raise RuntimeError(
                f'Župa {parish.slug}: identifikatori pomazanja se ponavljaju.'
            )

        for anointing_record in anointing_records:
            source_identifier = str(anointing_record['id']).strip()
            recipient_name = str(anointing_record.get('person') or '').strip()
            if not recipient_name:
                raise RuntimeError(
                    f'Župa {parish.slug}: pomazanje {source_identifier} nema osobu.'
                )
            address = str(anointing_record.get('address') or '').strip()
            event = SacramentalEvent.objects.create(
                parish=parish,
                public_identifier=source_identifier,
                event_type='anointing',
                event_date=parse_optional_date(
                    anointing_record.get('scheduled'), parish.slug
                ),
                place_name=address,
                celebrating_parish=parish,
                minister_name=str(anointing_record.get('priest') or '').strip(),
                liturgical_tradition=parish.default_liturgical_tradition,
                canonical_tradition=(
                    parish.church_sui_iuris.canonical_tradition
                    if parish.church_sui_iuris_id
                    else 'unconfirmed'
                ),
                status='draft',
                source='legacy_import',
            )
            EventParticipant.objects.create(
                parish=parish,
                event=event,
                role='recipient',
                historical_name=recipient_name,
                display_order=0,
            )
            AnointingDetails.objects.create(
                event=event,
                scheduled_time=parse_optional_time(
                    anointing_record.get('scheduledTime'), parish.slug
                ),
                address=address,
                location=str(anointing_record.get('location') or '').strip(),
                contact=str(anointing_record.get('contact') or '').strip(),
                notes=str(anointing_record.get('notes') or '').strip(),
                operational_status=str(
                    anointing_record.get('status') or 'planirano'
                ).strip(),
                completed=bool(anointing_record.get('done', False)),
            )

        migrated_count = SacramentalEvent.objects.filter(
            parish=parish,
            event_type='anointing',
            public_identifier__in=source_identifiers,
        ).count()
        if migrated_count != len(anointing_records):
            raise RuntimeError(
                f'Župa {parish.slug}: broj migriranih pomazanja nije jednak izvornom broju.'
            )

        parish_data.pop('anointing', None)
        parish.data = parish_data
        parish.save(update_fields=('data',))


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0020_anointingdetails'),
    ]

    operations = [
        migrations.RunPython(cutover_anointings, migrations.RunPython.noop),
    ]
