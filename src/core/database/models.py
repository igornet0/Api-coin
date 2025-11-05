# модели для БД
from pyclbr import Class

from sqlalchemy import (DateTime, ForeignKey, Float, String, 
                        BigInteger, Integer, Boolean, func, JSON)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class User(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(50), unique=True)

    balance: Mapped[int] = mapped_column(Float, default=0)

    role: Mapped[str] = mapped_column(String(50), default="user")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_2fa_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    kucoin_api_keys: Mapped[list['KucoinApiKey']] = relationship(back_populates='user')
    request_logs: Mapped[list['RequestLog']] = relationship(back_populates='user')
    orders: Mapped[list['Order']] = relationship(back_populates='user')
    portfolio: Mapped[list['Portfolio']] = relationship(back_populates='user')


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
    portfolio: Mapped[list['Portfolio']] = relationship(back_populates='coin')


class Timeseries(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey('coins.id'))  
    timestamp: Mapped[str] = mapped_column(String(50)) 
    path_dataset: Mapped[str] = mapped_column(String(100))

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


class KucoinApiKey(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String(50))
    api_key: Mapped[str] = mapped_column(String(50), unique=True)
    api_secret: Mapped[str] = mapped_column(String(50), unique=True)
    api_passphrase: Mapped[str] = mapped_column(String(50), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    limit_requests: Mapped[int] = mapped_column(Integer, default=1000)
    requests_count: Mapped[int] = mapped_column(Integer, default=0)
    timedelta_refresh: Mapped[int] = mapped_column(Integer, default=60)
    next_refresh: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    user: Mapped['User'] = relationship(back_populates='kucoin_api_keys')
    request_logs: Mapped[list['KucoinApiKeyRequestLog']] = relationship(back_populates='kucoin_api_key')
    orders: Mapped[list['Order']] = relationship(back_populates='kucoin_api_key')
    portfolio: Mapped[list['Portfolio']] = relationship(back_populates='kucoin_api_key')


class Portfolio(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    kucoin_api_key_id: Mapped[int] = mapped_column(ForeignKey('kucoin_api_keys.id'))
    coin_id: Mapped[int] = mapped_column(ForeignKey('coins.id'))
    amount: Mapped[float] = mapped_column(Float)
    average_price: Mapped[float] = mapped_column(Float)

    user: Mapped['User'] = relationship(back_populates='portfolio')
    kucoin_api_key: Mapped['KucoinApiKey'] = relationship(back_populates='portfolio')
    coin: Mapped['Coin'] = relationship(back_populates='portfolio')


class Order(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    kucoin_api_key_id: Mapped[int] = mapped_column(ForeignKey('kucoin_api_keys.id'))
    exchange_order_id: Mapped[str] = mapped_column(String(100))
    coin_id: Mapped[int] = mapped_column(ForeignKey('coins.id'))
    order_type: Mapped[str] = mapped_column(String(50)) # limit or market
    side: Mapped[str] = mapped_column(String(50)) # buy or sell
    size: Mapped[float] = mapped_column(Float) # size of the order
    price: Mapped[float] = mapped_column(Float) # price of the order
    status: Mapped[str] = mapped_column(String(50), default='open') # open or closed

    user: Mapped['User'] = relationship(back_populates='orders')
    kucoin_api_key: Mapped['KucoinApiKey'] = relationship(back_populates='orders')
    

class RequestLog(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    request_type: Mapped[str] = mapped_column(String(50))
    request_data: Mapped[str] = mapped_column(String(100000))
    response_data: Mapped[str] = mapped_column(String(100000))
    status_code: Mapped[int] = mapped_column(Integer)

    user: Mapped['User'] = relationship(back_populates='request_logs')
    kucoin_api_key_request_logs: Mapped[list['KucoinApiKeyRequestLog']] = relationship(back_populates='request_log')


class KucoinApiKeyRequestLog(Base):

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kucoin_api_key_id: Mapped[int] = mapped_column(ForeignKey('kucoin_api_keys.id'))
    request_log_id: Mapped[int] = mapped_column(ForeignKey('request_logs.id'))

    kucoin_api_key: Mapped['KucoinApiKey'] = relationship(back_populates='request_logs')
    request_log: Mapped['RequestLog'] = relationship(back_populates='kucoin_api_key_request_logs')


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