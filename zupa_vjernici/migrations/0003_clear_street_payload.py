# Clear Street.payload — tipizirana polja su izvor istine.

from django.db import migrations


def clear_street_payloads(apps, schema_editor):
    Street = apps.get_model('zupa_vjernici', 'Street')
    Street.objects.all().update(payload={})


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('zupa_vjernici', '0002_operational_parish_store'),
    ]

    operations = [
        migrations.RunPython(clear_street_payloads, noop_reverse),
    ]
