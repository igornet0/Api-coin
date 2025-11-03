from src.core import settings
from celery import Celery

celery_app = Celery(
    "parser_kucoin",
    broker=settings.rabbitmq.broker_url,
    backend=settings.redis.backend_url,
    include=["app.tasks"]
)

celery_app.conf.update(
    # Сериализация
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Время и часовой пояс
    timezone="UTC",
    enable_utc=True,
    
    # Отслеживание задач
    task_track_started=True,
    
    # Лимиты времени выполнения
    task_time_limit=3600,
    task_soft_time_limit=3300,
    
    # Восстановление задач после перезагрузки
    # Задачи подтверждаются только после успешного выполнения
    task_acks_late=True,
    
    # Задачи перераспределяются при падении воркера
    task_reject_on_worker_lost=True,
    
    # Персистентные сообщения (сохраняются на диске RabbitMQ)
    task_default_delivery_mode=2,  # 2 = persistent
    
    # Время хранения результатов (1 день)
    result_expires=86400,
    
    # Настройки для параллельной обработки задач
    # Количество задач, которые воркер может получить заранее (для оптимизации)
    # Равно concurrency для оптимального распределения
    worker_prefetch_multiplier=1,  # Получать только 1 задачу на воркер за раз (честное распределение)
    
    # Настройки для RabbitMQ (персистентные очереди)
    broker_transport_options={
        "fanout_prefix": True,
        "fanout_patterns": True,
    },
)

