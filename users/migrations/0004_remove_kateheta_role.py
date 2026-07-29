from django.db import migrations, models


def migrate_kateheta_users(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(role='kateheta').update(role='vikar')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_date_of_birth'),
    ]

    operations = [
        migrations.RunPython(migrate_kateheta_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('zupnik', 'Župnik'),
                    ('vikar', 'Vikar'),
                    ('upravitelj', 'Župni upravitelj'),
                ],
                default='zupnik',
                max_length=20,
            ),
        ),
    ]
