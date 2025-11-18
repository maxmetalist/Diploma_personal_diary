import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Периодические задачи
app.conf.beat_schedule = {
    # Для будильников
    "check-alarms-every-minute": {
        "task": "alarm.tasks.check_alarms_task",
        "schedule": crontab(minute="*"),  # Каждую минуту
    },
    # Для планинга
    "test-task-every-5-min": {
        "task": "planner.tasks.test_celery_task",
        "schedule": crontab(minute="*/5"),
    },
}

app.conf.timezone = "Europe/Moscow"
