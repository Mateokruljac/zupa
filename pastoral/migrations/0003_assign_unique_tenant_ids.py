import uuid

from django.db import migrations


def assign_unique_tenant_ids(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    for parish in Parish.objects.all().iterator():
        parish.tenant_id = uuid.uuid4()
        parish.save(update_fields=['tenant_id'])


def clear_tenant_ids(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    Parish.objects.update(tenant_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ('pastoral', '0002_parish_diocese_parish_lifecycle_status_and_more'),
    ]

    operations = [
        migrations.RunPython(assign_unique_tenant_ids, clear_tenant_ids),
    ]

