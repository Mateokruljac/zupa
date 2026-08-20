import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


CONFIGURATION_FIELDS = (
    'site_name', 'tagline', 'about_text', 'template_key', 'primary_color',
    'accent_color', 'contact_email', 'phone', 'address', 'office_hours',
    'confession_schedule', 'iban', 'donation_recipient', 'donation_purpose',
    'map_url', 'facebook_url', 'youtube_url', 'instagram_url', 'custom_domain',
    'enabled_sections',
)


def seed_published_configuration(apps, schema_editor):
    ParishWebsite = apps.get_model('public_site', 'ParishWebsite')
    for website in ParishWebsite.objects.all().iterator():
        if website.status == 'live':
            website.publication_status = 'published'
            website.published_configuration = {
                field: getattr(website, field)
                for field in CONFIGURATION_FIELDS
            }
            website.save(update_fields=('publication_status', 'published_configuration'))


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('public_site', '0004_parishwebsitemedia'),
    ]

    operations = [
        migrations.AddField(
            model_name='parishwebsite',
            name='publication_status',
            field=models.CharField(
                choices=[('draft', 'Skica'), ('scheduled', 'Zakazano'), ('published', 'Objavljeno')],
                db_index=True,
                default='draft',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='parishwebsite',
            name='published_configuration',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name='PublicContentPublication',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(choices=[('announcement', 'Obavijest'), ('event', 'Događanje')], db_index=True, max_length=20)),
                ('source_key', models.CharField(max_length=64)),
                ('source_label', models.CharField(blank=True, max_length=200)),
                ('status', models.CharField(choices=[('draft', 'Skica'), ('scheduled', 'Zakazano'), ('published', 'Objavljeno')], db_index=True, default='draft', max_length=16)),
                ('scheduled_for', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='updated_public_content_publications', to=settings.AUTH_USER_MODEL)),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_publications', to='public_site.parishwebsite')),
            ],
            options={
                'verbose_name': 'Kontrola javne objave',
                'verbose_name_plural': 'Kontrole javnih objava',
                'ordering': ('kind', 'source_label'),
            },
        ),
        migrations.AddConstraint(
            model_name='publiccontentpublication',
            constraint=models.UniqueConstraint(fields=('website', 'kind', 'source_key'), name='public_site_unique_content_publication'),
        ),
        migrations.RunPython(seed_published_configuration, migrations.RunPython.noop),
    ]
