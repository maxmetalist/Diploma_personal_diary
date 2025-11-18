from django.core.management.base import BaseCommand

from planner.tasks import check_notifications_task, test_celery_task


class Command(BaseCommand):
    help = "Тест Celery задач планировщика"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Тестируем Celery задачи...")

        # Тестовая задача
        self.stdout.write("1. Тестируем базовую задачу...")
        result = test_celery_task.delay()

        # Ждем результат с обработкой ошибок
        try:
            task_result = result.get(timeout=10)
            self.stdout.write(f"✅ Тестовая задача: {task_result}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка тестовой задачи: {e}"))
            return

        # Проверка уведомлений
        self.stdout.write("2. Запускаем проверку уведомлений...")
        result2 = check_notifications_task.delay()

        try:
            # Даем больше времени для отправки email
            task_result2 = result2.get(timeout=60)
            self.stdout.write(f"✅ Проверка уведомлений: {task_result2}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка проверки уведомлений: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("🎉 Все Celery задачи работают!"))
