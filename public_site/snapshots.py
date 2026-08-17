from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta

from django.templatetags.static import static
from django.utils import timezone

from pastoral.services.dates import fmt_hr_short, week_end_from, week_start_from
from pastoral.services.liturgical import LiturgicalService
from pastoral.services.mass_schedule import get_masses_for_date, normalize_schedule_entry


FORM_CARDS = (
    ('prijava-krsenje', 'Krštenje', 'Prijava djeteta za sakrament krštenja', 'Kap'),
    ('prijava-pricest', 'Prva pričest', 'Prijava prvopričesnika za pripravu', 'Kruh'),
    ('prijava-krizma', 'Krizma', 'Upis kandidata za svetu Potvrdu', 'Plamen'),
    ('prijava-ukop', 'Dogovor ukopa', 'Prvi podaci za dogovor pogreba', 'Križ'),
)


def _text(value, limit=500):
    return str(value or '').strip()[:limit]


def _safe_date(value):
    try:
        return date.fromisoformat(str(value or '')[:10])
    except ValueError:
        return None


def content_source_key(kind, raw):
    source = raw.get('id') or json.dumps(raw, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(f'{kind}:{source}'.encode('utf-8')).hexdigest()


def _publication_state(publications, kind, raw, preview):
    source_key = content_source_key(kind, raw)
    control = publications.get((kind, source_key))
    if control is None:
        return source_key, 'published', True, ''
    scheduled_for = (
        timezone.localtime(control.scheduled_for).strftime('%Y-%m-%dT%H:%M')
        if control.scheduled_for else ''
    )
    return source_key, control.status, preview or control.is_public_at(timezone.now()), scheduled_for


def _announcements(data, publications, preview=False):
    rows = []
    for raw in data.get('announcements') or []:
        if raw.get('public') is False:
            continue
        source_key, publication_status, is_visible, scheduled_for = _publication_state(
            publications, 'announcement', raw, preview,
        )
        if not is_visible:
            continue
        title = _text(raw.get('title'), 160)
        body = _text(raw.get('body'), 1200)
        if not title and not body:
            continue
        at = _text(raw.get('at'), 40)
        rows.append({
            'title': title or 'Župna obavijest',
            'body': body,
            'at': at,
            'date_label': fmt_hr_short(at[:10]) if _safe_date(at) else '',
            'source_key': source_key,
            'publication_status': publication_status,
            'scheduled_for': scheduled_for,
        })
    rows.sort(key=lambda row: row['at'], reverse=True)
    return rows[:6]


def _events(data, today, publications, preview=False):
    rows = []
    for raw in data.get('events') or []:
        if raw.get('public') is False or raw.get('type') == 'privatno':
            continue
        source_key, publication_status, is_visible, scheduled_for = _publication_state(
            publications, 'event', raw, preview,
        )
        if not is_visible:
            continue
        event_date = _safe_date(raw.get('date'))
        if not event_date:
            continue
        rows.append({
            'title': _text(raw.get('title'), 180),
            'date': event_date.isoformat(),
            'date_label': fmt_hr_short(event_date.isoformat()),
            'time': _text(raw.get('time'), 10),
            'place': _text(raw.get('place'), 160),
            'type': _text(raw.get('type'), 40),
            'is_past': event_date < today,
            'source_key': source_key,
            'publication_status': publication_status,
            'scheduled_for': scheduled_for,
        })
    rows.sort(key=lambda row: (row['date'], row['time']))
    upcoming = [row for row in rows if not row['is_past']][:6]
    recent = sorted(
        [row for row in rows if row['is_past']],
        key=lambda row: (row['date'], row['time']),
        reverse=True,
    )[:3]
    return upcoming or recent


def _mass_schedule(data):
    rows = []
    for raw in data.get('massSchedule') or []:
        item = normalize_schedule_entry(raw)
        rows.append({
            'day': _text(item.get('day'), 80),
            'time': _text(item.get('time'), 10),
            'location': _text(item.get('location'), 120),
            'notes': _text(item.get('notes'), 180),
        })
    return rows[:16]


def _today_masses(data, today):
    return [
        {
            'time': _text(row.get('time'), 10),
            'location': _text(row.get('location'), 120),
            'notes': _text(row.get('notes'), 180),
        }
        for row in get_masses_for_date(data, today.isoformat())
    ]


def _bulletins(data, today):
    issues = []
    for raw in data.get('zupniListicIssues') or []:
        issues.append({
            'title': _text(raw.get('title'), 180) or 'Župni listić',
            'week_start': _text(raw.get('weekStart'), 10),
            'week_end': _text(raw.get('weekEnd'), 10),
            'created_at': _text(raw.get('createdAt'), 40),
        })
    issues.sort(key=lambda item: item['created_at'], reverse=True)
    if issues:
        return issues[:4]
    start = week_start_from(today.isoformat())
    end = week_end_from(start)
    return [{
        'title': f'Župni tjedan {fmt_hr_short(start)} – {fmt_hr_short(end)}',
        'week_start': start,
        'week_end': end,
        'created_at': '',
        'generated': True,
    }]


def _liturgy(today):
    try:
        raw = LiturgicalService().get_day(today.isoformat())
    except Exception:
        return {}
    return {
        'title': _text(raw.get('title'), 200),
        'subtitle': _text(raw.get('subtitle') or raw.get('seasonLabel'), 160),
        'color': _text(raw.get('color'), 30).lower(),
        'color_label': _text(raw.get('colorLabel'), 80),
    }


def _website_media(website):
    rows = list(website.media.filter(is_visible=True).order_by('sort_order', 'created_at'))
    hero = next((item for item in rows if item.kind == 'hero'), None)
    gallery = [item for item in rows if item.kind == 'gallery']
    hero_payload = {
        'url': hero.image.url if hero else static('public_site/images/marija-hero.webp'),
        'alt': hero.alt_text if hero else 'Kip Blažene Djevice Marije u župnoj crkvi',
    }
    if gallery:
        gallery_payload = tuple({
            'url': item.image.url,
            'alt': _text(item.alt_text, 240),
            'caption': _text(item.caption, 240) or 'Fotografija iz života župe',
        } for item in gallery)
    else:
        gallery_payload = (
            {
                'url': static('public_site/images/marija-vitraj.webp'),
                'alt': 'Vitraj Blažene Djevice Marije',
                'caption': 'Marijanski vitraj u jutarnjem svjetlu',
            },
            {
                'url': static('public_site/images/marijanski-oltar.webp'),
                'alt': 'Marijanski oltar ukrašen cvijećem i svijećama',
                'caption': 'Marijanski oltar pripravljen za župno slavlje',
            },
        )
    return {'hero': hero_payload, 'gallery': gallery_payload}


def build_public_snapshot(website, *, configuration=None, preview=False):
    parish = website.parish
    data = parish.data or {}
    settings = parish.settings or {}
    configuration = configuration or {}
    value = lambda field: configuration.get(field, getattr(website, field))
    publications = {
        (item.kind, item.source_key): item
        for item in website.content_publications.all()
    }
    today = date.today()
    tomorrow = today + timedelta(days=1)
    return {
        'generated_at': datetime.now().astimezone(),
        'today': today,
        'tomorrow': tomorrow,
        'parish': {
            'name': _text(value('site_name'), 200),
            'tagline': _text(value('tagline'), 240),
            'about': _text(value('about_text'), 2400),
            'city': _text(settings.get('city'), 120),
            'diocese': _text(settings.get('diocese'), 200),
            'pastor': _text(settings.get('pastor'), 160),
            'logo_url': _text(settings.get('logoUrl'), 1000),
        },
        'contact': {
            'email': _text(value('contact_email'), 254),
            'phone': _text(value('phone'), 40),
            'address': _text(value('address'), 240),
            'office_hours': _text(value('office_hours'), 800),
            'confession_schedule': _text(value('confession_schedule'), 800),
            'map_url': _text(value('map_url'), 1000),
        },
        'donation': {
            'iban': _text(value('iban'), 34),
            'recipient': _text(value('donation_recipient'), 200),
            'purpose': _text(value('donation_purpose'), 240),
        },
        'social': {
            'facebook': _text(value('facebook_url'), 1000),
            'youtube': _text(value('youtube_url'), 1000),
            'instagram': _text(value('instagram_url'), 1000),
        },
        'media': _website_media(website),
        'liturgy': _liturgy(today),
        'today_masses': _today_masses(data, today),
        'mass_schedule': _mass_schedule(data),
        'announcements': _announcements(data, publications, preview),
        'events': _events(data, today, publications, preview),
        'bulletins': _bulletins(data, today),
        'forms': FORM_CARDS,
        'enabled_sections': set(value('enabled_sections') or []),
        'is_preview': preview,
    }
