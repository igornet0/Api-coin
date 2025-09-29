from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

import logging
from .base import ProdAppBaseConfig, LOG_DEFAULT_FORMAT
from .config import Settings, LoggingConfig, KucoinConfig, ConfigDatabase, AppConfig, SecurityCongig

class ProdSettings(Settings):

    model_config = SettingsConfigDict(
        **ProdAppBaseConfig,
    )

    debug: bool = Field(default=False)

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    security: SecurityCongig = Field(default_factory=SecurityCongig)
    kucoin: KucoinConfig = Field(default_factory=KucoinConfig)
    database: ConfigDatabase = Field(default_factory=ConfigDatabase)
    