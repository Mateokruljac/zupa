from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zupa_vjernici', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='street',
            name='zone',
        ),
        migrations.AddField(
            model_name='street',
            name='city',
            field=models.CharField(blank=True, max_length=120, verbose_name='Grad'),
        ),
        migrations.AlterField(
            model_name='street',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Ulica'),
        ),
    ]
