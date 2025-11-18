import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from alarm.models import Alarm

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def check_alarms_task():
    """Периодическая проверка активных будильников"""
    logger.info("🔔 Проверка активных будильников...")

    active_alarms = Alarm.objects.filter(is_active=True)

    ringing_count = 0
    for alarm in active_alarms:
        if alarm.should_ring_now():
            logger.info(f"🎯 Сработал будильник: {alarm.name}")
            ringing_count += 1

            # Запускаем задачу срабатывания для каждого будильника
            trigger_alarm_task.delay(alarm.id)

    return f"Проверено {active_alarms.count()} будильников, сработало: {ringing_count}"


@shared_task
def check_alarms_periodically():
    """Периодическая проверка будильников"""
    logger.info("🔔 Автоматическая проверка будильников...")

    active_alarms = Alarm.objects.filter(is_active=True)
    ringing_count = 0

    for alarm in active_alarms:
        if alarm.should_ring_now():
            logger.info(f"🎯 Сработал будильник: {alarm.name}")
            ringing_count += 1
            # Здесь можно добавить отправку уведомлений и т.д.

    logger.info(f"✅ Проверено {active_alarms.count()} будильников, сработало: {ringing_count}")
    return ringing_count


@shared_task
def trigger_alarm_task(alarm_id):
    """Задача срабатывания конкретного будильника"""
    try:
        alarm = Alarm.objects.get(id=alarm_id)
        logger.info(f"🚨 Обработка срабатывания: {alarm.name}")

        # Здесь потом появится логика:
        # - Отправка push-уведомлений
        # - Запись в историю
        # - Дополнительные действия
        # - Но всё это когда я научусь делать такие штуки

        return f"Будильник {alarm.name} обработан"

    except Alarm.DoesNotExist:
        logger.error(f"Будильник {alarm_id} не найден")
        return "Будильник не найден"
