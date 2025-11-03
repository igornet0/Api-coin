# Docker Configuration

Docker конфигурация для запуска парсера KuCoin в контейнерах.

## Структура

- `Dockerfile` - образ для приложения и Celery worker
- `docker-compose.yml` - оркестрация всех сервисов
- `.dockerignore` - файлы, исключенные из сборки
- `.env.example` - пример переменных окружения

## Быстрый старт

### 1. Подготовка окружения

Создайте файл `.env` в корне проекта на основе `docker/.env.example`:

```bash
cp docker/.env.example .env
```

### 2. Настройка конфигурации

Убедитесь, что файл `settings/prod.env` содержит все необходимые настройки (API ключи и т.д.)

### 3. Запуск через Makefile

```bash
# Собрать образы
make build

# Запустить все сервисы
make up

# Просмотр логов
make logs

# Остановить сервисы
make down
```

### 4. Запуск через Docker Compose напрямую

```bash
cd docker
docker-compose up -d
```

## Доступные сервисы

После запуска будут доступны:

- **FastAPI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Команды Makefile

### Основные команды

```bash
make help          # Показать все доступные команды
make build         # Собрать Docker образы
make up            # Запустить все сервисы
make down          # Остановить все сервисы
make restart       # Перезапустить все сервисы
make ps            # Показать статус сервисов
```

### Логи

```bash
make logs           # Логи всех сервисов
make logs-app       # Логи приложения
make logs-celery    # Логи Celery worker
make logs-db        # Логи базы данных
```

### Управление отдельными сервисами

```bash
make start-app      # Запустить только приложение
make stop-app       # Остановить приложение
make restart-app    # Перезапустить приложение
make start-celery   # Запустить Celery
make stop-celery    # Остановить Celery
```

### Работа с базой данных

```bash
make db-shell       # Подключиться к PostgreSQL
make db-backup      # Создать резервную копию БД
make db-restore     # Восстановить БД (FILE=backups/backup.sql)
make db-migrate     # Запустить миграции
```

### Разработка

```bash
make shell          # Открыть shell в контейнере приложения
make celery-shell   # Открыть shell в контейнере Celery
make dev            # Собрать, запустить и показать логи
```

### Очистка

```bash
make clean          # Остановить и удалить контейнеры и volumes
make clean-all      # Полная очистка включая образы
```

### Мониторинг

```bash
make health         # Проверить статус здоровья сервисов
make stats          # Показать статистику использования ресурсов
```

## Структура сервисов

### 1. PostgreSQL (postgres)
База данных для хранения данных парсинга.

### 2. RabbitMQ (rabbitmq)
Брокер сообщений для Celery.

### 3. Redis (redis)
Кеш и backend для Celery (опционально).

### 4. FastAPI (app)
Основное приложение API.

### 5. Celery Worker (celery)
Воркер для обработки задач парсинга.

### 6. Celery Beat (celery-beat)
Планировщик для периодических задач (опционально).

## Переменные окружения

Основные переменные окружения настраиваются в `docker-compose.yml`:

- `DATABASE__USER` - пользователь БД (по умолчанию: postgres)
- `DATABASE__PASSWORD` - пароль БД (по умолчанию: postgres)
- `DATABASE__DB_NAME` - имя БД (по умолчанию: parser_kucoin)
- `RABBITMQ_USER` - пользователь RabbitMQ (по умолчанию: guest)
- `RABBITMQ_PASSWORD` - пароль RabbitMQ (по умолчанию: guest)

Дополнительные настройки (API ключи и т.д.) берутся из `settings/prod.env`.

## Volumes

Следующие директории сохраняются как volumes:

- `postgres_data` - данные PostgreSQL
- `rabbitmq_data` - данные RabbitMQ
- `redis_data` - данные Redis
- `app_data` - данные приложения

Для разработки исходный код монтируется как volume для hot-reload.

## Troubleshooting

### Проблемы с подключением к БД

Убедитесь, что PostgreSQL полностью запущен:
```bash
make logs-db
```

Проверьте healthcheck:
```bash
make health
```

### Проблемы с RabbitMQ

Проверьте доступность RabbitMQ Management UI: http://localhost:15672

### Пересборка образов

При изменении зависимостей:
```bash
make rebuild
```

### Очистка данных

ВНИМАНИЕ: Это удалит все данные!
```bash
make clean
```

## Производственное использование

Для production рекомендуется:

1. Изменить пароли в `.env` файле
2. Использовать внешние сервисы БД, RabbitMQ, Redis
3. Настроить SSL/TLS для сервисов
4. Использовать secrets management
5. Настроить мониторинг и логирование
6. Использовать docker-compose.prod.yml для production конфигурации

