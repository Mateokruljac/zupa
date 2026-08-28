# Tipizirana obitelj / posjete + nested modeli + backfill iz payload-a.

import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

import django.db.models.deletion
from django.db import migrations, models


def _parse_iso_date(value):
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _decimal_amount(value):
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def backfill_households_and_visits(apps, schema_editor):
    Household = apps.get_model('zupa_vjernici', 'Household')
    HouseholdMember = apps.get_model('zupa_vjernici', 'HouseholdMember')
    HouseholdContribution = apps.get_model('zupa_vjernici', 'HouseholdContribution')
    HouseholdRelative = apps.get_model('zupa_vjernici', 'HouseholdRelative')
    PastoralVisit = apps.get_model('zupa_vjernici', 'PastoralVisit')

    for household in Household.objects.all().iterator():
        payload = household.payload or {}
        household.preferred_mass = str(payload.get('preferredMass') or '')
        household.pastoral_notes = str(payload.get('pastoralNotes') or '')
        household.origin_place = str(payload.get('originPlace') or '')
        household.last_visit_on = _parse_iso_date(payload.get('lastVisit'))
        household.tags = (
            list(payload.get('tags') or [])
            if isinstance(payload.get('tags'), list)
            else []
        )
        household.husband = (
            dict(payload.get('husband') or {})
            if isinstance(payload.get('husband'), dict)
            else {}
        )
        household.wife = (
            dict(payload.get('wife') or {})
            if isinstance(payload.get('wife'), dict)
            else {}
        )
        if not household.surname:
            household.surname = str(payload.get('surname') or '')
        if not household.street_public_identifier:
            household.street_public_identifier = str(payload.get('streetId') or '')
        if not household.address:
            household.address = str(payload.get('address') or '')
        if not household.phone:
            household.phone = str(payload.get('phone') or '')
        if not household.email:
            household.email = str(payload.get('email') or '')
        if not household.status:
            household.status = str(payload.get('status') or 'aktivna')
        household.payload = {}
        household.save()

        for index, member_record in enumerate(payload.get('members') or []):
            if not isinstance(member_record, dict):
                continue
            public_identifier = str(
                member_record.get('id')
                or f'm-{household.public_identifier}-{index + 1}'
            )
            HouseholdMember.objects.update_or_create(
                household=household,
                public_identifier=public_identifier,
                defaults={
                    'name': str(member_record.get('name') or ''),
                    'birth_year': str(member_record.get('birthYear') or ''),
                    'relation': str(member_record.get('relation') or ''),
                    'sacraments': list(member_record.get('sacraments') or [])
                    if isinstance(member_record.get('sacraments'), list)
                    else [],
                    'roles': list(member_record.get('roles') or [])
                    if isinstance(member_record.get('roles'), list)
                    else [],
                    'notes': str(member_record.get('notes') or ''),
                    'sort_order': index,
                },
            )

        for index, contribution_record in enumerate(
            payload.get('contributions') or []
        ):
            if not isinstance(contribution_record, dict):
                continue
            public_identifier = str(
                contribution_record.get('id')
                or f'yc-{household.public_identifier}-{index + 1}'
            )
            year_raw = contribution_record.get('year')
            try:
                year_value = int(year_raw) if year_raw not in (None, '') else 0
            except (TypeError, ValueError):
                year_value = 0
            HouseholdContribution.objects.update_or_create(
                household=household,
                public_identifier=public_identifier,
                defaults={
                    'year': year_value,
                    'lukno_paid': bool(contribution_record.get('luknoPaid')),
                    'lukno_amount': _decimal_amount(
                        contribution_record.get('luknoAmount')
                    ),
                    'lukno_paid_at': _parse_iso_date(
                        contribution_record.get('luknoPaidAt')
                    ),
                    'church_donation': _decimal_amount(
                        contribution_record.get('churchDonation')
                    ),
                    'donation_date': _parse_iso_date(
                        contribution_record.get('donationDate')
                    ),
                    'notes': str(contribution_record.get('notes') or ''),
                },
            )

        for index, relative_record in enumerate(payload.get('relatives') or []):
            if not isinstance(relative_record, dict):
                continue
            public_identifier = str(
                relative_record.get('id')
                or f'rel-{household.public_identifier}-{index + 1}'
            )
            HouseholdRelative.objects.update_or_create(
                household=household,
                public_identifier=public_identifier,
                defaults={
                    'name': str(relative_record.get('name') or ''),
                    'relation': str(relative_record.get('relation') or ''),
                    'birth_year': str(relative_record.get('birthYear') or ''),
                    'notes': str(relative_record.get('notes') or ''),
                    'sort_order': index,
                },
            )

    for visit in PastoralVisit.objects.all().iterator():
        payload = visit.payload or {}
        visit.visit_type = str(payload.get('type') or '')
        visit.person_name = str(payload.get('person') or '')
        visit.address = str(payload.get('address') or '')
        visit.priest = str(payload.get('priest') or '')
        visit.purpose = str(payload.get('purpose') or '')
        visit.report = str(payload.get('report') or '')
        if not visit.family_public_identifier:
            visit.family_public_identifier = str(payload.get('familyId') or '')
        if visit.scheduled_on is None:
            visit.scheduled_on = _parse_iso_date(payload.get('scheduled'))
        if not visit.is_done:
            visit.is_done = bool(payload.get('done'))
        visit.payload = {}
        visit.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('zupa_vjernici', '0003_clear_street_payload'),
    ]

    operations = [
        migrations.AddField(
            model_name='household',
            name='husband',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='household',
            name='last_visit_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='household',
            name='origin_place',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='household',
            name='pastoral_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='household',
            name='preferred_mass',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='household',
            name='tags',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='household',
            name='wife',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='pastoralvisit',
            name='address',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='pastoralvisit',
            name='person_name',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='pastoralvisit',
            name='priest',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='pastoralvisit',
            name='purpose',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='pastoralvisit',
            name='report',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='pastoralvisit',
            name='visit_type',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.CreateModel(
            name='HouseholdContribution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('public_identifier', models.CharField(db_index=True, max_length=64)),
                ('year', models.PositiveIntegerField(db_index=True, default=0)),
                ('lukno_paid', models.BooleanField(default=False)),
                ('lukno_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('lukno_paid_at', models.DateField(blank=True, null=True)),
                ('church_donation', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('donation_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contributions', to='zupa_vjernici.household')),
            ],
            options={
                'ordering': ['-year'],
                'unique_together': {('household', 'public_identifier')},
            },
        ),
        migrations.CreateModel(
            name='HouseholdMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('public_identifier', models.CharField(db_index=True, max_length=64)),
                ('name', models.CharField(blank=True, max_length=160)),
                ('birth_year', models.CharField(blank=True, max_length=20)),
                ('relation', models.CharField(blank=True, max_length=80)),
                ('sacraments', models.JSONField(blank=True, default=list)),
                ('roles', models.JSONField(blank=True, default=list)),
                ('notes', models.TextField(blank=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='zupa_vjernici.household')),
            ],
            options={
                'ordering': ['sort_order', 'name'],
                'unique_together': {('household', 'public_identifier')},
            },
        ),
        migrations.CreateModel(
            name='HouseholdRelative',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('public_identifier', models.CharField(db_index=True, max_length=64)),
                ('name', models.CharField(blank=True, max_length=160)),
                ('relation', models.CharField(blank=True, max_length=80)),
                ('birth_year', models.CharField(blank=True, max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relatives', to='zupa_vjernici.household')),
            ],
            options={
                'ordering': ['sort_order', 'name'],
                'unique_together': {('household', 'public_identifier')},
            },
        ),
        migrations.RunPython(backfill_households_and_visits, noop_reverse),
    ]
