from datetime import date, time
from decimal import Decimal, InvalidOperation

from django.db import migrations


def parse_optional_date(raw_value, parish_slug, field_name):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan datum u polju {field_name}: {raw_value!r}.'
        ) from error


def parse_optional_time(raw_value, parish_slug):
    if not raw_value:
        return None
    try:
        return time.fromisoformat(str(raw_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravno vrijeme mise {raw_value!r}.'
        ) from error


def parse_amount(raw_value, parish_slug):
    try:
        return Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise RuntimeError(
            f'Župa {parish_slug}: neispravan stipendij pogreba {raw_value!r}.'
        ) from error


def cutover_funerals(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    SacramentalEvent = apps.get_model('pastoral', 'SacramentalEvent')
    EventParticipant = apps.get_model('pastoral', 'EventParticipant')
    FuneralDetails = apps.get_model('pastoral', 'FuneralDetails')

    for parish in Parish.objects.select_related(
        'church_sui_iuris', 'default_liturgical_tradition'
    ):
        parish_data = dict(parish.data or {})
        funeral_records = list(parish_data.get('funerals') or [])
        source_identifiers = [
            str(funeral_record.get('id') or '').strip()
            for funeral_record in funeral_records
        ]
        if any(not identifier for identifier in source_identifiers):
            raise RuntimeError(
                f'Župa {parish.slug}: pogreb nema stabilni identifikator.'
            )
        if len(source_identifiers) != len(set(source_identifiers)):
            raise RuntimeError(
                f'Župa {parish.slug}: identifikatori pogreba se ponavljaju.'
            )

        for funeral_record in funeral_records:
            source_identifier = str(funeral_record['id']).strip()
            deceased_name = str(funeral_record.get('deceased') or '').strip()
            if not deceased_name:
                raise RuntimeError(
                    f'Župa {parish.slug}: pogreb {source_identifier} nema pokojnika.'
                )
            event = SacramentalEvent.objects.create(
                parish=parish,
                public_identifier=source_identifier,
                event_type='funeral',
                event_date=parse_optional_date(
                    funeral_record.get('funeralDate'), parish.slug, 'funeralDate'
                ),
                place_name=str(funeral_record.get('cemetery') or '').strip(),
                celebrating_parish=parish,
                minister_name=str(funeral_record.get('celebrant') or '').strip(),
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
                historical_name=deceased_name,
                display_order=0,
            )
            FuneralDetails.objects.create(
                event=event,
                death_date=parse_optional_date(
                    funeral_record.get('deathDate'), parish.slug, 'deathDate'
                ),
                cemetery_location=str(
                    funeral_record.get('cemeteryLocation') or ''
                ).strip(),
                family_contact=str(
                    funeral_record.get('familyContact') or ''
                ).strip(),
                mass_planned=bool(funeral_record.get('massPlanned', False)),
                mass_date=parse_optional_date(
                    funeral_record.get('massDate'), parish.slug, 'massDate'
                ),
                mass_time=parse_optional_time(
                    funeral_record.get('massTime'), parish.slug
                ),
                operational_status=str(
                    funeral_record.get('status') or 'planirano'
                ).strip(),
                stipend=parse_amount(funeral_record.get('stipend'), parish.slug),
                stipend_paid=bool(funeral_record.get('stipendPaid', False)),
            )

        migrated_count = SacramentalEvent.objects.filter(
            parish=parish,
            event_type='funeral',
            public_identifier__in=source_identifiers,
        ).count()
        if migrated_count != len(funeral_records):
            raise RuntimeError(
                f'Župa {parish.slug}: broj migriranih pogreba nije jednak izvornom broju.'
            )

        parish_data.pop('funerals', None)
        parish.data = parish_data
        parish.save(update_fields=('data',))


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0018_funeraldetails'),
    ]

    operations = [
        migrations.RunPython(cutover_funerals, migrations.RunPython.noop),
    ]
