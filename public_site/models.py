import uuid

from django.conf import settings
from django.db import models


def website_media_upload_to(instance, _filename):
    return (
        f'public-sites/{instance.website.parish.tenant_id}/'
        f'{instance.website_id}/{uuid.uuid4().hex}.webp'
    )


class ParishWebsite(models.Model):
    class PublicationStatus(models.TextChoices):
        DRAFT = 'draft', 'Skica'
        SCHEDULED = 'scheduled', 'Zakazano'
        PUBLISHED = 'published', 'Objavljeno'

    class Status(models.TextChoices):
        PROVISIONING = 'provisioning', 'Izrada u tijeku'
        DRAFT = 'draft', 'Skica spremna'
        LIVE = 'live', 'Objavljeno'
        SUSPENDED = 'suspended', 'Privremeno obustavljeno'
        ARCHIVED = 'archived', 'Arhivirano'

    class Template(models.TextChoices):
        CLASSIC = 'classic', 'Klasični'
        WARM = 'warm', 'Topli pastoralni'
        MODERN = 'modern', 'Suvremeni'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parish = models.OneToOneField(
        'pastoral.Parish',
        on_delete=models.PROTECT,
        related_name='public_website',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROVISIONING,
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
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requested_public_websites',
    )
    activated_at = models.DateTimeField()
    published_at = models.DateTimeField(null=True, blank=True)
    publication_status = models.CharField(
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    published_configuration = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('parish',)
        verbose_name = 'Javna web-stranica župe'
        verbose_name_plural = 'Javne web-stranice župa'

    def __str__(self):
        return f'{self.parish} · {self.get_status_display()}'

    @property
    def public_hostname(self):
        return self.custom_domain or f'{self.subdomain}.zupa.test'


class PublicContentPublication(models.Model):
    class Kind(models.TextChoices):
        ANNOUNCEMENT = 'announcement', 'Obavijest'
        EVENT = 'event', 'Događanje'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Skica'
        SCHEDULED = 'scheduled', 'Zakazano'
        PUBLISHED = 'published', 'Objavljeno'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(
        ParishWebsite,
        on_delete=models.CASCADE,
        related_name='content_publications',
    )
    kind = models.CharField(max_length=20, choices=Kind.choices, db_index=True)
    source_key = models.CharField(max_length=64)
    source_label = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_public_content_publications',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('kind', 'source_label')
        verbose_name = 'Kontrola javne objave'
        verbose_name_plural = 'Kontrole javnih objava'
        constraints = (
            models.UniqueConstraint(
                fields=('website', 'kind', 'source_key'),
                name='public_site_unique_content_publication',
            ),
        )

    def __str__(self):
        return f'{self.website.parish} · {self.get_kind_display()} · {self.source_label}'

    def is_public_at(self, moment):
        if self.status == self.Status.PUBLISHED:
            return True
        return (
            self.status == self.Status.SCHEDULED
            and self.scheduled_for is not None
            and self.scheduled_for <= moment
        )


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
        on_delete=models.PROTECT,
        related_name='uploaded_public_website_media',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('kind', 'sort_order', 'created_at')
        verbose_name = 'Fotografija javne web-stranice'
        verbose_name_plural = 'Fotografije javnih web-stranica'

    def __str__(self):
        return f'{self.website.parish} · {self.get_kind_display()}'


class WebsiteBuild(models.Model):
    class Kind(models.TextChoices):
        INITIAL = 'initial', 'Početna izrada'
        PREVIEW = 'preview', 'Izrada pregleda'
        PUBLISH = 'publish', 'Objava'

    class Status(models.TextChoices):
        QUEUED = 'queued', 'Zakazano'
        RUNNING = 'running', 'U tijeku'
        SUCCEEDED = 'succeeded', 'Dovršeno'
        FAILED = 'failed', 'Neuspješno'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(
        ParishWebsite,
        on_delete=models.PROTECT,
        related_name='builds',
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(max_length=16, choices=Status.choices, db_index=True)
    progress = models.PositiveSmallIntegerField(default=0)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requested_website_builds',
    )
    metadata = models.JSONField(default=dict, blank=True)
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-queued_at',)
        verbose_name = 'Izrada javne web-stranice'
        verbose_name_plural = 'Izrade javnih web-stranica'
        constraints = (
            models.CheckConstraint(
                condition=models.Q(progress__gte=0, progress__lte=100),
                name='public_site_build_progress_range',
            ),
        )

    def __str__(self):
        return f'{self.website.parish} · {self.get_kind_display()} · {self.get_status_display()}'
