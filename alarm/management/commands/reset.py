from django.core.management.base import BaseCommand

from alarm.models import AlarmSound


class Command(BaseCommand):
    help = "Reset alarm sounds and create new ones"

    def handle(self, *args, **options):
        # Удаляем все старые звуки
        count, _ = AlarmSound.objects.all().delete()
        self.stdout.write(f"🗑️ Удалено записей: {count}")

        # Создаем заново
        from django.core.management import call_command

        call_command("create_default_sounds")
