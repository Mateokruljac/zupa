"""Postojeće darove za crkvu pretvara u zasebne retke kategorije obiteljski_dar."""

from django.db import migrations


def split_church_donations(apps, schema_editor):
    HouseholdContribution = apps.get_model('zupa_vjernici', 'HouseholdContribution')
    for contribution in HouseholdContribution.objects.all():
        donation = contribution.church_donation or 0
        if donation <= 0:
            continue
        public_identifier = f'{contribution.public_identifier}-dar'
        HouseholdContribution.objects.update_or_create(
            household_id=contribution.household_id,
            public_identifier=public_identifier,
            defaults={
                'year': contribution.year,
                'category': 'obiteljski_dar',
                'lukno_paid': False,
                'lukno_amount': donation,
                'lukno_paid_at': contribution.donation_date,
                'church_donation': 0,
                'donation_date': None,
                'notes': contribution.notes or '',
            },
        )
        contribution.church_donation = 0
        contribution.donation_date = None
        contribution.category = contribution.category or 'lukno'
        contribution.save(
            update_fields=['church_donation', 'donation_date', 'category'],
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('zupa_vjernici', '0003_alter_householdcontribution_options_and_more'),
    ]

    operations = [
        migrations.RunPython(split_church_donations, noop_reverse),
    ]
