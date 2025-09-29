import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

# from .tasks import tasks
# from .rabbitmq_server import rabbit
from core import settings
from core.database import get_db_helper

db_helper = get_db_helper()
import logging

def configure_logging(logging_config):
    """Настройка логирования"""
    logging.basicConfig(
        level=logging_config.log_level,
        format=logging_config.format
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    configure_logging(settings.logging)
    logger = logging.getLogger(__name__)
    logger.info("Starting up KuCoin API server...")
    
    # Создаем таблицы в БД
    await db_helper.init_db()
    logger.info("Database tables created/verified")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KuCoin API server...")
    await db_helper.dispose()