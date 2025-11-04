# модели для БД
from sqlalchemy import (DateTime, ForeignKey, Float, String, 
                        BigInteger, Integer, Boolean, func, JSON)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class Coin(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    price_now: Mapped[float] = mapped_column(Float, default=0)

    max_price_now: Mapped[float] = mapped_column(Float, default=0)
    min_price_now: Mapped[float] = mapped_column(Float, default=0)
    open_price_now: Mapped[float] = mapped_column(Float, default=0)
    volume_now: Mapped[float] = mapped_column(Float, default=0)

    parsed: Mapped[bool] = mapped_column(Boolean, default=True)

    news_score_global: Mapped[float] = mapped_column(Float, default=0)

    timeseries: Mapped[list['Timeseries']] = relationship(back_populates='coin')
    parsing_configs: Mapped[list['ParsingConfigCoin']] = relationship(back_populates='coin')


class Timeseries(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey('coins.id'))  
    timestamp: Mapped[str] = mapped_column(String(50)) 
    path_dataset: Mapped[str] = mapped_column(String(100), unique=True)

    coin: Mapped['Coin'] = relationship(back_populates='timeseries')


class DataTimeseries(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timeseries_id: Mapped[int] = mapped_column(ForeignKey('timeseriess.id'))  
    datetime: Mapped[DateTime] = mapped_column(DateTime, nullable=False) 
    open: Mapped[float] = mapped_column(Float)
    max: Mapped[float] = mapped_column(Float)
    min: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)


class TelegramChannel(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    chat_id: Mapped[str] = mapped_column(String(50), unique=True)
    parsed: Mapped[bool] = mapped_column(Boolean, default=True)


class NewsUrl(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(200), unique=True)
    a_pup: Mapped[Float] = mapped_column(Float, default=0.9)
    parsed: Mapped[bool] = mapped_column(Boolean, default=True)


class News(Base):
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), default="news")
    id_url: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(String(100000), nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime, default=func.now())


class ParsingConfig(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    config: Mapped[dict] = mapped_column(JSON, default={})

    coins: Mapped[list['ParsingConfigCoin']] = relationship(back_populates='parsing_config')

    @property
    def coins_list(self) -> list[str]:
        return [coin.coin.name for coin in self.coins]

class ParsingConfigCoin(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parsing_config_id: Mapped[int] = mapped_column(ForeignKey('parsing_configs.id'))
    coin_id: Mapped[int] = mapped_column(ForeignKey('coins.id'))

    parsing_config: Mapped['ParsingConfig'] = relationship(back_populates='coins')
    coin: Mapped['Coin'] = relationship(back_populates='parsing_configs')


class ParsingTask(Base):
    """
    Модель для хранения задач парсинга в БД
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # ID задачи Celery
    task_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Параметры парсинга
    parser_type: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=100)
    time_parser: Mapped[str] = mapped_column(String(10), default="5m")
    pause: Mapped[float] = mapped_column(Float, default=60.0)
    miss: Mapped[bool] = mapped_column(Boolean, default=False)
    last_launch: Mapped[bool] = mapped_column(Boolean, default=False)
    clear: Mapped[bool] = mapped_column(Boolean, default=False)
    save: Mapped[bool] = mapped_column(Boolean, default=False)
    save_type: Mapped[str] = mapped_column(String(20), default="raw")
    coins: Mapped[dict] = mapped_column(JSON, default=None)  # Список монет в формате JSON
    manual_stop: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Статус задачи
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # Возможные статусы: pending, in_progress, completed, error, revoked
    
    # Прогресс и результат
    progress_message: Mapped[str] = mapped_column(String(500), default="")
    result: Mapped[dict | None] = mapped_column(JSON, default=None, nullable=True)
    error: Mapped[str | None] = mapped_column(String(1000), default=None, nullable=True)
    traceback: Mapped[str | None] = mapped_column(String(5000), default=None, nullable=True)
    
    # Временные метки
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    started_at: Mapped[DateTime] = mapped_column(DateTime, default=None, nullable=True)
    completed_at: Mapped[DateTime] = mapped_column(DateTime, default=None, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)