import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from planner.models import Notification, Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Проверяет задачи и создает уведомления"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test",
            action="store_true",
            help="Тестовый режим (показывает что было бы отправлено)",
        )
        parser.add_argument("--send-email", action="store_true", help="Отправлять email уведомления")

    def handle(self, *args, **options):
        now = timezone.now()
        test_mode = options["test"]
        send_email = options["send_email"]  # Получаем параметр отправки email

        self.stdout.write(f"🕒 Проверка уведомлений в {now}")
        if test_mode:
            self.stdout.write("🧪 ТЕСТОВЫЙ РЕЖИМ - email не отправляются")
        elif send_email:
            self.stdout.write("📧 РЕЖИМ ОТПРАВКИ EMAIL - уведомления будут отправлены")

        created_count = 0
        email_count = 0
        notifications_to_email = []  # Список уведомлений для отправки

        # 1. Создаем уведомления для приближающихся дедлайнов
        upcoming_tasks = Task.objects.filter(
            due_date__isnull=False,
            status__in=["todo", "in_progress"],
            notification_setting__in=["day_before", "hour_before", "fifteen_minutes", "at_time"],
        ).select_related("user")

        for task in upcoming_tasks:
            if not task.user.email:
                continue

            time_until_deadline = task.due_date - now

            # Проверяем условия для уведомлений
            should_notify = False
            message = ""

            if task.notification_setting == "day_before" and timedelta(hours=23) <= time_until_deadline <= timedelta(
                hours=25
            ):
                message = f'Напоминание: завтра дедлайн по задаче "{task.title}"'
                should_notify = True

            elif task.notification_setting == "hour_before" and timedelta(
                minutes=55
            ) <= time_until_deadline <= timedelta(hours=1, minutes=5):
                message = f'Напоминание: через час дедлайн по задаче "{task.title}"'
                should_notify = True

            elif task.notification_setting == "fifteen_minutes" and timedelta(
                minutes=10
            ) <= time_until_deadline <= timedelta(minutes=20):
                message = f'Напоминание: через 15 минут дедлайн по задаче "{task.title}"'
                should_notify = True

            elif (
                task.notification_setting == "at_time"
                and task.custom_notification_time
                and abs((task.custom_notification_time - now).total_seconds()) <= 300
            ):  # ±5 минут
                message = f'Напоминание: дедлайн по задаче "{task.title}"'
                should_notify = True

            if should_notify:
                # Проверяем нет ли уже такого уведомления
                existing_notification = Notification.objects.filter(
                    task=task, notification_type="deadline", message=message
                ).exists()

                if not existing_notification:
                    notification = Notification.objects.create(
                        user=task.user,
                        task=task,
                        notification_type="deadline",
                        title="Напоминание о задаче",
                        message=message,
                        scheduled_for=timezone.now(),
                    )
                    created_count += 1
                    notifications_to_email.append(notification)

                    if test_mode:
                        self.stdout.write(
                            self.style.SUCCESS(f"📧 [TEST] Уведомление для {task.user.email}: {task.title}")
                        )
                    else:
                        self.stdout.write(self.style.SUCCESS(f"✅ Создано уведомление: {task.title}"))

        # 2. Уведомления о просроченных задачах
        overdue_tasks = (
            Task.objects.filter(
                due_date__lt=now,
                status__in=["todo", "in_progress"],
            )
            .exclude(notifications__notification_type="overdue")
            .select_related("user")
        )

        for task in overdue_tasks:
            if not task.user.email:
                continue

            # Создаем уведомление о просрочке
            notification = Notification.objects.create(
                user=task.user,
                task=task,
                notification_type="overdue",
                title="Задача просрочена",
                message=f'Задача "{task.title}" просрочена!',
                scheduled_for=timezone.now(),
            )

            created_count += 1
            notifications_to_email.append(notification)

            if test_mode:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ [TEST] Уведомление о просрочке для {task.user.email}: {task.title}")
                )
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Создано уведомление о просрочке: {task.title}"))

        # 3. Отправка email уведомлений
        if send_email and not test_mode and notifications_to_email:
            self.stdout.write("\n📧 Отправка email уведомлений...")
            email_count = self.send_notification_emails(notifications_to_email)

        # Итоги
        self.stdout.write("\n" + "=" * 50)
        if test_mode:
            self.stdout.write(self.style.SUCCESS(f"ТЕСТ: Было бы создано {created_count} уведомлений"))
            if send_email:
                self.stdout.write(self.style.WARNING("В тестовом режиме email не отправляются"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Создано {created_count} новых уведомлений"))
            if send_email:
                self.stdout.write(self.style.SUCCESS(f"Отправлено {email_count} email уведомлений"))

    def send_notification_emails(self, notifications):
        """Отправляет email уведомления"""
        sent_count = 0

        for notification in notifications:
            try:
                # Формируем тему и текст письма
                subject = f"🔔 {notification.title}"

                # Базовый текст письма
                message_text = f"""
{notification.message}

Детали задачи:
• Задача: {notification.task.title}
• Приоритет: {notification.task.get_priority_display()}
• Статус: {notification.task.get_status_display()}
• Дедлайн: {notification.task.due_date.strftime('%d.%m.%Y %H:%M') if notification.task.due_date else 'Не установлен'}

---
Личный дневник - Ваш помощник в планировании!
                """.strip()

                # Отправляем email
                send_mail(
                    subject=subject,
                    message=message_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.user.email],
                    fail_silently=False,
                )

                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Email отправлен для {notification.user.email}: {notification.task.title}")
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Ошибка отправки email для {notification.user.email}: {e}"))
                logger.error(f"Ошибка отправки email уведомления: {e}")

        return sent_count
