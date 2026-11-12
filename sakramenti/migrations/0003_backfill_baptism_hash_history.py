import hashlib
import json
from datetime import date
from decimal import Decimal

from django.db import migrations


HASHED_FIELD_NAMES = (
    'entry_number', 'birth_date', 'baptism_date', 'child_first_name',
    'child_last_name', 'child_sex', 'baptism_place', 'identifier_type',
    'identifier_value', 'father_first_name', 'father_last_name',
    'father_religion', 'mother_first_name', 'mother_last_name',
    'mother_religion', 'parents_canonically_married',
    'residence_address', 'godparent_first_name', 'godparent_last_name',
    'minister_first_name', 'minister_last_name', 'minister_role',
    'confirmation_date', 'confirmation_place', 'confirmation_parish',
    'marriage_date', 'marriage_parish', 'spouse_first_name',
    'spouse_last_name', 'notes', 'physical_page',
)


def serialized_value(value):
    if isinstance(value, (date, Decimal)):
        return str(value)
    return value


def backfill_hash_and_history(apps, schema_editor):
    BaptismDetails = apps.get_model('sakramenti', 'BaptismDetails')
    BaptismDetailsHistory = apps.get_model(
        'sakramenti', 'BaptismDetailsHistory'
    )
    database_alias = schema_editor.connection.alias

    for baptism_details in BaptismDetails.objects.using(database_alias).iterator():
        snapshot = {
            field_name: serialized_value(getattr(baptism_details, field_name))
            for field_name in HASHED_FIELD_NAMES
        }
        canonical_payload = json.dumps(
            snapshot,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
        )
        content_hash = hashlib.sha256(
            canonical_payload.encode('utf-8')
        ).hexdigest()
        BaptismDetails.objects.using(database_alias).filter(
            pk=baptism_details.pk
        ).update(content_hash=content_hash)
        BaptismDetailsHistory.objects.using(database_alias).get_or_create(
            baptism_details_id=baptism_details.pk,
            content_hash=content_hash,
            defaults={
                'event_id': baptism_details.event_id,
                'change_type': 'created',
                'snapshot': snapshot,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('sakramenti', '0002_baptismdetailshistory_baptismdetails_baptism_date_and_more'),
    ]

    operations = [
        migrations.RunPython(
            backfill_hash_and_history,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
