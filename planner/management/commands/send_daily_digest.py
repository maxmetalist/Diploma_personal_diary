from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from planner.email_service import EmailNotificationService
from planner.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = "Отправляет ежедневный дайджест уведомлений"

    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # Находим пользователей с уведомлениями за последние 24 часа
        users_with_notifications = User.objects.filter(notifications__created_at__gte=yesterday).distinct()

        sent_count = 0

        for user in users_with_notifications:
            # Получаем уведомления пользователя за последние 24 часа
            notifications = Notification.objects.filter(user=user, created_at__gte=yesterday).select_related("task")[
                :10
            ]  # Ограничиваем количество

            if notifications:
                try:
                    if EmailNotificationService.send_daily_digest(user, notifications):
                        sent_count += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ Дайджест отправлен пользователю {user.email}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ Ошибка отправки дайджеста для {user.email}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка при отправке дайджеста для {user.email}: {e}"))

                self.stdout.write(self.style.SUCCESS(f"📧 Отправлено {sent_count} ежедневных дайджестов"))
