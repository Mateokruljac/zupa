import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def website_media_upload_to(instance, _filename):
    return (
        f'public-sites/{instance.website.parish_identifier}/'
        f'{instance.website_id}/{uuid.uuid4().hex}.webp'
    )


class ParishWebsite(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Skica'
        LIVE = 'live', 'Objavljeno'
        SUSPENDED = 'suspended', 'Privremeno obustavljeno'
        ARCHIVED = 'archived', 'Arhivirano'

    class Template(models.TextChoices):
        CLASSIC = 'classic', 'Klasični'
        WARM = 'warm', 'Topli pastoralni'
        MODERN = 'modern', 'Suvremeni'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish_identifier = models.SlugField(unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    subdomain = models.SlugField(unique=True)
    custom_domain = models.CharField(max_length=253, blank=True)
    template_key = models.CharField(
        max_length=24,
        choices=Template.choices,
        default=Template.CLASSIC,
    )
    site_name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=240, blank=True)
    about_text = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, default='#5c2e3a')
    accent_color = models.CharField(max_length=7, default='#b8922a')
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=240, blank=True)
    office_hours = models.TextField(blank=True)
    confession_schedule = models.TextField(blank=True)
    iban = models.CharField(max_length=34, blank=True)
    donation_recipient = models.CharField(max_length=200, blank=True)
    donation_purpose = models.CharField(max_length=240, blank=True)
    map_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    enabled_sections = models.JSONField(default=list, blank=True)
    published_snapshot = models.JSONField(default=dict, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='requested_parish_websites',
        null=True,
        blank=True,
    )
    activated_at = models.DateTimeField(default=timezone.now)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('site_name',)
        verbose_name = 'Javna web-stranica župe'
        verbose_name_plural = 'Javne web-stranice župa'

    def __str__(self):
        return f'{self.site_name} · {self.get_status_display()}'

    @property
    def public_hostname(self):
        return self.custom_domain or self.subdomain


class ParishWebsiteMedia(models.Model):
    class Kind(models.TextChoices):
        HERO = 'hero', 'Naslovna fotografija'
        GALLERY = 'gallery', 'Galerija'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(
        ParishWebsite,
        on_delete=models.CASCADE,
        related_name='media',
    )
    kind = models.CharField(max_length=16, choices=Kind.choices, db_index=True)
    image = models.ImageField(upload_to=website_media_upload_to, max_length=255)
    alt_text = models.CharField(max_length=240)
    caption = models.CharField(max_length=240, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    file_size = models.PositiveIntegerField()
    is_visible = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='uploaded_parish_website_media',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('kind', 'sort_order', 'created_at')
        verbose_name = 'Fotografija javne web-stranice'
        verbose_name_plural = 'Fotografije javnih web-stranica'

    def __str__(self):
        return f'{self.website.site_name} · {self.get_kind_display()}'
