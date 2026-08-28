from django.db import migrations, models

from financije.ledgers import normalize_ledger


def remap_legacy_ledgers(apps, schema_editor):
    CashbookEntry = apps.get_model('financije', 'CashbookEntry')
    for entry in CashbookEntry.objects.all().iterator():
        entry.ledger = normalize_ledger(entry.ledger, entry.category)
        entry.save(update_fields=['ledger'])


class Migration(migrations.Migration):

    dependencies = [
        ('financije', '0002_typed_finance_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashbookentry',
            name='ledger',
            field=models.CharField(blank=True, default='crkveni', max_length=40),
        ),
        migrations.RunPython(remap_legacy_ledgers, migrations.RunPython.noop),
    ]
