import uuid

import django.db.models.deletion
import public_site.models
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='ParishWebsite',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('parish_identifier', models.SlugField(unique=True)),
                ('status', models.CharField(choices=[('draft', 'Skica'), ('live', 'Objavljeno'), ('suspended', 'Privremeno obustavljeno'), ('archived', 'Arhivirano')], db_index=True, default='draft', max_length=20)),
                ('subdomain', models.SlugField(unique=True)),
                ('custom_domain', models.CharField(blank=True, max_length=253)),
                ('template_key', models.CharField(choices=[('classic', 'Klasični'), ('warm', 'Topli pastoralni'), ('modern', 'Suvremeni')], default='classic', max_length=24)),
                ('site_name', models.CharField(max_length=200)),
                ('tagline', models.CharField(blank=True, max_length=240)),
                ('about_text', models.TextField(blank=True)),
                ('primary_color', models.CharField(default='#5c2e3a', max_length=7)),
                ('accent_color', models.CharField(default='#b8922a', max_length=7)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=40)),
                ('address', models.CharField(blank=True, max_length=240)),
                ('office_hours', models.TextField(blank=True)),
                ('confession_schedule', models.TextField(blank=True)),
                ('iban', models.CharField(blank=True, max_length=34)),
                ('donation_recipient', models.CharField(blank=True, max_length=200)),
                ('donation_purpose', models.CharField(blank=True, max_length=240)),
                ('map_url', models.URLField(blank=True)),
                ('facebook_url', models.URLField(blank=True)),
                ('youtube_url', models.URLField(blank=True)),
                ('instagram_url', models.URLField(blank=True)),
                ('enabled_sections', models.JSONField(blank=True, default=list)),
                ('published_snapshot', models.JSONField(blank=True, default=dict)),
                ('activated_at', models.DateTimeField(default=timezone.now)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requested_parish_websites', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('site_name',), 'verbose_name': 'Javna web-stranica župe', 'verbose_name_plural': 'Javne web-stranice župa'},
        ),
        migrations.CreateModel(
            name='ParishWebsiteMedia',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(choices=[('hero', 'Naslovna fotografija'), ('gallery', 'Galerija')], db_index=True, max_length=16)),
                ('image', models.ImageField(max_length=255, upload_to=public_site.models.website_media_upload_to)),
                ('alt_text', models.CharField(max_length=240)),
                ('caption', models.CharField(blank=True, max_length=240)),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('width', models.PositiveIntegerField()),
                ('height', models.PositiveIntegerField()),
                ('file_size', models.PositiveIntegerField()),
                ('is_visible', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_parish_website_media', to=settings.AUTH_USER_MODEL)),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='public_site.parishwebsite')),
            ],
            options={
                'ordering': ('kind', 'sort_order', 'created_at'),
                'verbose_name': 'Fotografija javne web-stranice',
                'verbose_name_plural': 'Fotografije javnih web-stranica',
            },
        ),
    ]
