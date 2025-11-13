from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Тестирование отправки email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email для отправки тестового письма',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        test_email = options['email']

        try:
            send_mail(
                '✅ Тестовое письмо из Личных записулек',
                'Это тестовое письмо для проверки работы email системы.\n\nЕсли вы получили это письмо, значит email система работает корректно!',
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                [test_email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Тестовое письмо отправлено на {test_email}!')
            )

            # Показываем настройки
            self.stdout.write(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Не указан')}")
            self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Не указан')}")
            self.stdout.write(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Не указан')}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка отправки: {e}')
            )
            self.stdout.write(
                self.style.WARNING('💡 Совет: Проверьте настройки EMAIL_* в settings.py')
            )