from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_multitenant', '0002_tenant_appearance'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tenant',
            name='appearance',
        ),
    ]
