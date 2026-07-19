from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create admin user if not exists'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@shopeasy.com',
                password='Admin@1234'
            )
            self.stdout.write('Admin user created successfully!')
        else:
            self.stdout.write('Admin user already exists.')