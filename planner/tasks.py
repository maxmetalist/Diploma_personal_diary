import logging

from celery import shared_task
from django.core.management import call_command
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="planner.tasks.test_celery_task")
def test_celery_task():
    """Тестовая задача для проверки Celery"""
    logger.info("✅ Celery тестовая задача выполнена!")
    return "Celery работает!"


@shared_task(name="planner.tasks.check_notifications")
def check_notifications_task():
    """Фоновая задача для проверки уведомлений"""
    try:
        logger.info(f"🕒 Celery: Запуск проверки уведомлений в {timezone.now()}")
        call_command("check_notifications", "--send-email")
        logger.info("✅ Celery: Проверка уведомлений завершена")
        return "Уведомления проверены"
    except Exception as e:
        logger.error(f"❌ Celery: Ошибка проверки уведомлений: {e}")
        return f"Ошибка: {e}"


@shared_task(name="planner.tasks.send_daily_digest")
def send_daily_digest_task():
    """Фоновая задача для отправки ежедневного дайджеста"""
    try:
        logger.info(f"📧 Celery: Запуск отправки дайджеста в {timezone.now()}")
        call_command("send_daily_digest")
        logger.info("✅ Celery: Отправка дайджеста завершена")
        return "Дайджест отправлен"
    except Exception as e:
        logger.error(f"❌ Celery: Ошибка отправки дайджеста: {e}")
        return f"Ошибка: {e}"
