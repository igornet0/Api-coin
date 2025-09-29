from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from core.database.orm import UserQuery
from core.database.models import KucoinApiKey
from app.configuration import Server, verify_authorization
from app.configuration.schemas.user import KucoinApiKeyCreate, KucoinApiKeyResponse

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api-keys", tags=["api-keys"], dependencies=[Depends(http_bearer)])
logger = logging.getLogger("app.user_api_keys")


@router.post("/", response_model=KucoinApiKeyResponse)
async def create_api_key(
    api_key_data: KucoinApiKeyCreate,
    user: dict = Depends(verify_authorization),
):
    """Создать новый API ключ для пользователя"""
    try:
        api_key = await UserQuery.create_kucoin_api_key(
            user_id=user.id,
            name=api_key_data.name,
            api_key=api_key_data.api_key,
            api_secret=api_key_data.api_secret,
            api_passphrase=api_key_data.api_passphrase,
            limit_requests=api_key_data.limit_requests,
            timedelta_refresh=api_key_data.timedelta_refresh
        )
        
        return KucoinApiKeyResponse(
            id=api_key.id,
            name=api_key.name,
            api_key=api_key.api_key,
            is_active=api_key.is_active,
            limit_requests=api_key.limit_requests,
            requests_count=api_key.requests_count,
            timedelta_refresh=api_key.timedelta_refresh,
            next_refresh=api_key.next_refresh
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[KucoinApiKeyResponse])
async def get_user_api_keys(
    user: dict = Depends(verify_authorization),
    session: AsyncSession = Depends(Server.get_db)
):
    """Получить все API ключи пользователя"""
    try:
        api_keys = await UserQuery.get_kucoin_api_keys_by_user_id(user.id)
        
        return [
            KucoinApiKeyResponse(
                id=key.id,
                name=key.name,
                api_key=key.api_key,
                is_active=key.is_active,
                limit_requests=key.limit_requests,
                requests_count=key.requests_count,
                timedelta_refresh=key.timedelta_refresh,
                next_refresh=key.next_refresh
            ) for key in api_keys
        ]
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{api_key_id}", response_model=KucoinApiKeyResponse)
async def update_api_key(
    api_key_id: int,
    api_key_data: KucoinApiKeyCreate,
    user: dict = Depends(verify_authorization)
):
    """Обновить API ключ пользователя"""
    try:
        # Проверяем, принадлежит ли API ключ пользователю
        api_keys = await UserQuery.get_kucoin_api_keys_by_user_id(user.id)
        user_api_key_ids = [key.id for key in api_keys]
        
        if api_key_id not in user_api_key_ids:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Обновляем API ключ
        updated_key = await UserQuery.update_kucoin_api_key(
            api_key_id=api_key_id,
            name=api_key_data.name,
            api_key=api_key_data.api_key if api_key_data.api_key else None,
            api_secret=api_key_data.api_secret if api_key_data.api_secret else None,
            api_passphrase=api_key_data.api_passphrase if api_key_data.api_passphrase else None,
            limit_requests=api_key_data.limit_requests,
            timedelta_refresh=api_key_data.timedelta_refresh
        )
        
        return KucoinApiKeyResponse(
            id=updated_key.id,
            name=updated_key.name,
            api_key=updated_key.api_key,
            is_active=updated_key.is_active,
            limit_requests=updated_key.limit_requests,
            requests_count=updated_key.requests_count,
            timedelta_refresh=updated_key.timedelta_refresh,
            next_refresh=updated_key.next_refresh
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    user: dict = Depends(verify_authorization),
    session: AsyncSession = Depends(Server.get_db)
):
    """Удалить API ключ"""
    try:
        # Проверяем, что ключ принадлежит пользователю
        user_api_keys = await UserQuery.get_kucoin_api_keys_by_user_id(user.id)
        api_key = next((key for key in user_api_keys if key.id == api_key_id), None)
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        success = await UserQuery.delete_kucoin_api_key(api_key_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete API key")
        
        return {"message": "API key deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{api_key_id}/toggle")
async def toggle_api_key_status(
    api_key_id: int,
    user: dict = Depends(verify_authorization),
    session: AsyncSession = Depends(Server.get_db)
):
    """Переключить статус активности API ключа"""
    try:
        # Проверяем, что ключ принадлежит пользователю
        user_api_keys = await UserQuery.get_kucoin_api_keys_by_user_id(user.id)
        api_key = next((key for key in user_api_keys if key.id == api_key_id), None)
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        updated_key = await UserQuery.toggle_kucoin_api_key_status(api_key_id)
        
        return KucoinApiKeyResponse(
            id=updated_key.id,
            name=updated_key.name,
            api_key=updated_key.api_key,
            is_active=updated_key.is_active,
            limit_requests=updated_key.limit_requests
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling API key status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{api_key_id}/usage", response_model=dict)
async def get_api_key_usage(
    api_key_id: int,
    user: dict = Depends(verify_authorization)
):
    """Получить информацию об использовании API ключа"""
    try:
        # Проверяем, принадлежит ли API ключ пользователю
        api_keys = await UserQuery.get_kucoin_api_keys_by_user_id(user.id)
        user_api_key_ids = [key.id for key in api_keys]
        
        if api_key_id not in user_api_key_ids:
            raise HTTPException(status_code=403, detail="Access denied")
        
        usage_info = await UserQuery.get_api_key_usage_info(api_key_id)
        return usage_info
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting API key usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
