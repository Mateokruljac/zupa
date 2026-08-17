from io import BytesIO

from PIL import Image, ImageOps

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from control_plane.models import ControlPlaneAuditEvent, LicenseEntitlement
from control_plane.services.licenses import LicenseAccess, current_license_for, evaluate_license

from .models import ParishWebsite, ParishWebsiteMedia, PublicContentPublication, WebsiteBuild


DEFAULT_SECTIONS = [
    'hero', 'mass_schedule', 'announcements', 'calendar',
    'sacraments', 'bulletin', 'donations', 'contact',
]

WEBSITE_CONFIGURATION_FIELDS = (
    'site_name', 'tagline', 'about_text', 'template_key', 'primary_color',
    'accent_color', 'contact_email', 'phone', 'address', 'office_hours',
    'confession_schedule', 'iban', 'donation_recipient', 'donation_purpose',
    'map_url', 'facebook_url', 'youtube_url', 'instagram_url', 'custom_domain',
    'enabled_sections',
)


def website_configuration(website):
    return {field: getattr(website, field) for field in WEBSITE_CONFIGURATION_FIELDS}


def website_for(parish):
    return ParishWebsite.objects.filter(parish=parish).first()


def _optimized_website_image(uploaded, kind):
    uploaded.seek(0)
    with Image.open(uploaded) as source:
        image = ImageOps.exif_transpose(source)
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        elif image.mode == 'RGBA':
            background = Image.new('RGB', image.size, 'white')
            background.paste(image, mask=image.getchannel('A'))
            image = background
        max_size = (1920, 1280) if kind == ParishWebsiteMedia.Kind.HERO else (1600, 1600)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        width, height = image.size
        output = BytesIO()
        image.save(output, 'WEBP', quality=84, method=6)
    payload = output.getvalue()
    return ContentFile(payload, name='website-image.webp'), width, height, len(payload)


@transaction.atomic
def save_website_media(*, website, actor, kind, uploaded, alt_text, caption=''):
    if kind not in ParishWebsiteMedia.Kind.values:
        raise ValueError('Nepoznata vrsta fotografije.')
    if kind == ParishWebsiteMedia.Kind.GALLERY and website.media.filter(kind=kind).count() >= 12:
        raise ValueError('Galerija može sadržavati najviše 12 fotografija.')

    optimized, width, height, file_size = _optimized_website_image(uploaded, kind)
    old_hero = None
    if kind == ParishWebsiteMedia.Kind.HERO:
        old_hero = website.media.filter(kind=kind).first()
    next_order = website.media.filter(kind=kind).count()
    media = ParishWebsiteMedia(
        website=website,
        kind=kind,
        alt_text=(alt_text or '').strip()[:240],
        caption=(caption or '').strip()[:240],
        sort_order=next_order,
        width=width,
        height=height,
        file_size=file_size,
        created_by=actor,
    )
    media.image.save('website-image.webp', optimized, save=False)
    media.save()

    if old_hero:
        old_name = old_hero.image.name
        storage = old_hero.image.storage
        old_hero.delete()
        transaction.on_commit(lambda: storage.delete(old_name))

    ControlPlaneAuditEvent.objects.create(
        parish=website.parish,
        actor=actor,
        event_type='public_website.media_uploaded',
        target_type='public_site.ParishWebsiteMedia',
        target_id=str(media.pk),
        metadata={'kind': kind, 'width': width, 'height': height, 'file_size': file_size},
    )
    return media


@transaction.atomic
def delete_website_media(*, website, actor, media_id):
    media = website.media.filter(pk=media_id).first()
    if media is None:
        return False
    target_id = str(media.pk)
    kind = media.kind
    image_name = media.image.name
    storage = media.image.storage
    media.delete()
    ControlPlaneAuditEvent.objects.create(
        parish=website.parish,
        actor=actor,
        event_type='public_website.media_deleted',
        target_type='public_site.ParishWebsiteMedia',
        target_id=target_id,
        metadata={'kind': kind},
    )
    transaction.on_commit(lambda: storage.delete(image_name))
    return True


@transaction.atomic
def activate_public_website(*, parish, actor):
    grant = current_license_for(parish)
    if evaluate_license(grant) != LicenseAccess.FULL:
        raise PermissionDenied('Za aktivaciju je potrebna aktivna licenca župe.')

    auto_activate = settings.PUBLIC_WEBSITE_DEMO_AUTO_ACTIVATE
    if not auto_activate:
        raise PermissionDenied('Zahtjev je zaprimljen i čeka potvrdu administratora.')

    entitlement, _ = LicenseEntitlement.objects.update_or_create(
        grant=grant,
        code='public_website',
        defaults={
            'enabled': True,
            'configuration': {
                'billing': 'annual_add_on',
                'demo_auto_activation': True,
                'activated_at': timezone.now().isoformat(),
            },
        },
    )
    parish_settings = parish.settings or {}
    website, created = ParishWebsite.objects.get_or_create(
        parish=parish,
        defaults={
            'subdomain': parish.slug,
            'site_name': parish_settings.get('name') or str(parish),
            'tagline': 'Dobro došli u našu župnu zajednicu',
            'about_text': (
                'Župa je zajednica vjere, molitve i susreta. '
                'Ovdje pronađite aktualne informacije i način kako nam se pridružiti.'
            ),
            'primary_color': parish_settings.get('primaryColor') or '#5c2e3a',
            'accent_color': parish_settings.get('accentColor') or '#b8922a',
            'contact_email': parish_settings.get('email') or '',
            'phone': parish_settings.get('phone') or '',
            'address': parish_settings.get('address') or parish_settings.get('city') or '',
            'office_hours': 'Ponedjeljak – petak: 9:00 – 12:00\nNakon večernje mise prema dogovoru',
            'confession_schedule': 'Pola sata prije svete mise ili prema dogovoru.',
            'iban': '',
            'donation_recipient': parish_settings.get('name') or str(parish),
            'donation_purpose': 'Dar za potrebe župe',
            'enabled_sections': DEFAULT_SECTIONS,
            'requested_by': actor,
            'activated_at': timezone.now(),
        },
    )
    build = website.builds.filter(status=WebsiteBuild.Status.RUNNING).first()
    if build is None and website.status == ParishWebsite.Status.PROVISIONING:
        build = WebsiteBuild.objects.create(
            website=website,
            kind=WebsiteBuild.Kind.INITIAL,
            status=WebsiteBuild.Status.RUNNING,
            progress=35,
            requested_by=actor,
            started_at=timezone.now(),
            metadata={
                'demo': True,
                'steps_completed': ['entitlement', 'subdomain', 'template'],
            },
        )
    if created:
        ControlPlaneAuditEvent.objects.create(
            parish=parish,
            actor=actor,
            event_type='public_website.demo_auto_activated',
            target_type='public_site.ParishWebsite',
            target_id=str(website.pk),
            metadata={
                'entitlement_id': str(entitlement.pk),
                'build_id': str(build.pk) if build else '',
            },
        )
    return website, build


@transaction.atomic
def complete_demo_build(*, website, actor):
    build = website.builds.filter(status=WebsiteBuild.Status.RUNNING).first()
    if build:
        build.status = WebsiteBuild.Status.SUCCEEDED
        build.progress = 100
        build.finished_at = timezone.now()
        build.metadata = {**build.metadata, 'demo_completed': True}
        build.save(update_fields=('status', 'progress', 'finished_at', 'metadata'))
    website.status = ParishWebsite.Status.DRAFT
    website.save(update_fields=('status', 'updated_at'))
    ControlPlaneAuditEvent.objects.create(
        parish=website.parish,
        actor=actor,
        event_type='public_website.demo_build_completed',
        target_type='public_site.ParishWebsite',
        target_id=str(website.pk),
    )
    return website


@transaction.atomic
def publish_demo_website(*, website, actor):
    now = timezone.now()
    WebsiteBuild.objects.create(
        website=website,
        kind=WebsiteBuild.Kind.PUBLISH,
        status=WebsiteBuild.Status.SUCCEEDED,
        progress=100,
        requested_by=actor,
        started_at=now,
        finished_at=now,
        metadata={'demo': True, 'static_snapshot': True},
    )
    website.status = ParishWebsite.Status.LIVE
    website.published_at = now
    website.publication_status = ParishWebsite.PublicationStatus.PUBLISHED
    website.published_configuration = website_configuration(website)
    website.save(update_fields=(
        'status', 'published_at', 'publication_status',
        'published_configuration', 'updated_at',
    ))
    ControlPlaneAuditEvent.objects.create(
        parish=website.parish,
        actor=actor,
        event_type='public_website.demo_published',
        target_type='public_site.ParishWebsite',
        target_id=str(website.pk),
    )
    return website


@transaction.atomic
def update_content_publication(
    *, website, actor, kind, source_key, source_label, status, scheduled_for=None,
):
    if kind not in PublicContentPublication.Kind.values:
        raise ValueError('Nepoznata vrsta javnog sadržaja.')
    if status not in PublicContentPublication.Status.values:
        raise ValueError('Nepoznat status objave.')
    if status == PublicContentPublication.Status.SCHEDULED and scheduled_for is None:
        raise ValueError('Za zakazanu objavu potrebno je odabrati datum i vrijeme.')
    if (
        status == PublicContentPublication.Status.SCHEDULED
        and scheduled_for <= timezone.now()
    ):
        raise ValueError('Vrijeme zakazane objave mora biti u budućnosti.')
    if status != PublicContentPublication.Status.SCHEDULED:
        scheduled_for = None
    publication, _ = PublicContentPublication.objects.update_or_create(
        website=website,
        kind=kind,
        source_key=source_key,
        defaults={
            'source_label': (source_label or '').strip()[:200],
            'status': status,
            'scheduled_for': scheduled_for,
            'updated_by': actor,
        },
    )
    ControlPlaneAuditEvent.objects.create(
        parish=website.parish,
        actor=actor,
        event_type='public_website.content_publication_updated',
        target_type='public_site.PublicContentPublication',
        target_id=str(publication.pk),
        metadata={'kind': kind, 'status': status, 'scheduled_for': scheduled_for.isoformat() if scheduled_for else ''},
    )
    return publication


@transaction.atomic
def reset_demo_website(*, parish, actor):
    if not settings.PUBLIC_WEBSITE_DEMO_AUTO_ACTIVATE:
        raise PermissionDenied('Reset je dostupan samo u demo načinu.')
    website = website_for(parish)
    target_id = str(website.pk) if website else ''
    if website:
        media_files = [
            (item.image.storage, item.image.name)
            for item in website.media.all()
            if item.image.name
        ]
        website.builds.all().delete()
        website.delete()
        for storage, image_name in media_files:
            transaction.on_commit(lambda storage=storage, name=image_name: storage.delete(name))
    grant = current_license_for(parish)
    if grant:
        LicenseEntitlement.objects.filter(
            grant=grant,
            code='public_website',
        ).delete()
    ControlPlaneAuditEvent.objects.create(
        parish=parish,
        actor=actor,
        event_type='public_website.demo_reset',
        target_type='public_site.ParishWebsite',
        target_id=target_id,
    )
