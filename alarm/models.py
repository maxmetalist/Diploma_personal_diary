import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class AlarmSound(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название мелодии")
    file = models.FileField(
        upload_to="alarm_sounds/default/",
        verbose_name="Файл мелодии",
        validators=[FileExtensionValidator(allowed_extensions=["mp3", "wav", "ogg"])],
    )
    is_default = models.BooleanField(default=True, verbose_name="Стандартная мелодия")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "мелодия будильника"
        verbose_name_plural = "мелодии будильников"

    def __str__(self):
        return self.name

    def filename(self):
        return os.path.basename(self.file.name)


class Alarm(models.Model):
    DAYS_OF_WEEK = [
        (0, "Понедельник"),
        (1, "Вторник"),
        (2, "Среда"),
        (3, "Четверг"),
        (4, "Пятница"),
        (5, "Суббота"),
        (6, "Воскресенье"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alarms")
    name = models.CharField(max_length=200, verbose_name="Название будильника")
    reminder_text = models.TextField(blank=True, verbose_name="Текст напоминания")
    alarm_time = models.TimeField(verbose_name="Время срабатывания")

    # Настройки повторения
    is_recurring = models.BooleanField(default=False, verbose_name="Повторяющийся будильник")
    days_of_week = models.JSONField(default=list, blank=True, verbose_name="Дни недели")

    # Мелодия
    sound = models.ForeignKey(AlarmSound, on_delete=models.CASCADE, verbose_name="Мелодия")
    custom_sound = models.FileField(
        upload_to="alarm_sounds/custom/",
        null=True,
        blank=True,
        verbose_name="Своя мелодия",
        validators=[FileExtensionValidator(allowed_extensions=["mp3", "wav", "ogg"])],
    )

    # Статус
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "будильник"
        verbose_name_plural = "будильники"
        ordering = ["alarm_time"]

    def __str__(self):
        return f"{self.name} - {self.alarm_time}"

    def get_sound_url(self):
        """Возвращает URL звукового файла"""
        # Сначала проверяем пользовательскую мелодию
        if self.custom_sound and self.custom_sound.name:
            try:
                return self.custom_sound.url
            except ValueError:
                # Файл не существует в хранилище
                pass

        # Затем проверяем стандартную мелодию
        if self.sound and self.sound.file:
            try:
                return self.sound.file.url
            except ValueError:
                # Файл не существует в хранилище
                pass

        # Запасной вариант - статические файлы
        filename_mapping = {
            "Классический будильник": "classic.mp3",
            "Птички": "crowing.wav",
            "Радиосигнал": "digital.wav",
            "Колокольчик": "old.mp3",
            "Электронный": "electronic.mp3",
            "Электронный 2": "electronic1.mp3",
        }

        filename = filename_mapping.get(self.sound.name if self.sound else "")
        if filename:
            return f"/static/alarm_sounds/{filename}"

        # Последний запасной вариант
        return "/static/alarm_sounds/classic.mp3"

    def get_days_display(self):
        """Возвращает строку с днями недели"""
        if not self.days_of_week:
            return "Однократно"
        try:
            days_names = []
            for day in self.days_of_week:
                # Преобразуем день в число если это строка
                day_int = int(day) if isinstance(day, str) else day
                # Ищем название дня в DAYS_OF_WEEK
                day_name = next((name for num, name in self.DAYS_OF_WEEK if num == day_int), None)
                if day_name:
                    days_names.append(day_name)

            return ", ".join(days_names) if days_names else "Однократно"
        except (ValueError, TypeError):
            return "Однократно"

    def should_ring_today(self):
        """Проверяет, должен ли будильник сработать сегодня"""
        if not self.is_active:
            return False

        today_weekday = timezone.now().weekday()

        if self.is_recurring:
            return today_weekday in self.days_of_week
        else:
            # Для однократного будильника проверяем дату создания
            return self.created_at.date() == timezone.now().date()

    def should_ring_now(self, tolerance_minutes=10):
        """Упрощенная проверка для тестирования"""

        from django.utils import timezone

        now = timezone.now()
        current_time = now.time()
        current_weekday = now.weekday()

        # Основные проверки
        if not self.is_active:
            return False

        # Проверка времени с допуском
        alarm_minutes = self.alarm_time.hour * 60 + self.alarm_time.minute
        current_minutes = current_time.hour * 60 + current_time.minute
        time_diff = abs(current_minutes - alarm_minutes)

        if time_diff > tolerance_minutes:
            return False

        # Проверка дней недели для повторяющихся будильников
        if self.is_recurring:
            if not self.days_of_week:
                return False
            # Преобразуем все дни в int для сравнения
            try:
                days_int = [int(day) for day in self.days_of_week]
                return current_weekday in days_int
            except (ValueError, TypeError):
                return False
        else:
            # Для однократных будильников проверяем дату создания
            return self.created_at.date() == now.date()
