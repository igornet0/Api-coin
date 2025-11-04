from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CoinResponse(BaseModel):
    id: int
    name: str
    price_now: float
    max_price_now: float
    min_price_now: float
    open_price_now: float
    volume_now: float
    parsed: bool
    news_score_global: float
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True


class TimeseriesResponse(BaseModel):
    id: int
    coin_id: int
    timestamp: str
    path_dataset: str
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True


class DataTimeseriesResponse(BaseModel):
    id: int
    timeseries_id: int
    datetime: datetime
    open: float
    max: float
    min: float
    close: float
    volume: float

    class Config:
        from_attributes = True


class NewsResponse(BaseModel):
    id: int
    type: str
    id_url: int
    title: str
    text: str
    date: datetime

    class Config:
        from_attributes = True


class TelegramChannelResponse(BaseModel):
    id: int
    name: str
    chat_id: str
    parsed: bool

    class Config:
        from_attributes = True


class NewsUrlResponse(BaseModel):
    id: int
    url: str
    a_pup: float
    parsed: bool

    class Config:
        from_attributes = True


class ParsingTaskRequest(BaseModel):
    parser_type: str = Field(..., description="Тип парсера: kucoin_api, kucoin_driver, news_api, telegram_api")
    count: int = Field(default=100, description="Количество датасетов для парсинга")
    time_parser: str = Field(default="5m", description="Интервал времени (1m, 5m, 15m, 1h и т.д.)")
    pause: float = Field(default=60, description="Пауза между парсингом в минутах")
    miss: bool = Field(default=False, description="Парсить пропущенные данные")
    last_launch: bool = Field(default=False, description="Использовать последний запуск")
    clear: bool = Field(default=False, description="Очистить датасет")
    save: bool = Field(default=False, description="Сохранить датасет")
    save_type: str = Field(default="raw", description="Тип сохранения: raw, processed")
    coins: Optional[List[str]] = Field(default=None, description="Список монет для парсинга (если не указан, парсятся все активные монеты)")
    manual_stop: bool = Field(default=False, description="Режим парсинга до ручной остановки (игнорирует count)")


class ParsingTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None
    traceback: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ParsingTaskListItem(BaseModel):
    task_id: str
    parser_type: str
    status: str
    progress_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    manual_stop: bool = False
    coins: Optional[List[str]] = None

    class Config:
        from_attributes = True


class CoinCreateRequest(BaseModel):
    name: str = Field(..., description="Название монеты")
    price_now: float = Field(default=0, description="Текущая цена")
    parsed: bool = Field(default=True, description="Статус парсинга")


class CoinsUploadResponse(BaseModel):
    total: int
    added: int
    skipped: int
    errors: List[str] = []

