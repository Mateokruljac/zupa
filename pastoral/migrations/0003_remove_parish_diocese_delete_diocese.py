# Generated manually — uklanja duplicirani Diocese model.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parish',
            name='diocese',
        ),
        migrations.DeleteModel(
            name='Diocese',
        ),
    ]
