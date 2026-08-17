from datetime import date

from django.db import migrations
from django.utils.text import slugify


def seed_existing_demo_tenant(apps, schema_editor):
    Parish = apps.get_model('pastoral', 'Parish')
    User = apps.get_model('users', 'User')
    Diocese = apps.get_model('control_plane', 'Diocese')
    Membership = apps.get_model('control_plane', 'ParishMembership')
    LicenseGrant = apps.get_model('control_plane', 'LicenseGrant')
    Entitlement = apps.get_model('control_plane', 'LicenseEntitlement')
    AuditEvent = apps.get_model('control_plane', 'ControlPlaneAuditEvent')

    parishes = list(Parish.objects.all())
    for parish in parishes:
        settings_data = parish.settings or {}
        diocese_name = settings_data.get('diocese')
        if diocese_name and parish.diocese_id is None:
            base_code = slugify(diocese_name)[:45] or 'biskupija'
            diocese, _ = Diocese.objects.get_or_create(
                name=diocese_name,
                defaults={'code': base_code},
            )
            parish.diocese_id = diocese.id
            parish.save(update_fields=['diocese'])

        grant = LicenseGrant.objects.filter(
            parish_id=parish.id,
            plan_code='legacy-demo',
        ).first()
        if grant is None:
            grant = LicenseGrant.objects.create(
                parish_id=parish.id,
                status='active',
                valid_from=date(2026, 1, 1),
                valid_until=date(2027, 12, 31),
                grace_until=date(2028, 1, 30),
                plan_code='legacy-demo',
                terms_version='demo-1',
            )
        Entitlement.objects.get_or_create(
            grant_id=grant.id,
            code='pastoral-core',
            defaults={'enabled': True},
        )
        AuditEvent.objects.get_or_create(
            parish_id=parish.id,
            event_type='tenant.bootstrap',
            target_type='pastoral.Parish',
            target_id=str(parish.tenant_id),
            defaults={
                'outcome': 'success',
                'metadata': {'source': 'migration', 'version': 1},
            },
        )

    default_parish = next(
        (item for item in parishes if item.slug == 'bdm-slavonski-brod'),
        parishes[0] if parishes else None,
    )
    if default_parish is not None:
        valid_roles = {'zupnik', 'vikar', 'upravitelj'}
        for user in User.objects.all():
            Membership.objects.get_or_create(
                parish_id=default_parish.id,
                user_id=user.id,
                defaults={
                    'role': user.role if user.role in valid_roles else 'zupnik',
                    'status': 'active',
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ('control_plane', '0001_initial'),
        ('pastoral', '0004_alter_parish_tenant_id'),
        ('users', '0004_remove_kateheta_role'),
    ]

    operations = [
        migrations.RunPython(seed_existing_demo_tenant, migrations.RunPython.noop),
    ]

