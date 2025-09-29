from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

import logging

from .base import LOG_DEFAULT_FORMAT

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class LoggingConfig(BaseSettings):

    model_config = SettingsConfigDict(env_prefix="LOGGING__", extra="ignore")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    format: str = LOG_DEFAULT_FORMAT
    
    access_log: bool = Field(default=True)

    @property
    def log_level(self) -> str:
        return getattr(logging, self.level)


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP__", extra="ignore")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    frontend_host: str = Field(default="localhost")
    frontend_port: int = Field(default=3000)
    frontend_protocol: str = Field(default="http")

    @property
    def frontend_url(self) -> str:
        return f"{self.frontend_protocol}://{self.frontend_host}:{self.frontend_port}"

    @property
    def allowed_origins_urls(self) -> list[str]:
        return [f"http://{self.host}:{self.port}",
                f"https://{self.host}:{self.port}",
                self.frontend_url,
                ]


class SecurityCongig(BaseSettings):
    
    model_config = SettingsConfigDict(env_prefix="SECURITY__", extra="ignore")

    private_key_path: Path = BASE_DIR / "ssl" / "privkey.pem"
    public_key_path: Path = BASE_DIR / "ssl" / "pubkey.pem"
    certificate_path: Path = BASE_DIR / "ssl" / "certificate.pem"

    secret_key: str = Field(default=...)
    refresh_secret_key: str = Field(default=...)
    algorithm: str = Field(default="HS256")
    refresh_algorithm: str = Field(default="HS256")

    access_token_expire_minutes: int = Field(default=120)
    refresh_token_expire_days:int = Field(default=7)


class KucoinConfig(BaseSettings):

    model_config = SettingsConfigDict(env_prefix="KUCOIN__", extra="ignore")

    api_key: str = Field(default="")
    api_secret: str = Field(default="")
    api_passphrase: str = Field(default="")
    
    @field_validator('api_key', 'api_secret', 'api_passphrase')
    @classmethod
    def validate_kucoin_credentials(cls, v):
        """Валидация обязательных параметров KuCoin API"""
        if not v:
            import warnings
            warnings.warn("KuCoin API credentials are empty", UserWarning)
        return v
    

class ConfigDatabase(BaseSettings):

    model_config = SettingsConfigDict(env_prefix="DATABASE__", extra="ignore")

    user: str = Field(default="")
    password: str = Field(default="")
    host: str = Field(default="localhost")
    db_name: str = Field(default="db_name")
    port: int = Field(default=5432)

    echo: bool = Field(default=False)
    echo_pool: bool = Field(default=False)
    pool_size: int = Field(default=20)
    max_overflow: int = 50
    pool_timeout: int = 5
    
    @field_validator('user', 'password')
    @classmethod
    def validate_db_credentials(cls, v):
        """Валидация обязательных параметров подключения к БД"""
        if not v:
            import warnings
            warnings.warn("Database credentials are empty", UserWarning)
        return v
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Валидация порта базы данных"""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator('pool_size')
    @classmethod
    def validate_pool_size(cls, v):
        """Валидация размера пула подключений"""
        if v < 1:
            raise ValueError("Pool size must be at least 1")
        return v

    naming_convention: dict = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
    
    def get_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
    
    @property
    def url(self) -> str:
        """URL для подключения к базе данных"""
        return self.get_url()


class Settings(BaseSettings):
    
    debug: bool = Field(default=True)
    app: AppConfig = Field(default_factory=AppConfig)
    security: SecurityCongig = Field(default_factory=SecurityCongig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    kucoin: KucoinConfig = Field(default_factory=KucoinConfig)
    database: ConfigDatabase = Field(default_factory=ConfigDatabase)

    