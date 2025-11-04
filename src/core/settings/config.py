from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

import logging

LOG_DEFAULT_FORMAT = '[%(asctime)s] %(name)-35s:%(lineno)-3d - %(levelname)-7s - %(message)s'

# Определяем путь к файлу конфигурации относительно корня проекта
# config.py находится в src/core/settings/, а prod.env в settings/
def _find_config_file() -> Path:
    """Находит файл конфигурации независимо от рабочей директории"""
    # Путь относительно расположения config.py (надежный способ - всегда работает)
    # __file__ = src/core/settings/config.py
    # parent = src/core/settings/
    # parent.parent = src/core/
    # parent.parent.parent = src/
    # parent.parent.parent.parent = корень проекта
    config_file_from_module = Path(__file__).resolve().parent.parent.parent.parent / "settings" / "prod.env"
    
    # Проверяем существование с абсолютным путем
    abs_path = config_file_from_module.resolve()
    if abs_path.exists():
        return abs_path
    
    # Пробуем относительно текущей рабочей директории
    config_file_from_cwd = Path.cwd() / "settings" / "prod.env"
    abs_path_cwd = config_file_from_cwd.resolve()
    if abs_path_cwd.exists():
        return abs_path_cwd
    
    # Пробуем на уровень выше (для запуска из src/)
    config_file_from_parent = Path.cwd().parent / "settings" / "prod.env"
    abs_path_parent = config_file_from_parent.resolve()
    if abs_path_parent.exists():
        return abs_path_parent
    
    # Если ничего не найдено, возвращаем путь относительно модуля (будет ошибка при загрузке)
    # Но это должно работать, так как это абсолютный путь
    return abs_path

_CONFIG_FILE = _find_config_file()

# Для отладки: убедимся, что файл найден
if not _CONFIG_FILE.exists():
    import sys
    print(f"ERROR: Config file not found at {_CONFIG_FILE}", file=sys.stderr)
    print(f"Current working directory: {Path.cwd()}", file=sys.stderr)
    print(f"Config file location: {Path(__file__).resolve()}", file=sys.stderr)
    raise FileNotFoundError(f"Configuration file not found: {_CONFIG_FILE}")

class AppBaseConfig:
    """Базовый класс для конфигурации с общими настройками"""
    case_sensitive = False
    env_file = str(_CONFIG_FILE)
    env_file_encoding = "utf-8"
    env_nested_delimiter="__"
    extra = "ignore"


class LoggingConfig(BaseSettings):
    
    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="LOGGING__")
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    format: str = LOG_DEFAULT_FORMAT
    
    access_log: bool = Field(default=True)

    @property
    def log_level(self) -> int:
        return getattr(logging, self.level)
    

class TelegramConfig(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="TG__")
    api_id: str = Field(default=...)
    api_hash: str = Field(default=...)
    phone: str = Field(default=...)


class ConfigParserDriver(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="DRIVER__")
    
    url_parsing: str = Field(default=...)

    show_browser: bool = Field(default=True)
    window_size_w: int = Field(default=780)
    window_size_h: int = Field(default=700)

    @property
    def window_size(self) -> tuple[int]:
        return self.window_size_w, self.window_size_h
    
    def get_url(self, coin: str) -> str:
        return self.url_parsing.replace("{coin}", coin)
    

class ConfigDatabase(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="DATABASE__")
    
    user: str = Field(default=...)
    password: str = Field(default=...)
    host: str = Field(default="localhost")
    db_name: str = Field(default="db_name")
    port: int = Field(default=5432)

    echo: bool = Field(default=False)
    echo_pool: bool = Field(default=False)
    pool_size: int = Field(default=20)
    max_overflow: int = 50
    pool_timeout: int = 5

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
    
    def get_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


class KucoinConfig(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="KUCOIN__")
    
    api_key: str = Field(default=...)
    api_secret: str = Field(default=...)
    api_passphrase: str = Field(default=...)


class CoindeskConfig(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="COINDESK__")
    
    api_key: str = Field(default=...)


class AppConfig(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="APP__")
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    workers: int = Field(default=1)
    timeout: int = Field(default=30)
    limit_concurrency: int = Field(default=10)
    limit_max_requests: int = Field(default=1000)
    limit_max_requests_jitter: int = Field(default=100)
    limit_max_requests_jitter_backoff: int = Field(default=100)
    limit_max_requests_jitter_backoff_factor: int = Field(default=100)

class RabbitmqConfig(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="RABBITMQ__")
    
    host: str = Field(default=...)
    user: str = Field(default=...)
    password: str = Field(default=...)
    port: int = Field(default=5672)

    @property
    def broker_url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}//"

class RedisConfig(BaseSettings):

    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="REDIS__")
    
    host: str = Field(default=...)
    port: int = Field(default=6379)

    @property
    def backend_url(self) -> str:
        return f"redis://{self.host}:{self.port}/0"

class ConfigParser(BaseSettings):

    model_config = SettingsConfigDict(
        **AppBaseConfig.__dict__,
    )

    kucoin: KucoinConfig = Field(default_factory=KucoinConfig)

    app: AppConfig = Field(default_factory=AppConfig)
    rabbitmq: RabbitmqConfig = Field(default_factory=RabbitmqConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    driver: ConfigParserDriver = Field(default_factory=ConfigParserDriver)
    database: ConfigDatabase = Field(default_factory=ConfigDatabase)
    tg: TelegramConfig = Field(default_factory=TelegramConfig)
    coindesk: CoindeskConfig = Field(default_factory=CoindeskConfig)

settings = ConfigParser()