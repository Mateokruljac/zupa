from django import template
from django.urls import reverse
import json

register = template.Library()


@register.filter
def get_item(mapping, key):
    if mapping is None:
        return None
    if isinstance(mapping, dict):
        return mapping.get(key)
    return getattr(mapping, key, None)


@register.filter
def hr_date(value):
    if not value:
        return '—'
    if isinstance(value, dict):
        return '—'
    try:
        from datetime import date
        if isinstance(value, str):
            parts = value.split('-')
            d = date(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            d = value
        months = ['sij', 'velj', 'ožu', 'tra', 'svi', 'lip', 'srp', 'kol', 'ruj', 'lis', 'stu', 'pro']
        return f"{d.day}. {months[d.month - 1]} {d.year}."
    except (ValueError, IndexError, TypeError, AttributeError):
        return str(value)


@register.filter
def hr_datetime(value):
    if not value:
        return '—'
    try:
        from datetime import datetime
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
        return dt.strftime('%d.%m.%Y. %H:%M')
    except (ValueError, TypeError, AttributeError):
        return str(value)


@register.filter
def money_eur(value):
    try:
        return f'{float(value):.2f} €'
    except (TypeError, ValueError):
        return '—'



@register.filter
def to_json(value):
    return json.dumps(value, ensure_ascii=False)


@register.filter
def lit_color_class(color):
    c = (color or '').lower()
    if c in ('purple', 'violet', 'purpura'):
        return 'cal-cell--lit-violet'
    if c == 'white':
        return 'cal-cell--lit-white'
    if c == 'red':
        return 'cal-cell--lit-red'
    if c == 'rose':
        return 'cal-cell--lit-rose'
    return 'cal-cell--lit-green'


@register.filter
def lit_swatch_class(color):
    c = (color or '').lower()
    if c in ('purple', 'violet', 'purpura'):
        return 'lit-color--violet'
    if c == 'white':
        return 'lit-color--white'
    if c == 'red':
        return 'lit-color--red'
    if c == 'rose':
        return 'lit-color--rose'
    return 'lit-color--green'


_MONTHS_HR = (
    'Siječanj', 'Veljača', 'Ožujak', 'Travanj', 'Svibanj', 'Lipanj',
    'Srpanj', 'Kolovoz', 'Rujan', 'Listopad', 'Studeni', 'Prosinac',
)


@register.filter
def hr_month(value):
    try:
        return _MONTHS_HR[int(value) - 1]
    except (ValueError, IndexError, TypeError):
        return value


_FIELD_LABELS = {
    'ime_prezime': 'Ime i prezime',
    'ime_djeteta': 'Ime djeteta',
    'datum_rodjenja': 'Datum rođenja',
    'datum_krstenja': 'Datum krštenja',
    'datum_potvrde': 'Datum potvrde',
    'datum_vjencanja': 'Datum vjenčanja',
    'datum_pogreba': 'Datum pogreba',
    'datum_smrti': 'Datum smrti',
    'datum_sastanka': 'Datum sastanka',
    'datum_pricesti': 'Datum prve pričesti',
    'datum_uplate': 'Datum uplate',
    'datum_mise': 'Datum mise',
    'tjedan_od': 'Tjedan od (ponedjeljak)',
    'maticni_broj': 'Matični broj',
    'roditelji': 'Roditelji',
    'kumovi': 'Kum(ovi)',
    'kum': 'Kum/ka',
    'mladenci': 'Mladenci',
    'svjedoci': 'Svjedoci',
    'pokojnik': 'Pokojnik',
    'groblje': 'Groblje',
    'obitelj': 'Obitelj',
    'adresa': 'Adresa',
    'iznos': 'Iznos (€)',
    'platitelj': 'Platitelj',
    'svrha': 'Svrha uplate',
    'broj_racuna': 'Broj računa',
    'namjera': 'Namjera',
    'vrijeme_mise': 'Vrijeme mise',
    'narucitelj': 'Naručitelj',
    'stipendij': 'Stipendij (€)',
    'skupina': 'Skupina / godina',
    'program_sadrzaj': 'Program i aktivnosti',
    'prisutni': 'Prisutni',
    'dnevni_red': 'Dnevni red',
    'zakljucci': 'Zaključci',
    'stanje_zupe': 'Stanje župe',
    'preporuke': 'Preporuke',
    'zupnik': 'Župnik',
    'zupa': 'Župa',
    'godina': 'Godina',
    'danas': 'Danas',
}

_FIELD_TEXTAREA = frozenset({
    'dnevni_red', 'zakljucci', 'stanje_zupe', 'preporuke', 'program_sadrzaj', 'prisutni', 'svrha', 'namjera',
})

_FIELD_NUMBER = frozenset({'iznos', 'stipendij'})

_FIELD_DATE_PREFIX = 'datum_'

_DOC_CATEGORY_LABELS = {
    'krizma': 'Krizma',
    'krsenje': 'Krštenje',
    'nakane': 'Misne nakane',
    'ured': 'Župni ured',
    'pastoral': 'Pastoral',
    'vjenčanje': 'Vjenčanje',
    'vjencanje': 'Vjenčanje',
    'prva-pricest': 'Prva pričest',
    'pogreb': 'Pogrebi',
    'lukno': 'Lukno',
    'financije': 'Financije',
    'ostalo': 'Ostalo',
}


@register.filter
def field_label(key):
    if not key:
        return ''
    return _FIELD_LABELS.get(key, str(key).replace('_', ' ').capitalize())


@register.filter
def field_widget_type(key):
    if not key:
        return 'text'
    if key in _FIELD_NUMBER:
        return 'number'
    if key in _FIELD_TEXTAREA:
        return 'textarea'
    if key.startswith(_FIELD_DATE_PREFIX) or key == 'tjedan_od':
        return 'date'
    return 'text'


@register.filter
def field_is_wide(key):
    return field_widget_type(key) == 'textarea'


@register.filter
def field_placeholder(key):
    wtype = field_widget_type(key)
    if wtype == 'date':
        return 'YYYY-MM-DD ili 15. lip 2026.'
    if wtype == 'number':
        return '0,00'
    placeholders = {
        'zupnik': 'npr. fra Ivan Horvat',
        'zupa': 'npr. Sv. Ante Padovanski',
        'maticni_broj': 'npr. 42/2024',
        'roditelji': 'Ime i prezime roditelja',
        'kumovi': 'Ime i prezime kumova',
    }
    return placeholders.get(key, '')


@register.filter
def field_date_value(value):
    """Vrijednost za type=date — samo ISO YYYY-MM-DD."""
    if not value or not isinstance(value, str):
        return ''
    v = value.strip()
    if len(v) >= 10 and v[4] == '-' and v[7] == '-':
        try:
            int(v[:4])
            int(v[5:7])
            int(v[8:10])
            return v[:10]
        except ValueError:
            return ''
    return ''


@register.simple_tag
def doc_field_value(field, prefill=None, defaults=None):
    if isinstance(prefill, dict):
        val = prefill.get(field)
        if val not in (None, ''):
            return val
    if isinstance(defaults, dict):
        return defaults.get(field, '') or ''
    return ''


@register.filter
def doc_category_label(cat_id):
    if not cat_id:
        return 'Ostalo'
    return _DOC_CATEGORY_LABELS.get(cat_id, str(cat_id).replace('-', ' ').capitalize())


@register.filter
def debt_cat_label(cat_id, direction='receivable'):
    from pastoral.services.debts import cat_meta
    return cat_meta(cat_id, direction).get('label', cat_id)


@register.simple_tag
def page_url(page):
    if page in ('dashboard', 'app'):
        return reverse('pastoral:app')
    if page == 'login':
        return reverse('pastoral:login')
    if page.startswith('public/'):
        slug = page.replace('public/', '').replace('.html', '')
        if slug == 'index':
            return reverse('pastoral:public_index')
        return reverse('pastoral:public_form', kwargs={'form': slug})
    slug = page.replace('pages/', '').replace('.html', '')
    return reverse('pastoral:page', kwargs={'page': slug})


@register.simple_tag
def reminder_link(href):
    """URL za podsjetnik — slug s opcionalnim query stringom."""
    if not href:
        return reverse('pastoral:app')
    if '?' in href:
        slug, qs = href.split('?', 1)
        return f"{reverse('pastoral:page', kwargs={'page': slug})}?{qs}"
    return reverse('pastoral:page', kwargs={'page': href})
