from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer
from typing import Optional
import logging

from core.database.orm import CoinQuery
from core.database.models import Coin
from app.configuration.rate_limiting import get_user_api_key_for_request
from app.configuration.auth import verify_authorization

http_bearer = HTTPBearer(auto_error=False)


router = APIRouter(prefix="/coin_api", tags=["coin_api"], dependencies=[Depends(http_bearer)])
logger = logging.getLogger("app.coin_api")

coin_query = CoinQuery()

@router.get("/")
async def get_coins(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    parsed_only: Optional[bool] = Query(None, description="Фильтр по статусу парсинга")
):
    """Получить список монет из базы данных"""
    try:
        coins = await coin_query.get_coins(skip=skip, limit=limit, parsed_only=parsed_only)
        return {
            "coins": coins,
            "skip": skip,
            "limit": limit,
            "count": len(coins)
        }
    except Exception as e:
        logger.error(f"Error getting coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{coin_id}")
async def get_coin(coin_id: int):
    """Получить конкретную монету по ID"""
    try:
        coin = await coin_query.get_coin_by_id(coin_id)
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")
        return {"coin": coin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/name/{coin_name}")
async def get_coin_by_name(coin_name: str):
    """Получить монету по имени"""
    try:
        coin = await coin_query.get_coin_by_name(coin_name)
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")
        return {"coin": coin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coin by name {coin_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{coin_id}")
async def update_coin(coin_id: int, coin_data: dict):
    """Обновить данные монеты"""
    try:
        coin = await coin_query.update_coin(coin_id, coin_data)
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")
        return {"message": "Coin updated successfully", "coin": coin}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{coin_id}")
async def delete_coin(coin_id: int):
    """Удалить монету"""
    try:
        success = await coin_query.delete_coin(coin_id)
        if not success:
            raise HTTPException(status_code=404, detail="Coin not found")
        return {"message": "Coin deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{coin_id}/timeseries")
async def get_coin_timeseries(coin_id: int):
    """Получить временные ряды для монеты"""
    try:
        coin = await coin_query.get_coin_by_id(coin_id)
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")
        
        timeseries = await coin_query.get_coin_timeseries(coin_id)
        return {
            "coin_id": coin_id,
            "timeseries": timeseries
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeseries for coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{coin_id}/timeseries")
async def create_timeseries(coin_id: int, timeseries_data: dict):
    """Создать временной ряд для монеты"""
    try:
        coin = await coin_query.get_coin_by_id(coin_id)
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")
        
        timeseries = await coin_query.create_timeseries(coin_id, timeseries_data)
        return {
            "message": "Timeseries created successfully",
            "timeseries": timeseries
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating timeseries for coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_coins_stats():
    """Получить статистику по монетам"""
    try:
        stats = await coin_query.get_coins_stats()
        return {"stats": stats}
    except Exception as e:
        logger.error(f"Error getting coins stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limited/{coin_id}")
async def get_coin_with_rate_limit(
    coin_id: int,
    api_key_id: int = Query(..., description="ID API ключа для проверки лимитов"),
    validated_api_key: int = Depends(get_user_api_key_for_request)
):
    """
    Получить информацию о монете с проверкой лимитов API ключа
    Этот эндпоинт демонстрирует использование системы лимитирования
    """
    try:
        coin = await coin_query.get_coin_by_id(coin_id)
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")
        
        return {
            "coin": coin,
            "api_key_id": validated_api_key,
            "message": "Request successful - rate limit checked"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coin {coin_id} with rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))
