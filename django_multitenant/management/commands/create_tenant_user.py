"""Kreira tenant (schema + domena) i po želji korisnika u toj schemi."""
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django_tenants.utils import get_public_schema_name, schema_context

from django_multitenant.models import Domain, Tenant
from django_multitenant.schema import with_tenant_schema


class Command(BaseCommand):
    help = (
        'Kreira PostgreSQL schemu tenanta, primarnu domenu i (opcionalno) '
        'korisnika. HTTP nakon toga bira schemu prema Host zaglavlju.'
    )

    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str)
        parser.add_argument('name', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument(
            '--email',
            default='',
            help='Ako je zadano, u tenant schemi se kreira staff korisnik.',
        )
        parser.add_argument('--password', default='')
        parser.add_argument(
            '--seed',
            action='store_true',
            help='Pokreni seed_pastoral unutar nove scheme.',
        )

    @with_tenant_schema
    def handle(self, *args, **options):
        schema_name = options['schema_name']
        name = options['name']
        domain = options['domain']
        public_schema = get_public_schema_name()
        if schema_name == public_schema:
            raise CommandError('Ne koristi public schemu kao tenant.')

        connection.set_schema(public_schema)
        tenant, created = Tenant.objects.get_or_create(
            schema_name=schema_name,
            defaults={'name': name},
        )
        if not created and tenant.name != name:
            tenant.name = name
            tenant.save(update_fields=['name'])

        Domain.objects.get_or_create(
            domain=domain,
            defaults={'tenant': tenant, 'is_primary': True},
        )
        call_command(
            'migrate_schemas',
            schema_name=schema_name,
            interactive=False,
            verbosity=1,
        )

        with schema_context(schema_name):
            if options['email']:
                self._create_tenant_user(
                    options['email'],
                    options['password'],
                )
            if options['seed']:
                call_command('seed_pastoral')

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Kreiran tenant {schema_name} ({domain}).',
            ))
        else:
            self.stdout.write(f'Tenant {schema_name} već postoji; schema je usklađena.')

    @with_tenant_schema
    def _create_tenant_user(self, email, password):
        from django_multitenant.models import User

        if not password:
            raise CommandError('--password je obavezan uz --email.')
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'name': email,
                'role': 'zupnik',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        action = 'kreiran' if created else 'ažuriran'
        self.stdout.write(f'Korisnik {email} {action} u schemi {connection.schema_name}.')
