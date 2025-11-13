from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from planner.models import Notification
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Сервис для отправки email уведомлений"""

    @staticmethod
    def send_task_notification(notification):
        """Отправляет уведомление о задаче по email"""
        try:
            user = notification.user
            task = notification.task

            if not user.email:
                logger.warning(f"У пользователя {user.username} не указан email")
                return False

            # Тема письма
            subject = f"🔔 {notification.title}"

            # URL для задачи
            task_url = ""
            if task:
                task_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}{reverse('planner:task_update', kwargs={'pk': task.id})}"

            # Контекст для шаблона
            context = {
                'user': user,
                'notification': notification,
                'task': task,
                'task_url': task_url,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            }

            # HTML версия письма
            html_content = render_to_string('planner/emails/task_notification.html', context)

            # Текстовая версия письма
            text_content = strip_tags(html_content)

            # Создаем письмо
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                to=[user.email],
                reply_to=[getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')]
            )

            # Добавляем HTML версию
            email.attach_alternative(html_content, "text/html")

            # Отправляем
            email.send()

            # Помечаем уведомление как отправленное
            notification.is_sent = True
            notification.save()

            logger.info(f"✅ Email отправлен пользователю {user.email}: {notification.title}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки email для {notification.user.username}: {str(e)}")
            return False

    @staticmethod
    def send_daily_digest(user, notifications):
        """Отправляет ежедневный дайджест уведомлений"""
        try:
            if not user.email:
                return False

            subject = "📅 Ежедневный дайджест задач - Личные записульки"

            context = {
                'user': user,
                'notifications': notifications,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            }

            html_content = render_to_string('planner/emails/daily_digest.html', context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                to=[user.email]
            )

            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"✅ Ежедневный дайджест отправлен пользователю {user.email}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки дайджеста для {user.username}: {str(e)}")
            return False