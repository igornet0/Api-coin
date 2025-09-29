from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

import logging
from .base import DevAppBaseConfig, LOG_DEFAULT_FORMAT
from .config import Settings, LoggingConfig, KucoinConfig, ConfigDatabase, AppConfig, SecurityCongig

class DevSettings(Settings):

    model_config = SettingsConfigDict(
        **DevAppBaseConfig,
    )

    debug: bool = Field(default=True)

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    security: SecurityCongig = Field(default_factory=SecurityCongig)
    kucoin: KucoinConfig = Field(default_factory=KucoinConfig)
    database: ConfigDatabase = Field(default_factory=ConfigDatabase)
    