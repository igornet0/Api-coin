"""
Rate limiting functionality for API requests
"""
from functools import wraps
from fastapi import HTTPException, Depends
from typing import Callable, Any
import logging

from core.database.orm import UserQuery
from app.configuration.auth import verify_authorization

logger = logging.getLogger(__name__)


async def check_api_key_rate_limit(api_key_id: int) -> bool:
    """
    Проверить лимиты API ключа перед выполнением запроса
    Возвращает True если запрос можно выполнить, иначе возбуждает HTTPException
    """
    try:
        can_proceed = await UserQuery.check_and_increment_request_count(api_key_id)
        
        if not can_proceed:
            # Получаем информацию об использовании для детального сообщения
            usage_info = await UserQuery.get_api_key_usage_info(api_key_id)
            
            if not usage_info['is_active']:
                raise HTTPException(
                    status_code=403, 
                    detail="API key is inactive"
                )
            
            raise HTTPException(
                status_code=429, 
                detail={
                    "message": "Rate limit exceeded",
                    "requests_count": usage_info['requests_count'],
                    "limit_requests": usage_info['limit_requests'],
                    "time_until_refresh_minutes": usage_info['time_until_refresh_minutes']
                }
            )
        
        return True
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def require_api_key_rate_limit(api_key_param: str = "api_key_id"):
    """
    Декоратор для проверки лимитов API ключа
    
    Args:
        api_key_param: Имя параметра, содержащего ID API ключа
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем API ключ из параметров
            api_key_id = kwargs.get(api_key_param)
            
            if not api_key_id:
                raise HTTPException(status_code=400, detail=f"Missing parameter: {api_key_param}")
            
            # Проверяем лимиты
            await check_api_key_rate_limit(api_key_id)
            
            # Выполняем оригинальную функцию
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def get_user_api_key_for_request(
    api_key_id: int, 
    user: dict = Depends(verify_authorization)
) -> int:
    """
    Dependency для проверки принадлежности API ключа пользователю и проверки лимитов
    """
    try:
        # Проверяем, принадлежит ли API ключ пользователю
        api_keys = await UserQuery.get_kucoin_api_keys_by_user_id(user.id)
        user_api_key_ids = [key.id for key in api_keys]
        
        if api_key_id not in user_api_key_ids:
            raise HTTPException(status_code=403, detail="Access denied: API key not owned by user")
        
        # Проверяем лимиты
        await check_api_key_rate_limit(api_key_id)
        
        return api_key_id
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key access: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
