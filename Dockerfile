FROM python:3.13-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем Poetry
RUN pip install poetry

# Конфигурируем Poetry
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости
RUN poetry install --without dev --no-interaction --no-ansi --no-root

# Копируем весь проект
COPY . .

EXPOSE 8000

CMD case "$SERVICE_NAME" in \
    "web") \
        python manage.py migrate && \
        python manage.py collectstatic --noinput && \
        gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 \
        ;; \
    "celery_worker") \
        celery -A config worker --loglevel=info --concurrency=4 \
        ;; \
    "celery_beat") \
        celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler \
        ;; \
    *) \
        echo "Unknown service: $SERVICE_NAME" && exit 1 \
        ;; \
    esac
