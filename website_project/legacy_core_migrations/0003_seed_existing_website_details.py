from django.db import migrations


ABOUT = (
    'Župa je zajednica vjere, molitve i susreta. '
    'Ovdje pronađite aktualne obavijesti, raspored svetih misa, '
    'događanja i način kako se uključiti u život naše zajednice.'
)


def seed_existing_websites(apps, schema_editor):
    ParishWebsite = apps.get_model('public_site', 'ParishWebsite')
    for website in ParishWebsite.objects.select_related('parish'):
        parish_settings = website.parish.settings or {}
        changed = []
        defaults = {
            'about_text': ABOUT,
            'contact_email': parish_settings.get('email') or '',
            'phone': parish_settings.get('phone') or '',
            'address': parish_settings.get('address') or parish_settings.get('city') or '',
            'office_hours': 'Ponedjeljak – petak: 9:00 – 12:00\nNakon večernje mise prema dogovoru',
            'confession_schedule': 'Pola sata prije svete mise ili prema dogovoru.',
            'donation_recipient': parish_settings.get('name') or website.site_name,
            'donation_purpose': 'Dar za potrebe župe',
        }
        for field, value in defaults.items():
            if not getattr(website, field):
                setattr(website, field, value)
                changed.append(field)
        if changed:
            website.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ('public_site', '0002_parishwebsite_about_text_parishwebsite_address_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_existing_websites, migrations.RunPython.noop),
    ]
