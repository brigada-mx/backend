"""
USAGE:
```
source .env
python manage.py staffuser --email <> --password <> --first_name <> --surnames <>
```
"""
from django.core.management.base import BaseCommand

from db.users.models import StaffUser


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--first_name', default='919')
        parser.add_argument('--surnames', default='Admin')
        parser.add_argument('--superuser', action='store_true')

    def handle(self, *args, **options):
        email = options.get('email')
        password = options.get('password')
        superuser = options.get('superuser')
        if not email or not password:
            raise ValueError('Both email and password must be defined')
        first_name = options.get('first_name')
        surnames = options.get('surnames')

        user = StaffUser.objects.filter(email=email).first()
        if user is None:
            user = StaffUser(
                email=email, first_name=first_name, surnames=surnames, is_superuser=superuser, is_active=True
            )
        user.set_password(password)
        user.save()
