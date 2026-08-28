# Tipizirana polja župnog ureda + backfill iz payload-a.

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


def backfill_office_fields(apps, schema_editor):
    OfficeTask = apps.get_model('ured', 'OfficeTask')
    ParishCalendarEvent = apps.get_model('ured', 'ParishCalendarEvent')
    StaffMessage = apps.get_model('ured', 'StaffMessage')
    PublicSubmission = apps.get_model('ured', 'PublicSubmission')
    Announcement = apps.get_model('ured', 'Announcement')

    for task in OfficeTask.objects.all().iterator():
        payload = task.payload or {}
        task.title = str(payload.get('title') or '')
        task.due_date = _parse_iso_date(payload.get('due'))
        task.priority = str(payload.get('priority') or 'srednja')
        task.is_done = bool(payload.get('done'))
        task.category = str(payload.get('category') or '')
        task.payload = {}
        task.save()

    for event in ParishCalendarEvent.objects.all().iterator():
        payload = event.payload or {}
        event.title = str(payload.get('title') or '')
        event.event_date = _parse_iso_date(payload.get('date'))
        event.place = str(payload.get('place') or '')
        event.event_type = str(payload.get('type') or '')
        event.payload = {}
        event.save()

    for message in StaffMessage.objects.all().iterator():
        payload = message.payload or {}
        message.from_name = str(payload.get('from') or '')
        message.from_role = str(payload.get('fromRole') or '')
        message.to_name = str(payload.get('to') or '')
        message.to_role = str(payload.get('toRole') or '')
        message.subject = str(payload.get('subject') or '')
        message.body = str(payload.get('body') or '')
        message.sent_at = str(payload.get('at') or '')
        message.is_read = bool(payload.get('read'))
        message.payload = {}
        message.save()

    for submission in PublicSubmission.objects.all().iterator():
        payload = submission.payload or {}
        form_type = str(payload.get('formType') or payload.get('type') or '')
        known_keys = {
            'id', 'type', 'formType', 'status', 'name', 'phone', 'email',
            'address', 'at', 'data',
        }
        submission.form_type = form_type
        submission.status = str(payload.get('status') or '')
        submission.person_name = str(payload.get('name') or '')
        submission.phone = str(payload.get('phone') or '')
        submission.email = str(payload.get('email') or '')
        submission.address = str(payload.get('address') or '')
        submission.submitted_at = str(payload.get('at') or '')
        submission.form_data = (
            dict(payload.get('data') or {})
            if isinstance(payload.get('data'), dict)
            else {}
        )
        submission.extra = {
            key: value
            for key, value in payload.items()
            if key not in known_keys
        }
        submission.payload = {}
        submission.save()

    for announcement in Announcement.objects.all().iterator():
        payload = announcement.payload or {}
        announcement.title = str(payload.get('title') or '')
        announcement.body = str(payload.get('body') or '')
        announcement.announced_at = str(payload.get('at') or '')
        announcement.payload = {}
        announcement.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ured', '0001_operational_parish_store'),
    ]

    operations = [
        migrations.AddField(model_name='announcement', name='announced_at', field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name='announcement', name='body', field=models.TextField(blank=True)),
        migrations.AddField(model_name='announcement', name='title', field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name='officetask', name='category', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='officetask', name='due_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='officetask', name='is_done', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='officetask', name='priority', field=models.CharField(blank=True, default='srednja', max_length=40)),
        migrations.AddField(model_name='officetask', name='title', field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name='parishcalendarevent', name='event_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='parishcalendarevent', name='event_type', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='parishcalendarevent', name='place', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='parishcalendarevent', name='title', field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name='publicsubmission', name='address', field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name='publicsubmission', name='email', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='publicsubmission', name='extra', field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name='publicsubmission', name='form_data', field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name='publicsubmission', name='form_type', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='publicsubmission', name='person_name', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='publicsubmission', name='phone', field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name='publicsubmission', name='status', field=models.CharField(blank=True, max_length=40)),
        migrations.AddField(model_name='publicsubmission', name='submitted_at', field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name='staffmessage', name='body', field=models.TextField(blank=True)),
        migrations.AddField(model_name='staffmessage', name='from_name', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='staffmessage', name='from_role', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='staffmessage', name='is_read', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='staffmessage', name='sent_at', field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name='staffmessage', name='subject', field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name='staffmessage', name='to_name', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='staffmessage', name='to_role', field=models.CharField(blank=True, max_length=120)),
        migrations.RunPython(backfill_office_fields, noop_reverse),
    ]
