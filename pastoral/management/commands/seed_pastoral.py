from django.core.management.base import BaseCommand

from pastoral.models import User
from pastoral.services.data import ParishDataService


class Command(BaseCommand):
    help = 'Učitaj demo podatke župe i demo korisnike'

    def handle(self, *args, **options):
        svc = ParishDataService()
        svc.reset_demo()
        self.stdout.write(self.style.SUCCESS('Demo podaci župe učitani.'))

        demo_users = [
            ('ured@zupa-bdm-sb.hr', 'Župni ured', 'zupnik'),
            ('vikar@zupa-bdm-sb.hr', 'Vikar', 'vikar'),
            ('upravitelj@zupa-bdm-sb.hr', 'Upravitelj', 'upravitelj'),
        ]
        for email, name, role in demo_users:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'name': name, 'role': role},
            )
            if not created:
                user.role = role
                user.name = name
                user.save()
            user.set_password('pastoral-demo')
            user.save()
            self.stdout.write(f'  {email} ({role})')

        self.stdout.write(self.style.SUCCESS('Gotovo.'))
