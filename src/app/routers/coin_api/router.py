"""
Роутер для работы с данными монет из базы данных
"""
from uuid import RFC_4122
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from src.app.configuration.auth import verify_authorization
from src.app.routers.market.router import get_symbols, get_ticker
from src.core.database.orm import CoinQuery

router = APIRouter(prefix="/coin-data", tags=["coin_data"])
logger = logging.getLogger(__name__)


@router.get("/coins")
async def get_coins(
    limit: int = Query(50, description="Количество монет", ge=1, le=1000),
    offset: int = Query(0, description="Смещение", ge=0),
    api_key_id: int = Query(None, description="ID API ключа"),
    user: dict = Depends(verify_authorization)):
    """Получить список монет из базы данных"""
    try:
        coins = await CoinQuery.get_all_coins(limit=limit, offset=offset)

        if not coins:
            coins = await get_symbols(api_key_id=api_key_id, user=user)

        return {
            "coins": [
                {
                    "id": coin.id,
                    "name": coin.name,
                    "price_now": coin.price_now,
                    "max_price_now": coin.max_price_now,
                    "min_price_now": coin.min_price_now,
                    "open_price_now": coin.open_price_now,
                    "volume_now": coin.volume_now,
                    "parsed": coin.parsed,
                    "updated": coin.updated.isoformat()
                }
                for coin in coins
            ],
            "total": len(coins),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/coins/top-volume")
# async def get_top_volume_coins(
#     limit: int = Query(50, description="Количество монет", ge=1, le=100),
#     user: dict = Depends(verify_authorization)):
#     """Получить топ монеты по объему торгов"""
#     try:
#         coins = await CoinQuery.get_top_volume_coins(limit=limit)
        
#         return {
#             "coins": [
#                 {
#                     "id": coin.id,
#                     "symbol": coin.name,
#                     "name": coin.name,
#                     "last_price": coin.last_price,
#                     "volume": coin.volume,
#                     "volume_value": coin.volume_value,
#                     "change_rate": coin.change_rate,
#                     "updated": coin.updated.isoformat() if coin.updated else None
#                 }
#                 for coin in coins
#             ],
#             "total": len(coins)
#         }
#     except Exception as e:
#         logger.error(f"Error getting top volume coins: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/coins/top-gainers")
# async def get_top_gainers(
#     limit: int = Query(50, description="Количество монет", ge=1, le=100),
#     user: dict = Depends(verify_authorization)):
#     """Получить топ монеты по росту цены"""
#     try:
#         coins = await CoinQuery.get_top_gainers(limit=limit)
        
#         return {
#             "coins": [
#                 {
#                     "id": coin.id,
#                     "symbol": coin.name,
#                     "name": coin.name,
#                     "last_price": coin.last_price,
#                     "change_rate": coin.change_rate,
#                     "change_price": coin.change_price,
#                     "volume": coin.volume,
#                     "updated": coin.updated.isoformat() if coin.updated else None
#                 }
#                 for coin in coins
#             ],
#             "total": len(coins)
#         }
#     except Exception as e:
#         logger.error(f"Error getting top gainers: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/coins/top-losers")
# async def get_top_losers(
#     limit: int = Query(50, description="Количество монет", ge=1, le=100),
#     user: dict = Depends(verify_authorization)):
#     """Получить топ монеты по падению цены"""
#     try:
#         coins = await CoinQuery.get_top_losers(limit=limit)
        
#         return {
#             "coins": [
#                 {
#                     "id": coin.id,
#                     "symbol": coin.name,
#                     "name": coin.name,
#                     "last_price": coin.last_price,
#                     "change_rate": coin.change_rate,
#                     "change_price": coin.change_price,
#                     "volume": coin.volume,
#                     "updated": coin.updated.isoformat() if coin.updated else None
#                 }
#                 for coin in coins
#             ],
#             "total": len(coins)
#         }
#     except Exception as e:
#         logger.error(f"Error getting top losers: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/coins/search")
async def search_coins(
    q: str = Query(..., description="Поисковый запрос"),
    api_key_id: int = Query(None, description="ID API ключа"),
    limit: int = Query(20, description="Количество результатов", ge=1, le=100),
    user: dict = Depends(verify_authorization)):
    """Поиск монет по символу"""
    try:
        coins = await CoinQuery.search_coins_by_symbol(q, limit=limit)
        if api_key_id:
            for coin in coins:
                try:
                    data = await get_ticker(coin.name, api_key_id, user)
                    ticker = data.get('ticker')
                    coin.price_now = ticker.get('price')
                except Exception as e:
                    logger.error(f"Error getting ticker for {coin.name}: {e}")
                    continue
        
        return {
            "coins": [
                {
                    "id": coin.id,
                    "name": coin.name,
                    "price_now": coin.price_now,
                    "max_price_now": coin.max_price_now,
                    "min_price_now": coin.min_price_now,
                    "open_price_now": coin.open_price_now,
                    "volume_now": coin.volume_now,
                    "parsed": coin.parsed,
                    "updated": coin.updated.isoformat()
                }
                for coin in coins
            ],
            "query": q,
            "total": len(coins)
        }
    except Exception as e:
        logger.error(f"Error searching coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coins/{symbol}")
async def get_coin_by_symbol(
    symbol: str,
    user: dict = Depends(verify_authorization)
):
    """Получить детальную информацию о монете по символу"""
    try:
        coin = await CoinQuery.get_coin_by_symbol(symbol.upper())
        
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")
        
        return {
            "coin": {
                "id": coin.id,
                "symbol": coin.name,
                "name": coin.name,
                "last_price": coin.last_price,
                "volume": coin.volume,
                "updated": coin.updated.isoformat() if coin.updated else None,
                "is_active": coin.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coin {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coins/cleanup")
async def cleanup_old_coins(
    hours_threshold: int = Query(24, description="Количество часов без обновления", ge=1, le=168),
    user: dict = Depends(verify_authorization)
):
    """Деактивировать старые монеты"""
    try:
        deactivated_count = await CoinQuery.deactivate_old_coins(hours_threshold)
        
        return {
            "message": f"Deactivated {deactivated_count} old coins",
            "hours_threshold": hours_threshold,
            "deactivated_count": deactivated_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up old coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

