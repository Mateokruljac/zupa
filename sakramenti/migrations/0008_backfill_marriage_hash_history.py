import hashlib
import json
from datetime import date
from decimal import Decimal

from django.db import migrations


HASHED_FIELD_NAMES = (
    'entry_number', 'physical_page', 'marriage_date', 'marriage_place',
    'groom_first_name', 'groom_last_name', 'groom_birth_place',
    'groom_birth_date', 'groom_oib', 'groom_religion',
    'groom_baptism_date', 'groom_baptism_parish',
    'groom_baptism_parish_address', 'groom_residence_address',
    'bride_first_name', 'bride_last_name', 'bride_birth_place',
    'bride_birth_date', 'bride_oib', 'bride_religion',
    'bride_baptism_date', 'bride_baptism_parish',
    'bride_baptism_parish_address', 'bride_residence_address',
    'groom_father_first_name', 'groom_father_last_name',
    'groom_mother_first_name', 'groom_mother_maiden_name',
    'bride_father_first_name', 'bride_father_last_name',
    'bride_mother_first_name', 'bride_mother_maiden_name',
    'groom_witness_first_name', 'groom_witness_last_name',
    'bride_witness_first_name', 'bride_witness_last_name',
    'officiant_first_name', 'officiant_last_name', 'officiant_role', 'notes',
)


def split_name(value):
    parts = str(value or '').strip().split()
    if len(parts) > 1:
        return ' '.join(parts[:-1]), parts[-1]
    return (parts[0], '') if parts else ('', '')


def serialized_value(value):
    return str(value) if isinstance(value, (date, Decimal)) else value


def backfill(apps, schema_editor):
    Details = apps.get_model('sakramenti', 'MarriageDetails')
    History = apps.get_model('sakramenti', 'MarriageDetailsHistory')
    Participant = apps.get_model('sakramenti', 'EventParticipant')
    alias = schema_editor.connection.alias
    for details in Details.objects.using(alias).select_related('event').iterator():
        event = details.event
        spouses = list(Participant.objects.using(alias).filter(
            event_id=event.pk, role='spouse'
        ).order_by('display_order', 'id')[:2])
        groom = split_name(spouses[0].historical_name) if spouses else split_name(details.couple_display_name.split(' & ', 1)[0])
        bride = split_name(spouses[1].historical_name) if len(spouses) > 1 else split_name(details.couple_display_name.split(' & ', 1)[1] if ' & ' in details.couple_display_name else '')
        groom_witness = split_name(details.groom_witness_name)
        bride_witness = split_name(details.bride_witness_name)
        officiant = split_name(event.minister_name)
        updates = {
            'marriage_date': event.event_date, 'marriage_place': event.place_name or '',
            'groom_first_name': groom[0], 'groom_last_name': groom[1],
            'bride_first_name': bride[0], 'bride_last_name': bride[1],
            'groom_witness_first_name': groom_witness[0], 'groom_witness_last_name': groom_witness[1],
            'bride_witness_first_name': bride_witness[0], 'bride_witness_last_name': bride_witness[1],
            'officiant_first_name': officiant[0], 'officiant_last_name': officiant[1],
        }
        for name, value in updates.items():
            setattr(details, name, value)
        snapshot = {name: serialized_value(getattr(details, name)) for name in HASHED_FIELD_NAMES}
        content_hash = hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        updates['content_hash'] = content_hash
        Details.objects.using(alias).filter(pk=details.pk).update(**updates)
        History.objects.using(alias).get_or_create(
            marriage_details_id=details.pk, content_hash=content_hash,
            defaults={'event_id': details.event_id, 'change_type': 'created', 'snapshot': snapshot},
        )


class Migration(migrations.Migration):
    dependencies = [('sakramenti', '0007_marriagedetailshistory_and_more')]
    operations = [migrations.RunPython(backfill, reverse_code=migrations.RunPython.noop)]
