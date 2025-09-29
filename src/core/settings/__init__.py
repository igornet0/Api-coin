__all__ = ("load_settings", "get_settings", "auto_load_settings")

import os
from typing import Literal, Optional
from .dev_config import DevSettings
from .prod_config import ProdSettings

settings = None

def get_settings():
    """Получить текущие настройки приложения"""
    if settings is None:
        raise ValueError("Settings are not loaded. Call load_settings() first.")
        
    return settings

def load_settings(env: Literal["prod", "dev"]):
    """
    Загрузить настройки для указанной среды
    
    Args:
        env: Среда выполнения ('prod' или 'dev')
    """
    global settings

    if env == "prod":
        settings = ProdSettings()
    elif env == "dev":
        settings = DevSettings()
    else:
        raise ValueError(f"Invalid environment: {env}. Must be 'prod' or 'dev'")
    
    return settings

def auto_load_settings(env: Optional[Literal["prod", "dev"]] = None):
    """
    Автоматически загрузить настройки
    
    Приоритет определения среды:
    1. Параметр env
    2. Переменная окружения ENVIRONMENT
    3. Переменная окружения ENV
    4. По умолчанию 'dev'
    
    Args:
        env: Среда выполнения (опционально)
    
    Returns:
        Экземпляр настроек
    """
    if env is None:
        # Пытаемся определить среду из переменных окружения
        env = os.getenv("ENVIRONMENT") or os.getenv("ENV") or "dev"
        
        # Нормализация значений
        env = env.lower()
        if env in ["production", "prod"]:
            env = "prod"
        elif env in ["development", "dev", "debug"]:
            env = "dev"
    
    return load_settings(env)

def is_settings_loaded() -> bool:
    """Проверить, загружены ли настройки"""
    return settings is not None