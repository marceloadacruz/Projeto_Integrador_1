from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Garante um admin de desenvolvimento. Idempotente e só funciona com DEBUG=True."

    DEFAULT_USERNAME = "admin"
    DEFAULT_EMAIL = "admin@example.com"
    DEFAULT_PASSWORD = "12345"

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(self.style.WARNING(
                "DEBUG=False; pulando criação de admin de dev por segurança."
            ))
            return

        User = get_user_model()

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Já existe um superuser (mantido). Nenhum admin de dev foi criado.")
            return

        User.objects.create_superuser(
            self.DEFAULT_USERNAME, self.DEFAULT_EMAIL, self.DEFAULT_PASSWORD,
        )
        self.stdout.write(self.style.SUCCESS(
            f'Admin de dev "{self.DEFAULT_USERNAME}" criado com senha "{self.DEFAULT_PASSWORD}". '
            "SÓ USE EM DESENVOLVIMENTO."
        ))
