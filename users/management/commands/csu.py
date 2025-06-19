from django.core.management import BaseCommand

from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.create(username="admin", email="admin@example.com", address="Mykop")
        user.set_password("admin123")
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
