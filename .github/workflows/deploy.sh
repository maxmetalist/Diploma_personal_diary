#!/bin/bash

set -e

# Параметры
IMAGE_TAG=$1
DOCKER_REGISTRY="ghcr.io"
IMAGE_NAME="your-username/Diploma_personal_diary"  # Замените на ваш репозиторий
COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 Starting deployment with tag: $IMAGE_TAG"

# Создаем директорию если не существует
mkdir -p /opt/diploma_personal_diary
cd /opt/diploma_personal_diary

# Логинимся в GitHub Container Registry
echo ${{ secrets.GITHUB_TOKEN }} | docker login $DOCKER_REGISTRY -u ${{ github.actor }} --password-stdin

# Останавливаем текущие контейнеры
echo "🛑 Stopping current containers..."
docker-compose -f $COMPOSE_FILE down || true

# Pull новых образов
echo "📥 Pulling new images..."
docker pull $DOCKER_REGISTRY/$IMAGE_NAME/web:$IMAGE_TAG
docker pull $DOCKER_REGISTRY/$IMAGE_NAME/celery-worker:$IMAGE_TAG
docker pull $DOCKER_REGISTRY/$IMAGE_NAME/celery-beat:$IMAGE_TAG

# Обновляем docker-compose.prod.yml с новыми тегами
cat > $COMPOSE_FILE << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DATABASE_NAME}
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - app-network

  web:
    image: $DOCKER_REGISTRY/$IMAGE_NAME/web:$IMAGE_TAG
    environment:
      - DATABASE_NAME=${DATABASE_NAME}
      - DATABASE_USER=${DATABASE_USER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4"
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - app-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`${DOMAIN}`)"
      - "traefik.http.services.web.loadbalancer.server.port=8000"

  celery_worker:
    image: $DOCKER_REGISTRY/$IMAGE_NAME/celery-worker:$IMAGE_TAG
    environment:
      - DATABASE_NAME=${DATABASE_NAME}
      - DATABASE_USER=${DATABASE_USER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
    command: celery -A config worker --loglevel=info --concurrency=4
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - app-network

  celery_beat:
    image: $DOCKER_REGISTRY/$IMAGE_NAME/celery-beat:$IMAGE_TAG
    environment:
      - DATABASE_NAME=${DATABASE_NAME}
      - DATABASE_USER=${DATABASE_USER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
    command: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - app-network

  nginx:
    image: nginx:1.25
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/static
      - media_volume:/media
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - app-network

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  app-network:
    driver: bridge
EOF

# Запускаем контейнеры
echo "🚀 Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Проверяем здоровье сервисов
echo "🏥 Checking services health..."
sleep 30

# Выполняем миграции если нужно
echo "🔄 Running migrations..."
docker-compose -f $COMPOSE_FILE exec -T web python manage.py migrate

# Чистим старые образы
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment completed successfully!"