from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "🔵 Низкий"),
        ("medium", "🟡 Средний"),
        ("high", "🔴 Высокий"),
    ]

    STATUS_CHOICES = [
        ("todo", "📝 К выполнению"),
        ("in_progress", "🔄 В процессе"),
        ("done", "✅ Выполнено"),
    ]

    RECURRENCE_CHOICES = [
        ("none", "Не повторяется"),
        ("daily", "Ежедневно"),
        ("weekly", "Еженедельно"),
        ("monthly", "Ежемесячно"),
        ("custom", "Особое расписание"),
    ]

    NOTIFICATION_CHOICES = [
        ("none", "Не уведомлять"),
        ("day_before", "За день"),
        ("hour_before", "За час"),
        ("fifteen_minutes", "За 15 минут"),
        ("at_time", "В указанное время"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium", verbose_name="Приоритет")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="todo", verbose_name="Статус")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата выполнения")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Поля для периодических задач
    is_recurring = models.CharField(
        max_length=20, choices=RECURRENCE_CHOICES, default="none", verbose_name="Повторение"
    )

    # Для еженедельного повторения - дни недели (0-6, где 0 - понедельник)
    weekly_days = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Дни недели",
        help_text="Дни недели для повторения (0-6, где 0 - понедельник)",
    )

    # Для ежемесячного повторения - числа месяца (1-31)
    monthly_days = models.JSONField(
        default=list, blank=True, verbose_name="Числа месяца", help_text="Числа месяца для повторения (1-31)"
    )

    # Дата окончания повторений
    recurrence_end_date = models.DateTimeField(null=True, blank=True, verbose_name="Повторять до")

    # ID оригинальной задачи для цепочки повторений
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recurrences",
        verbose_name="Родительская задача",
    )

    # Поля для уведомлений
    notification_setting = models.CharField(
        max_length=20, choices=NOTIFICATION_CHOICES, default="none", verbose_name="Уведомление"
    )

    # Дополнительное время для уведомления (если выбрано 'at_time')
    custom_notification_time = models.DateTimeField(null=True, blank=True, verbose_name="Время уведомления")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        indexes = [
            models.Index(fields=["user", "due_date"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["parent_task"]),
        ]

    def __str__(self):
        recurrence_info = ""
        if self.is_recurring != "none":
            recurrence_info = f" ({self.get_is_recurring_display()})"
        return f"{self.title}{recurrence_info}"

    def is_overdue(self):
        if self.due_date and not self.completed_date:
            return timezone.now() > self.due_date
        return False

    def get_days_until_deadline(self):
        """Возвращает количество дней до дедлайна"""
        if self.due_date and not self.completed_date:
            delta = self.due_date - timezone.now()
            return delta.days
        return None

    def create_deadline_notification(self):
        """Создает уведомление о приближающемся дедлайне"""
        if not self.due_date or self.notification_setting == "none":
            return None

        from datetime import timedelta

        # Вычисляем время уведомления
        notification_time = None
        message = ""

        if self.notification_setting == "day_before":
            notification_time = self.due_date - timedelta(days=1)
            message = f"Напоминание: завтра дедлайн по задаче '{self.title}'"
        elif self.notification_setting == "hour_before":
            notification_time = self.due_date - timedelta(hours=1)
            message = f"Напоминание: через час дедлайн по задаче '{self.title}'"
        elif self.notification_setting == "fifteen_minutes":
            notification_time = self.due_date - timedelta(minutes=15)
            message = f"Напоминание: через 15 минут дедлайн по задаче '{self.title}'"
        elif self.notification_setting == "at_time" and self.custom_notification_time:
            notification_time = self.custom_notification_time
            message = f"Напоминание: дедлайн по задаче '{self.title}'"

        if notification_time and notification_time > timezone.now():
            from .models import Notification

            notification = Notification.objects.create(
                user=self.user,
                task=self,
                notification_type="deadline",
                title="Напоминание о дедлайне",
                message=message,
                scheduled_for=notification_time,
            )
            return notification

        return None

    def create_overdue_notification(self):
        """Создает уведомление о просроченной задаче"""
        if self.due_date and self.due_date < timezone.now() and self.status in ["todo", "in_progress"]:
            from .models import Notification

            notification = Notification.objects.create(
                user=self.user,
                task=self,
                notification_type="overdue",
                title="Задача просрочена",
                message=f'Задача "{self.title}" просрочена!',
                scheduled_for=timezone.now(),
            )
            return notification
        return None

    def create_recurrences(self):
        """Создает следующие экземпляры повторяющейся задачи"""
        if self.is_recurring == "none" or not self.due_date:
            return None

        from datetime import timedelta

        next_date = self.due_date

        if self.is_recurring == "daily":
            next_date = self.due_date + timedelta(days=1)

        elif self.is_recurring == "weekly" and self.weekly_days:
            # Находим следующий день недели из списка
            current_weekday = self.due_date.weekday()  # 0-6 (пн-вс)
            next_days = [int(day) for day in self.weekly_days if int(day) > current_weekday]

            if next_days:
                days_to_add = min(next_days) - current_weekday
            else:
                days_to_add = 7 - current_weekday + min([int(day) for day in self.weekly_days])
            next_date = self.due_date + timedelta(days=days_to_add)

        elif self.is_recurring == "monthly" and self.monthly_days:
            # Находим следующее число месяца
            current_day = self.due_date.day
            next_days = [int(day) for day in self.monthly_days if int(day) > current_day]

            if next_days:
                next_day = min(next_days)
            else:
                next_day = min([int(day) for day in self.monthly_days])

            # Простой расчет следующей даты
            try:
                next_date = self.due_date.replace(day=next_day)
                if next_date <= self.due_date:
                    # Переход на следующий месяц
                    if next_date.month == 12:
                        next_date = next_date.replace(year=next_date.year + 1, month=1)
                    else:
                        next_date = next_date.replace(month=next_date.month + 1)
            except ValueError:
                # Если день не существует в месяце (например, 31 февраля)
                # Переходим на следующий месяц и берем первое число
                if self.due_date.month == 12:
                    next_date = self.due_date.replace(year=self.due_date.year + 1, month=1, day=1)
                else:
                    next_date = self.due_date.replace(month=self.due_date.month + 1, day=1)

        # Проверяем не превысили ли дату окончания повторений
        if self.recurrence_end_date and next_date > self.recurrence_end_date:
            return None

        # Создаем новую задачу
        recurrence = Task.objects.create(
            title=self.title,
            description=self.description,
            due_date=next_date,
            priority=self.priority,
            user=self.user,
            is_recurring=self.is_recurring,
            weekly_days=self.weekly_days,
            monthly_days=self.monthly_days,
            recurrence_end_date=self.recurrence_end_date,
            parent_task=self,
            notification_setting=self.notification_setting,
            custom_notification_time=self.custom_notification_time,
        )

        # Создаем уведомление для новой повторяющейся задачи
        recurrence.create_deadline_notification()

        return recurrence

    def get_recurrence_description(self):
        """Возвращает текстовое описание периодичности"""
        if self.is_recurring == "none":
            return "Не повторяется"
        elif self.is_recurring == "daily":
            return "Ежедневно"
        elif self.is_recurring == "weekly" and self.weekly_days:
            days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            days = [days_names[int(day)] for day in self.weekly_days]
            return f"Еженедельно: {', '.join(days)}"
        elif self.is_recurring == "monthly" and self.monthly_days:
            days = [str(day) for day in self.monthly_days]
            return f"Ежемесячно: {', '.join(days)} числа"
        elif self.is_recurring == "custom":
            return "Особое расписание"
        return self.get_is_recurring_display()

    def clean_weekly_days(self):
        """Очищает и валидирует дни недели"""
        if self.weekly_days:
            # Убираем дубликаты и сортируем
            unique_days = list(set(int(day) for day in self.weekly_days if 0 <= int(day) <= 6))
            self.weekly_days = sorted(unique_days)

    def clean_monthly_days(self):
        """Очищает и валидирует числа месяца"""
        if self.monthly_days:
            # Убираем дубликаты и сортируем, оставляем только 1-31
            unique_days = list(set(int(day) for day in self.monthly_days if 1 <= int(day) <= 31))
            self.monthly_days = sorted(unique_days)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_task = None

        if not is_new:
            try:
                old_task = Task.objects.get(pk=self.pk)
            except Task.DoesNotExist:
                pass

        # Очищаем данные периодичности
        self.clean_weekly_days()
        self.clean_monthly_days()

        # Обработка статуса выполнения
        if self.status == "done" and not self.completed_date:
            self.completed_date = timezone.now()
        elif self.status != "done" and self.completed_date:
            self.completed_date = None

        super().save(*args, **kwargs)

        # Обработка уведомлений при изменении даты выполнения или настроек уведомлений
        if not is_new and old_task:
            if (
                self.due_date != old_task.due_date or
                self.notification_setting != old_task.notification_setting or
                self.custom_notification_time != old_task.custom_notification_time
            ):
                # Удаляем старые уведомления по этой задаче
                self.notifications.filter(notification_type="deadline").delete()
                # Создаем новые уведомления
                self.create_deadline_notification()

        # Создаем уведомление о дедлайне для новой задачи
        if is_new:
            self.create_deadline_notification()

        # Если задача завершена и она повторяющаяся, создаем следующую
        if not is_new and self.status == "done" and self.is_recurring != "none":
            self.create_recurrences()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("deadline", "Приближается дедлайн"),
        ("overdue", "Просроченная задача"),
        ("reminder", "Напоминание"),
        ("system", "Системное уведомление"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    task = models.ForeignKey("Task", on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default="system")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)  # Отправлено ли уведомление
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(default=timezone.now)  # Когда показать уведомление

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["scheduled_for", "is_sent"]),
        ]

    def __str__(self):
        return f"{self.title} - {getattr(self.user, 'email', 'No user')}"

    def mark_as_read(self):
        """Пометить уведомление как прочитанное"""
        self.is_read = True
        self.save()

    def mark_as_sent(self):
        """Пометить уведомление как отправленное"""
        self.is_sent = True
        self.save()


class NotificationPreference(models.Model):
    """Настройки уведомлений для пользователя"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences"
    )

    # Типы уведомлений
    enable_email_notifications = models.BooleanField(default=True)
    enable_push_notifications = models.BooleanField(default=True)
    enable_browser_notifications = models.BooleanField(default=True)

    # Настройки для задач
    notify_before_deadline = models.BooleanField(default=True)
    deadline_reminder_time = models.PositiveIntegerField(
        default=24, help_text="За сколько часов уведомлять о дедлайне"
    )
    notify_on_overdue = models.BooleanField(default=True)

    # Время тишины (не беспокоить)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Настройки уведомлений - {self.user.username}"

    def is_quiet_time(self):
        """Проверяет, сейчас ли время тишины"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        now = timezone.now().time()
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            # Если время тишины переходит через полночь
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end
