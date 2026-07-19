from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create or reset admin user'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='admin')
            user.set_password('Admin@1234')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write('Admin password reset successfully!')
        except User.DoesNotExist:
            User.objects.create_superuser(
                username='admin',
                email='admin@shopeasy.com',
                password='Admin@1234'
            )
            self.stdout.write('Admin user created successfully!')


