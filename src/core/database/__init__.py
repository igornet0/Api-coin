__all__ = ("Database", "db_helper",
           "Coin", "Timeseries", "News",
           "DataTimeseries", "DataTimeseries",
           "Base")

from .models import (Coin, Timeseries, DataTimeseries, News)
from .engine import Database
from .base import Base

from src.core.settings import settings_parser

db_helper = None

def get_db_helper() -> Database:
    global db_helper
    
    if db_helper is None:
        load_database()
        
    return db_helper

def load_database() -> Database:
    global db_helper

    db_helper = Database(
        url=settings_parser.database.url,
        echo=settings_parser.database.echo,
        echo_pool=settings_parser.database.echo_pool,
        pool_size=settings_parser.database.pool_size,
        max_overflow=settings_parser.database.max_overflow,
    )

    return db_helper