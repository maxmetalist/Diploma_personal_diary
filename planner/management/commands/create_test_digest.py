# management/commands/create_test_digest.py
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from planner.models import Notification, Task

User = get_user_model()


class Command(BaseCommand):
    help = "Создает тестовые уведомления для дайджеста"

    def handle(self, *args, **options):
        user = User.objects.get(email="z.max83@mail.ru")

        # Создаем несколько тестовых уведомлений
        notifications_data = [
            {"title": "Новая задача создана", "message": 'Вы создали задачу "Подготовить отчет"', "type": "info"},
            {
                "title": "Напоминание о дедлайне",
                "message": 'Завтра дедлайн по задаче "Заполнить таблицы"',
                "type": "reminder",
            },
            {"title": "Задача просрочена", "message": 'Задача "Отправить документы" просрочена', "type": "overdue"},
        ]

        for i, notif_data in enumerate(notifications_data):
            Notification.objects.create(
                user=user,
                title=notif_data["title"],
                message=notif_data["message"],
                notification_type=notif_data["type"],
                scheduled_for=timezone.now(),
            )

        self.stdout.write(self.style.SUCCESS("✅ Созданы тестовые уведомления для дайджеста"))
