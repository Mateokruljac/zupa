from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_multitenant', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='appearance',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Boje, paleta i svijetli/tamni način ovog tenanta.',
                verbose_name='Izgled',
            ),
        ),
    ]
