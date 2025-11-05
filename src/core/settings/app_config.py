from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

from .base import AppBaseConfig, BASE_DIR
from .config import LoggingConfig, ConfigDatabase


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="APP__")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)
    workers: int = Field(default=1)
    limit_concurrency: int = Field(default=10)

    frontend_host: str = Field(default="localhost")
    frontend_port: int = Field(default=3000)
    frontend_protocol: str = Field(default="http")

    @property
    def frontend_url(self) -> str:
        return f"{self.frontend_protocol}://{self.frontend_host}:{self.frontend_port}"

    @property
    def allowed_origins_urls(self) -> list[str]:
        # Return the configured frontend URL
        return [self.frontend_url]
    
    def get_allowed_origins(self, debug: bool = False) -> list[str]:
        """Get allowed origins based on environment"""
        origins = [self.frontend_url]
        
        # In development mode, add common localhost variants
        if debug:
            origins.extend([
                "http://localhost",
                "http://localhost:3000",
                "http://127.0.0.1",
                "http://127.0.0.1:3000",
            ])
        
        return list(set(origins))



class SecurityCongig(BaseSettings):
    
    model_config = SettingsConfigDict(**AppBaseConfig.__dict__, 
                                      env_prefix="SECURITY__")

    private_key_path: Path = BASE_DIR / "ssl" / "privkey.pem"
    public_key_path: Path = BASE_DIR / "ssl" / "pubkey.pem"
    certificate_path: Path = BASE_DIR / "ssl" / "certificate.pem"

    secret_key: str = Field(default=...)
    refresh_secret_key: str = Field(default=...)
    algorithm: str = Field(default="HS256")
    refresh_algorithm: str = Field(default="HS256")

    access_token_expire_minutes: int = Field(default=120)
    refresh_token_expire_days:int = Field(default=7)


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

class ConfigApp(BaseSettings):

    model_config = SettingsConfigDict(
        **AppBaseConfig.__dict__,
    )

    debug: bool = Field(default=True)

    app: AppConfig = Field(default_factory=AppConfig)
    security: SecurityCongig = Field(default_factory=SecurityCongig)
    rabbitmq: RabbitmqConfig = Field(default_factory=RabbitmqConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    database: ConfigDatabase = Field(default_factory=ConfigDatabase)

settings_app = ConfigApp()