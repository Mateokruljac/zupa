# Tipizirane misne iznimke i log rasporeda + backfill.

from datetime import date

from django.db import migrations, models


def _parse_iso_date(value):
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def backfill_mass_exception_and_log(apps, schema_editor):
    MassException = apps.get_model('liturgija', 'MassException')
    MassScheduleLogEntry = apps.get_model('liturgija', 'MassScheduleLogEntry')

    for exception in MassException.objects.all().iterator():
        payload = exception.payload or {}
        exception.exception_date = _parse_iso_date(payload.get('date'))
        exception.cancel_all = bool(payload.get('cancelAll'))
        exception.cancel_times = (
            list(payload.get('cancelTimes') or [])
            if isinstance(payload.get('cancelTimes'), list)
            else []
        )
        exception.add_slots = (
            list(payload.get('addSlots') or [])
            if isinstance(payload.get('addSlots'), list)
            else []
        )
        exception.note = str(payload.get('note') or '')
        exception.payload = {}
        exception.save()

    for entry in MassScheduleLogEntry.objects.all().iterator():
        payload = entry.payload or {}
        entry.logged_at = str(payload.get('at') or '')
        entry.message = str(payload.get('message') or '')
        entry.payload = {}
        entry.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('liturgija', '0003_typed_mass_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='massexception',
            name='add_slots',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='massexception',
            name='cancel_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='massexception',
            name='cancel_times',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='massexception',
            name='exception_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='massexception',
            name='note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='massschedulelogentry',
            name='logged_at',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='massschedulelogentry',
            name='message',
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(backfill_mass_exception_and_log, noop_reverse),
    ]
