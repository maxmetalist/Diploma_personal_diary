from django.core.management.base import BaseCommand

from alarm.models import Alarm, AlarmSound


class Command(BaseCommand):
    """Команда проверки доступности мелодий для будильников"""

    help = "Check alarm sounds availability"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Проверка стандартных мелодий...")

        sounds = AlarmSound.objects.all()
        for sound in sounds:
            status = "✅ Есть файл" if sound.file and sound.file.name else "❌ Нет файла"
            self.stdout.write(f"   {sound.name}: {status}")
            if sound.file and sound.file.name:
                try:
                    url = sound.file.url
                    self.stdout.write(f"      URL: {url}")
                except ValueError:
                    self.stdout.write(f"      ❌ Ошибка получения URL")

        self.stdout.write("\n🔍 Проверка будильников...")
        alarms = Alarm.objects.all()[:5]  # Первые 5 для примера
        for alarm in alarms:
            self.stdout.write(f"\n   Будильник: {alarm.name}")
            self.stdout.write(f"      Мелодия: {alarm.sound}")
            self.stdout.write(f"      Кастомный звук: {alarm.custom_sound}")
            self.stdout.write(f"      Final URL: {alarm.get_sound_url()}")
