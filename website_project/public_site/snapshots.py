from copy import deepcopy
from datetime import date, datetime, timedelta

from django.templatetags.static import static


DEFAULT_ENABLED_SECTIONS = {
    'announcements',
    'mass_schedule',
    'calendar',
    'bulletin',
    'donations',
}


def _text(value, limit=500):
    return str(value or '').strip()[:limit]


def _website_media(website):
    media_items = list(
        website.media.filter(is_visible=True).order_by('sort_order', 'created_at')
    )
    hero_image = next(
        (media_item for media_item in media_items if media_item.kind == 'hero'),
        None,
    )
    gallery_images = [
        media_item for media_item in media_items if media_item.kind == 'gallery'
    ]
    hero_payload = {
        'url': (
            hero_image.image.url
            if hero_image
            else static('public_site/images/marija-hero.webp')
        ),
        'alt': (
            hero_image.alt_text
            if hero_image
            else 'Naslovna fotografija župne zajednice'
        ),
    }
    if gallery_images:
        gallery_payload = tuple({
            'url': gallery_image.image.url,
            'alt': _text(gallery_image.alt_text, 240),
            'caption': (
                _text(gallery_image.caption, 240)
                or 'Fotografija iz života župe'
            ),
        } for gallery_image in gallery_images)
    else:
        gallery_payload = (
            {
                'url': static('public_site/images/marija-vitraj.webp'),
                'alt': 'Vitraj Blažene Djevice Marije',
                'caption': 'Marijanski vitraj',
            },
            {
                'url': static('public_site/images/marijanski-oltar.webp'),
                'alt': 'Marijanski oltar',
                'caption': 'Marijanski oltar',
            },
        )
    return {'hero': hero_payload, 'gallery': gallery_payload}


def build_public_snapshot(website, *, preview=False):
    published_snapshot = deepcopy(website.published_snapshot or {})
    parish_payload = published_snapshot.setdefault('parish', {})
    parish_payload.update({
        'name': website.site_name,
        'tagline': website.tagline,
        'about': website.about_text,
    })
    published_snapshot['contact'] = {
        **published_snapshot.get('contact', {}),
        'email': website.contact_email,
        'phone': website.phone,
        'address': website.address,
        'office_hours': website.office_hours,
        'confession_schedule': website.confession_schedule,
        'map_url': website.map_url,
    }
    published_snapshot['donation'] = {
        'iban': website.iban,
        'recipient': website.donation_recipient,
        'purpose': website.donation_purpose,
    }
    published_snapshot['social'] = {
        'facebook': website.facebook_url,
        'youtube': website.youtube_url,
        'instagram': website.instagram_url,
    }
    published_snapshot['media'] = _website_media(website)
    published_snapshot['generated_at'] = datetime.now().astimezone()
    published_snapshot['today'] = date.today()
    published_snapshot['tomorrow'] = date.today() + timedelta(days=1)
    published_snapshot['liturgy'] = published_snapshot.get('liturgy', {})
    published_snapshot['today_masses'] = published_snapshot.get('today_masses', [])
    published_snapshot['mass_schedule'] = published_snapshot.get('mass_schedule', [])
    published_snapshot['announcements'] = published_snapshot.get('announcements', [])
    published_snapshot['events'] = published_snapshot.get('events', [])
    published_snapshot['bulletins'] = published_snapshot.get('bulletins', [])
    published_snapshot['forms'] = published_snapshot.get('forms', [])
    published_snapshot['enabled_sections'] = set(
        website.enabled_sections or DEFAULT_ENABLED_SECTIONS
    )
    published_snapshot['is_preview'] = preview
    return published_snapshot
