from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import migrations


def parse_optional_date(raw_value, parish_slug):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan datum vjenčanja {raw_value!r}.'
        ) from error


def parse_amount(raw_value, parish_slug):
    try:
        return Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan stipendij vjenčanja {raw_value!r}.'
        ) from error


def spouse_names(wedding_record):
    groom_name = str(wedding_record.get('groomName') or '').strip()
    bride_name = str(wedding_record.get('brideName') or '').strip()
    if groom_name or bride_name:
        return groom_name, bride_name
    couple_name = str(wedding_record.get('couple') or '').strip()
    separated_names = couple_name.split(' & ', 1)
    if len(separated_names) == 2:
        return separated_names[0].strip(), separated_names[1].strip()
    return '', ''


def cutover_weddings(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    SacramentalEvent = apps.get_model('pastoral', 'SacramentalEvent')
    EventParticipant = apps.get_model('pastoral', 'EventParticipant')
    MarriageDetails = apps.get_model('pastoral', 'MarriageDetails')

    for parish in Parish.objects.select_related(
        'church_sui_iuris', 'default_liturgical_tradition'
    ):
        parish_data = dict(parish.data or {})
        wedding_records = list(parish_data.get('weddings') or [])
        source_identifiers = [
            str(wedding_record.get('id') or '').strip()
            for wedding_record in wedding_records
        ]
        if any(not identifier for identifier in source_identifiers):
            raise RuntimeError(
                f'Župa {parish.slug}: vjenčanje nema stabilni identifikator.'
            )
        if len(source_identifiers) != len(set(source_identifiers)):
            raise RuntimeError(
                f'Župa {parish.slug}: identifikatori vjenčanja se ponavljaju.'
            )

        for wedding_record in wedding_records:
            source_identifier = str(wedding_record['id']).strip()
            couple_name = str(wedding_record.get('couple') or '').strip()
            if not couple_name:
                groom_name, bride_name = spouse_names(wedding_record)
                couple_name = ' & '.join(
                    name for name in (groom_name, bride_name) if name
                )
            if not couple_name:
                raise RuntimeError(
                    f'Župa {parish.slug}: vjenčanje {source_identifier} nema mladence.'
                )

            event = SacramentalEvent.objects.create(
                parish=parish,
                public_identifier=source_identifier,
                event_type='marriage',
                event_date=parse_optional_date(
                    wedding_record.get('weddingDate'), parish.slug
                ),
                place_name=str(wedding_record.get('church') or '').strip(),
                celebrating_parish=parish,
                minister_name=str(wedding_record.get('celebrant') or '').strip(),
                liturgical_tradition=parish.default_liturgical_tradition,
                canonical_tradition=(
                    parish.church_sui_iuris.canonical_tradition
                    if parish.church_sui_iuris_id
                    else 'unconfirmed'
                ),
                status='draft',
                source='legacy_import',
            )
            groom_name, bride_name = spouse_names(wedding_record)
            for display_order, spouse_name in enumerate((groom_name, bride_name)):
                if spouse_name:
                    EventParticipant.objects.create(
                        parish=parish,
                        event=event,
                        role='spouse',
                        historical_name=spouse_name,
                        display_order=display_order,
                    )
            MarriageDetails.objects.create(
                event=event,
                couple_display_name=couple_name,
                contact=str(wedding_record.get('contact') or '').strip(),
                preparatory_sessions=int(
                    wedding_record.get('preparatorySessions') or 0
                ),
                documents_complete=bool(wedding_record.get('documentsOk', False)),
                witnesses_name=str(
                    wedding_record.get('witnesses')
                    or ', '.join(
                        name
                        for name in (
                            str(wedding_record.get('groomSponsor') or '').strip(),
                            str(wedding_record.get('brideSponsor') or '').strip(),
                        )
                        if name
                    )
                ).strip(),
                operational_status=str(
                    wedding_record.get('status') or 'planirano'
                ).strip(),
                stipend=parse_amount(wedding_record.get('stipend'), parish.slug),
                stipend_paid=bool(wedding_record.get('stipendPaid', False)),
            )

        migrated_count = SacramentalEvent.objects.filter(
            parish=parish,
            event_type='marriage',
            public_identifier__in=source_identifiers,
        ).count()
        if migrated_count != len(wedding_records):
            raise RuntimeError(
                f'Župa {parish.slug}: broj migriranih vjenčanja nije jednak izvornom broju.'
            )

        parish_data.pop('weddings', None)
        parish.data = parish_data
        parish.save(update_fields=('data',))


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0015_marriagedetails'),
    ]

    operations = [
        migrations.RunPython(cutover_weddings, migrations.RunPython.noop),
    ]
