# Tipizirana polja za raspored misa i nakane + backfill iz payload-a.

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import migrations, models


def _parse_iso_date(value):
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _decimal_amount(value):
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _weekdays_list(value):
    if not isinstance(value, list):
        return []
    weekdays = []
    for item in value:
        try:
            weekdays.append(int(item))
        except (TypeError, ValueError):
            continue
    return weekdays


def backfill_typed_mass_fields(apps, schema_editor):
    MassScheduleSlot = apps.get_model('liturgija', 'MassScheduleSlot')
    MassIntention = apps.get_model('liturgija', 'MassIntention')

    for slot in MassScheduleSlot.objects.all().iterator():
        payload = slot.payload or {}
        slot.day_label = str(payload.get('day') or '')
        slot.mass_time = str(payload.get('time') or '')
        slot.weekdays = _weekdays_list(payload.get('weekdays'))
        slot.celebrant = str(payload.get('celebrant') or '')
        slot.location = str(payload.get('location') or '')
        slot.notes = str(payload.get('notes') or '')
        slot.valid_from = _parse_iso_date(payload.get('validFrom'))
        slot.valid_until = _parse_iso_date(payload.get('validUntil'))
        slot.no_mass = bool(payload.get('noMass'))
        slot.payload = {}
        slot.save()

    for intention in MassIntention.objects.all().iterator():
        payload = intention.payload or {}
        intention.intention_date = _parse_iso_date(payload.get('date'))
        intention.mass_time = str(payload.get('massTime') or '')
        intention.requested_by = str(payload.get('requestedBy') or '')
        intention.intention_for = str(payload.get('intentionFor') or '')
        intention.stipend = _decimal_amount(payload.get('stipend'))
        intention.is_paid = bool(payload.get('paid'))
        intention.notes = str(payload.get('notes') or '')
        intention.payload = {}
        intention.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('liturgija', '0002_operational_parish_store'),
    ]

    operations = [
        migrations.AddField(
            model_name='massintention',
            name='intention_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='massintention',
            name='intention_for',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='massintention',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='massintention',
            name='mass_time',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='massintention',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='massintention',
            name='requested_by',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='massintention',
            name='stipend',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='celebrant',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='day_label',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='location',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='mass_time',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='no_mass',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='valid_from',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='valid_until',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='massscheduleslot',
            name='weekdays',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(backfill_typed_mass_fields, noop_reverse),
    ]
