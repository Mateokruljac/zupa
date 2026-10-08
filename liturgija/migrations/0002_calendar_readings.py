from django.db import migrations, models
import django_jsonform.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('liturgija', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='liturgicalcalendarentry',
            name='readings',
            field=django_jsonform.models.fields.JSONField(
                blank=True,
                default=list,
                help_text='Npr. Prvo čitanje → Pnz 7,14-22. Drugo čitanje je opcionalno.',
                schema={
                    'type': 'array',
                    'title': 'Čitanja',
                    'items': {
                        'type': 'dict',
                        'keys': {
                            'label': {
                                'type': 'string',
                                'title': 'Naziv',
                                'default': '',
                            },
                            'value': {
                                'type': 'string',
                                'title': 'Kratica',
                                'default': '',
                            },
                        },
                    },
                },
                verbose_name='Čitanja (kratice)',
            ),
        ),
        migrations.AlterField(
            model_name='liturgicalcalendarentry',
            name='priority',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='Stupanj iz Romcala; koristi se samo za auto-odabir glavnog slavlja.',
                verbose_name='Rang (Romcal)',
            ),
        ),
        migrations.AlterField(
            model_name='liturgicalcalendarentry',
            name='is_primary',
            field=models.BooleanField(
                db_index=True,
                default=True,
                help_text=(
                    'Ako označite ovo slavlje kao glavno, drugo glavno slavlje '
                    'na isti dan bit će odznačeno.'
                ),
                verbose_name='Glavno slavlje dana',
            ),
        ),
        migrations.AlterField(
            model_name='liturgicalcalendarentry',
            name='priority_label',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Svetkovina', 'Svetkovina'),
                    ('Blagdan', 'Blagdan'),
                    ('Spomendan', 'Spomendan'),
                    ('Svagdan', 'Svagdan'),
                    ('Ostalo', 'Ostalo'),
                ],
                max_length=120,
                verbose_name='Vrsta slavlja',
            ),
        ),
    ]
