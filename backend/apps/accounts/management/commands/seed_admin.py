import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Bootstrap the first super_admin user (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default=None)
        parser.add_argument("--email", default="")

    def handle(self, *args, **options):
        username = options["username"]
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"User '{username}' already exists — skipping.")
            return
        password = options["password"] or os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            raise CommandError("Provide --password or set DJANGO_SUPERUSER_PASSWORD.")
        User.objects.create_superuser(
            username=username, email=options["email"], password=password, role="super_admin"
        )
        self.stdout.write(self.style.SUCCESS(f"Created super_admin '{username}'."))
