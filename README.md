# KuCoin API Server

API сервер для работы с биржей KuCoin и сохранения данных в базу данных PostgreSQL.

## Возможности

- 🔄 Получение данных с биржи KuCoin (тикеры, свечи, статистика)
- 💾 Автоматическое сохранение данных в PostgreSQL
- 🌐 REST API для работы с данными
- 🔌 WebSocket для real-time данных
- 📊 Статистика и аналитика

## Установка

1. Установите зависимости:
```bash
poetry install
```

2. Настройте переменные окружения в файле `src/settings/prod.env`:
```env
# KuCoin API
KUCOIN__API_KEY=your_api_key
KUCOIN__API_SECRET=your_api_secret
KUCOIN__API_PASSPHRASE=your_passphrase

# Database
DATABASE__USER=your_db_user
DATABASE__PASSWORD=your_db_password
DATABASE__HOST=your_db_host
DATABASE__DB_NAME=your_db_name
DATABASE__PORT=5432
```

3. Убедитесь, что PostgreSQL запущен и доступен

## Запуск

```bash
python main.py
```

Сервер будет доступен по адресу: http://localhost:8080

## API Endpoints

### Market Data
- `GET /api/v1/market/symbols` - Список торговых пар
- `GET /api/v1/market/ticker/{symbol}` - Тикер для пары
- `GET /api/v1/market/tickers` - Все тикеры
- `GET /api/v1/market/stats/{symbol}` - 24h статистика
- `GET /api/v1/market/klines/{symbol}` - Свечные данные
- `GET /api/v1/market/currencies` - Список валют

### Синхронизация с БД
- `POST /api/v1/market/sync-ticker/{symbol}` - Синхронизировать тикер
- `POST /api/v1/market/sync-all-tickers` - Синхронизировать все тикеры

### Coins (База данных)
- `GET /api/v1/coins/` - Список монет из БД
- `GET /api/v1/coins/{coin_id}` - Монета по ID
- `GET /api/v1/coins/name/{coin_name}` - Монета по имени
- `PUT /api/v1/coins/{coin_id}` - Обновить монету
- `DELETE /api/v1/coins/{coin_id}` - Удалить монету
- `GET /api/v1/coins/stats/summary` - Статистика

### WebSocket
- `WS /api/v1/ws/connect` - WebSocket подключение
- `GET /api/v1/ws/topics` - Активные топики
- `POST /api/v1/ws/subscribe/{topic}` - Подписаться на топик
- `POST /api/v1/ws/unsubscribe/{topic}` - Отписаться от топика

## WebSocket Usage

Подключитесь к WebSocket и отправьте команды:

```javascript
// Подключение
const ws = new WebSocket('ws://localhost:8080/api/v1/ws/connect');

// Подписка на топик
ws.send(JSON.stringify({
    "type": "subscribe",
    "topic": "/market/ticker:BTC-USDT"
}));

// Отписка
ws.send(JSON.stringify({
    "type": "unsubscribe", 
    "topic": "/market/ticker:BTC-USDT"
}));

// Ping
ws.send(JSON.stringify({
    "type": "ping"
}));
```

## Примеры использования

### Получение тикера BTC-USDT
```bash
curl http://localhost:8080/api/v1/market/ticker/BTC-USDT
```

### Синхронизация тикера с БД
```bash
curl -X POST http://localhost:8080/api/v1/market/sync-ticker/BTC-USDT
```

### Получение всех монет из БД
```bash
curl http://localhost:8080/api/v1/coins/
```

## Документация API

После запуска сервера документация доступна по адресу:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Структура проекта

```
src/
├── app/
│   ├── create_app.py          # Создание FastAPI приложения
│   └── routers/               # API роутеры
│       ├── market.py          # Market data endpoints
│       ├── coins.py           # Database operations
│       └── websocket.py       # WebSocket endpoints
├── core/
│   ├── database/              # База данных
│   │   ├── models.py          # SQLAlchemy модели
│   │   ├── engine.py          # Настройка БД
│   │   └── orm/               # ORM запросы
│   ├── settings/              # Конфигурация
│   └── utils/                 # Утилиты
└── kucoin/                    # KuCoin SDK
    ├── client.py              # Основной клиент
    ├── ws_client.py           # WebSocket клиент
    └── model_data/            # Модули данных
```

## Требования

- Python 3.8+
- PostgreSQL 12+
- Poetry (для управления зависимостями)

