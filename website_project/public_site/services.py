from io import BytesIO

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps

from .models import ParishWebsite, ParishWebsiteMedia


def website_for(parish_identifier):
    return ParishWebsite.objects.filter(
        parish_identifier=parish_identifier,
    ).first()


@transaction.atomic
def publish_website(website):
    website.status = ParishWebsite.Status.LIVE
    website.published_at = timezone.now()
    website.save(update_fields=('status', 'published_at', 'updated_at'))
    return website


@transaction.atomic
def save_website_media(*, website, actor, kind, uploaded, alt_text, caption):
    uploaded.seek(0)
    with Image.open(uploaded) as source_image:
        source_image.load()
        normalized_image = ImageOps.exif_transpose(source_image).convert('RGB')
        normalized_image.thumbnail((2400, 1600), Image.Resampling.LANCZOS)
        output = BytesIO()
        normalized_image.save(output, format='WEBP', quality=84, method=6)
        width, height = normalized_image.size
    output_bytes = output.getvalue()
    media_item = ParishWebsiteMedia(
        website=website,
        kind=kind,
        alt_text=(alt_text or '').strip(),
        caption=(caption or '').strip(),
        width=width,
        height=height,
        file_size=len(output_bytes),
        created_by=actor,
    )
    media_item.image.save('upload.webp', ContentFile(output_bytes), save=False)
    media_item.save()
    return media_item
