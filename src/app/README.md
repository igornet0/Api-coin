# FastAPI Parser Application

Простое FastAPI приложение для просмотра данных из базы данных и управления парсингом через RabbitMQ и Celery.

## Структура приложения

```
app/
├── __init__.py
├── main.py              # Главный файл FastAPI приложения
├── schemas.py           # Pydantic схемы для валидации
├── dependencies.py      # Зависимости FastAPI
├── celery_app.py        # Конфигурация Celery
├── tasks.py             # Celery задачи для парсинга
└── api/
    └── routes/
        ├── coins.py     # Роутеры для работы с монетами
        ├── news.py      # Роутеры для работы с новостями
        └── parsing.py   # Роутеры для управления парсингом
```

## Запуск приложения

### 1. Установка зависимостей

```bash
poetry install
```

### 2. Запуск RabbitMQ

Убедитесь, что RabbitMQ запущен. Можно использовать Docker:

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

RabbitMQ будет доступен на:
- AMQP: `localhost:5672`
- Web UI: `http://localhost:15672` (guest/guest)

### 3. Запуск Celery Worker

В отдельном терминале запустите Celery worker:

```bash
cd src
celery -A app.celery_app worker --loglevel=info
```

### 4. Запуск FastAPI приложения

```bash
cd src
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно на `http://localhost:8000`

### 5. Документация API

После запуска приложения документация доступна по адресам:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Coins (Монеты)

- `GET /coins` - Получить список всех монет
- `GET /coins/{coin_name}` - Получить информацию о монете
- `GET /coins/{coin_name}/timeseries` - Получить временные ряды для монеты
- `GET /coins/timeseries/{timeseries_id}/data` - Получить данные временного ряда

### News (Новости)

- `GET /news` - Получить список новостей
- `GET /news/urls` - Получить список URL новостей
- `GET /news/urls/{url_id}` - Получить информацию о URL новости
- `GET /news/channels` - Получить список Telegram каналов
- `GET /news/channels/{channel_id}` - Получить информацию о Telegram канале

### Parsing (Парсинг)

- `POST /parsing/start` - Запустить задачу парсинга
- `GET /parsing/status/{task_id}` - Получить статус задачи
- `POST /parsing/stop/{task_id}` - Остановить задачу парсинга

## Примеры использования

### Запуск парсинга

```bash
curl -X POST "http://localhost:8000/parsing/start" \
  -H "Content-Type: application/json" \
  -d '{
    "parser_type": "kucoin_api",
    "count": 100,
    "time_parser": "5m",
    "pause": 60,
    "save": true
  }'
```

### Проверка статуса задачи

```bash
curl "http://localhost:8000/parsing/status/{task_id}"
```

### Получение списка монет

```bash
curl "http://localhost:8000/coins"
```

## Доступные типы парсеров

- `kucoin_api` - Парсер KuCoin через API
- `kucoin_driver` - Парсер KuCoin через веб-драйвер
- `news_api` - Парсер новостей через API
- `telegram_api` - Парсер Telegram каналов

## Конфигурация

Конфигурация Celery находится в `app/celery_app.py`. По умолчанию используется:
- Broker: `amqp://guest:guest@localhost:5672//` (RabbitMQ)
- Backend: `rpc://` (для хранения результатов задач)

Для изменения настроек отредактируйте файл `app/celery_app.py`.

