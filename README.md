# PythonProject5 Tracker

Django-приложение для управления привычками с напоминаниями через Telegram-бота.

## Описание

Приложение позволяет отслеживать привычки и получать напоминания через Telegram-бота. Использует Django в качестве основного фреймворка, Celery для асинхронных задач, Redis как брокер сообщений и PostgreSQL для хранения данных.

## Технологии

- Python 3.11
- Django
- PostgreSQL 15
- Redis 7
- Celery
- Docker & Docker Compose
- Nginx
- Gunicorn

## Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/andyAlem/PythonProject5_tracker.git
cd PythonProject5_tracker
```

2. Создайте файл с переменными окружения:
```bash
cp .env.example .env
```

3. Заполните `.env` файл:
```env
NAME=habits_db_name
USER=habits_user_name
PASSWORD=secure_password
SECRET_KEY=your-django-secret-key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

4. Запустите проект:
```bash
docker compose up -d
```

5. Создайте суперпользователя:
```bash
docker compose exec web python manage.py createsuperuser
```

Приложение будет доступно по адресу: http://localhost

## Структура проекта

```
PythonProject5_tracker/
├── config/                 # Конфигурация Django
├── apps/                   # Приложения Django
├── static/                 # Статические файлы
├── media/                  # Медиа файлы
├── requirements.txt        # Python зависимости
├── Dockerfile             # Docker образ приложения
├── docker-compose.yml     # Docker Compose конфигурация
├── nginx.conf             # Конфигурация Nginx
└── .github/workflows/     # GitHub Actions
```

## Переменные окружения

### Обязательные переменные:
- `NAME` - название базы данных
- `USER` - пользователь базы данных  
- `PASSWORD` - пароль базы данных
- `SECRET_KEY` - секретный ключ Django
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота

### Дополнительные переменные:
- `DEBUG` - режим отладки (по умолчанию False)
- `ALLOWED_HOSTS` - разрешенные хосты
- `HOST` - хост базы данных (по умолчанию db)
- `PORT` - порт базы данных (по умолчанию 5432)

## Деплой на сервер

### Подготовка сервера

1. Обновите систему:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Установите Docker:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

3. Установите Docker Compose:
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

4. Перезагрузите сервер:
```bash
sudo reboot
```

### Настройка SSH ключей

1. Создайте SSH ключ на сервере:
```bash
ssh-keygen -t rsa -b 4096 -C "deploy@habits-tracker"
```

2. Добавьте публичный ключ в authorized_keys:
```bash
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

3. Скопируйте приватный ключ для GitHub Actions:
```bash
cat ~/.ssh/id_rsa
```

### Настройка проекта на сервере

1. Создайте директорию для проекта:
```bash
mkdir -p ~/habits-tracker
cd ~/habits-tracker
```

2. Клонируйте репозиторий:
```bash
git clone https://github.com/andyAlem/PythonProject5_tracker.git .
```

3. Создайте .env файл с продакшн настройками:
```bash
nano .env
```

```env
NAME=habits_prod
USER=habits_user
PASSWORD=VerySecurePassword123
SECRET_KEY=your-64-character-production-secret-key
TELEGRAM_BOT_TOKEN=your_production_telegram_bot_token
DEBUG=False
```

4. Создайте продакшн версию docker-compose:
```bash
nano docker-compose.prod.yml
```

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: ${NAME}
      POSTGRES_USER: ${USER}
      POSTGRES_PASSWORD: ${PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn --bind 0.0.0.0:8000 --workers 3 config.wsgi:application"
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    expose:
      - "8000"
    environment:
      - NAME=${NAME}
      - USER=${USER}
      - PASSWORD=${PASSWORD}
      - HOST=db
      - PORT=5432
      - SECRET_KEY=${SECRET_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery:
    build: .
    command: celery -A config worker -l info
    environment:
      - NAME=${NAME}
      - USER=${USER}
      - PASSWORD=${PASSWORD}
      - HOST=db
      - PORT=5432
      - SECRET_KEY=${SECRET_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - NAME=${NAME}
      - USER=${USER}
      - PASSWORD=${PASSWORD}
      - HOST=db
      - PORT=5432
      - SECRET_KEY=${SECRET_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

5. Запустите проект:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

6. Создайте суперпользователя:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### GitHub Actions настройки

Добавьте в Settings → Secrets and variables → Actions:

- `SSH_PRIVATE_KEY` - приватный SSH ключ
- `SERVER_HOST` - IP адрес сервера
- `SSH_USERNAME` - имя пользователя
- `DEPLOY_DIR` - путь к проекту на сервере

### Обновление GitHub Actions workflow

Замените содержимое файла `.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_USER: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install flake8

      - name: Create .env file
        run: |
          echo "SECRET_KEY=test-secret-key-for-github-actions" >> .env
          echo "NAME=test_db" >> .env
          echo "USER=postgres" >> .env
          echo "PASSWORD=postgres" >> .env
          echo "HOST=localhost" >> .env
          echo "PORT=5432" >> .env
          echo "TELEGRAM_BOT_TOKEN=test-bot-token" >> .env

      - name: Run linting
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run migrations
        run: python manage.py migrate

      - name: Run tests
        run: python manage.py test

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.7
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SSH_USERNAME }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ${{ secrets.DEPLOY_DIR }}
            git pull origin main
            docker compose -f docker-compose.prod.yml down
            docker compose -f docker-compose.prod.yml up -d --build
            docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate
            docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
```

## Полезные команды

### Локальная разработка
```bash
# Запуск сервисов
docker compose up -d

# Просмотр логов
docker compose logs web
docker compose logs celery

# Выполнение команд Django
docker compose exec web python manage.py shell
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Остановка сервисов
docker compose down
```

### Продакшн сервер
```bash
# Запуск
docker compose -f docker-compose.prod.yml up -d

# Просмотр статуса
docker compose -f docker-compose.prod.yml ps

# Просмотр логов
docker compose -f docker-compose.prod.yml logs web

# Обновление проекта
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build

# Выполнение миграций
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Сбор статики
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Отладка

### Проблемы с SSH
```bash
# Проверка подключения
ssh -T git@github.com

# Проверка прав на файлы SSH
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa ~/.ssh/authorized_keys
```

### Проблемы с Docker
```bash
# Просмотр всех контейнеров
docker ps -a

# Просмотр логов конкретного контейнера
docker logs container_name

# Очистка системы Docker
docker system prune -a
```

### Проблемы с базой данных
```bash
# Подключение к базе данных
docker compose exec db psql -U habits_user -d habits_db

# Проверка состояния базы
docker compose exec web python manage.py dbshell
```

## Мониторинг

Для мониторинга состояния приложения используйте:

```bash
# Проверка статуса всех сервисов
docker compose -f docker-compose.prod.yml ps

# Проверка использования ресурсов
docker stats

# Проверка работы веб-сервера
curl http://localhost

# Проверка работы API
curl http://localhost/api/
```

## Резервное копирование

### Создание резервной копии базы данных
```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U habits_user habits_db > backup.sql
```

### Восстановление из резервной копии
```bash
docker compose -f docker-compose.prod.yml exec -T db psql -U habits_user habits_db < backup.sql
```

## Безопасность

1. Используйте сильные пароли для базы данных
2. Регулярно обновляйте зависимости
3. Настройте файрвол на сервере
4. Используйте HTTPS в продакшене
5. Ограничьте доступ по SSH только по ключам

## Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Убедитесь, что все сервисы запущены
3. Проверьте конфигурацию переменных окружения
4. Обратитесь к документации Django и Docker