# management/commands/create_default_sounds.py
import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from alarm.models import AlarmSound


class Command(BaseCommand):
    help = "Create default alarm sounds with actual audio files"

    def handle(self, *args, **options):
        # Ищем папку со звуками в разных возможных местах
        possible_paths = [
            os.path.join(settings.BASE_DIR, "alarm", "static", "alarm_sounds"),
            os.path.join(settings.BASE_DIR, "static", "alarm_sounds"),
            os.path.join(os.path.dirname(__file__), "..", "..", "static", "alarm_sounds"),
        ]

        sounds_dir = os.path.join(settings.BASE_DIR, "static", "alarm_sounds")
        for path in possible_paths:
            if os.path.exists(path):
                sounds_dir = path
                break

        if not sounds_dir:
            self.stdout.write(self.style.ERROR("❌ Папка со звуками не найдена!"))
            self.stdout.write("Проверьте что файлы находятся в alarm/static/alarm_sounds/")
            return

        self.stdout.write(f"📁 Найдена папка со звуками: {sounds_dir}")

        # Покажем какие файлы есть в папке
        self.stdout.write("\n📂 Файлы в папке:")
        for item in os.listdir(sounds_dir):
            self.stdout.write(f"   📄 {item}")

        default_sounds = [
            {"name": "Классический будильник", "filename": "classic.mp3"},
            {"name": "Петух", "filename": "crowing.wav"},
            {"name": "Цифровой сигнал", "filename": "digital.wav"},
            {"name": "Колокольчик", "filename": "old.mp3"},
            {"name": "Электронный", "filename": "electronic.mp3"},
            {"name": "Электронный 2", "filename": "electronic1.mp3"},
        ]

        created_count = 0
        updated_count = 0

        for sound_data in default_sounds:
            file_path = os.path.join(sounds_dir, sound_data["filename"])

            if not os.path.exists(file_path):
                self.stdout.write(self.style.WARNING(f'⚠️ Файл не найден: {sound_data["filename"]}'))
                continue

            # Создаем или обновляем запись
            sound, created = AlarmSound.objects.get_or_create(name=sound_data["name"], defaults={"is_default": True})

            # Обновляем файл
            with open(file_path, "rb") as f:
                sound.file.save(sound_data["filename"], File(f), save=True)

            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Создана мелодия: {sound.name} -> {sound_data["filename"]}'))
                created_count += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'🔄 Обновлена мелодия: {sound.name} -> {sound_data["filename"]}')
                )
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"\n🎵 Готово! Создано: {created_count}, Обновлено: {updated_count}"))
