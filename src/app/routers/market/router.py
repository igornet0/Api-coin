"""
KuCoin Market API роутер с интеграцией лимитирования
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
import logging

from src.app.configuration.auth import verify_authorization
from src.app.services import get_ex_service
from src.app.configuration.schemas.user import KucoinApiKeyResponse

router = APIRouter(prefix="/kucoin/market", tags=["kucoin_market"])
logger = logging.getLogger(__name__)


@router.get("/symbols")
async def get_symbols(
    api_key_id: int = Query(..., description="ID API ключа"),
    market: Optional[str] = Query(None, description="Фильтр по рынку"),
    user: dict = Depends(verify_authorization)
):
    """Получить список торговых пар с KuCoin"""
    try:
        kucoin_service = await get_ex_service(api_key_id, user.id)
        symbols = await kucoin_service.get_symbols(market)
        
        return {
            "symbols": symbols,
            "api_key_id": api_key_id,
            "market_filter": market
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol}")
async def get_ticker(
    symbol: str,
    api_key_id: int = Query(..., description="ID API ключа"),
    user: dict = Depends(verify_authorization)) -> Dict[str, Any]:
    """Получить тикер для конкретной торговой пары"""
    try:
        kucoin_service = await get_ex_service(api_key_id, user.id)
        ticker = await kucoin_service.get_ticker(symbol)
        
        return {
            "ticker": ticker,
            "symbol": symbol,
            "api_key_id": api_key_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticker for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickers")
async def get_all_tickers(
    api_key_id: int = Query(..., description="ID API ключа"),
    save_to_db: bool = Query(False, description="Сохранить тикеры в базу данных"),
    user: dict = Depends(verify_authorization)
):
    """Получить все тикеры"""
    try:
        kucoin_service = await get_ex_service(api_key_id, user.id)
        tickers = await kucoin_service.get_all_tickers(save_to_db=save_to_db)
        
        return {
            "tickers": tickers,
            "api_key_id": api_key_id,
            "saved_to_db": save_to_db
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all tickers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{symbol}")
async def get_24hr_stats(
    symbol: str,
    api_key_id: int = Query(..., description="ID API ключа"),
    user: dict = Depends(verify_authorization)
):
    """Получить 24-часовую статистику для торговой пары"""
    try:
        kucoin_service = await get_ex_service(api_key_id, user.id)
        stats = await kucoin_service.get_24hr_stats(symbol)
        
        return {
            "stats": stats,
            "symbol": symbol,
            "api_key_id": api_key_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting 24hr stats for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str,
    api_key_id: int = Query(..., description="ID API ключа"),
    kline_type: str = Query('1h', description="Тип свечей (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w, 1y)"),
    start_at: Optional[int] = Query(None, description="Время начала (timestamp)"),
    end_at: Optional[int] = Query(None, description="Время окончания (timestamp)"),
    user: dict = Depends(verify_authorization)
):
    """Получить свечи (klines) для торговой пары"""
    try:
        kucoin_service = await get_ex_service(api_key_id, user.id)
        klines = await kucoin_service.async_get_kline_spot(symbol, time=kline_type)

        return {
            "klines": klines,
            "symbol": symbol,
            "type": kline_type,
            "api_key_id": api_key_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting klines for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
