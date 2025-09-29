__all__ = ("Database", "db_helper",
           "Coin", "Timeseries", 
           "DataTimeseries", "DataTimeseries",
           "Base")

from core.database.models import (Coin, Timeseries, DataTimeseries)
from core.database.engine import Database
from core.database.base import Base

from core.settings import get_settings

db_helper = None

def get_db_helper() -> Database:
    if db_helper is None:
        raise ValueError("Database not initialized. Call load_database() first.")
        
    return db_helper

def load_database() -> Database:
    global db_helper
    
    settings = get_settings()

    db_helper = Database(
        url=settings.database.url,
        echo=settings.database.echo,
        echo_pool=settings.database.echo_pool,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
    )

    return db_helper