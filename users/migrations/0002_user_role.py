from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('zupnik', 'Župnik'),
                    ('vikar', 'Vikar'),
                    ('upravitelj', 'Župni upravitelj'),
                    ('kateheta', 'Kateheta'),
                ],
                default='zupnik',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='address',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(db_index=True, max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(blank=True, db_index=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
