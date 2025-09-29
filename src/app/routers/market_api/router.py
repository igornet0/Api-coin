from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging

from kucoin.client import Market
from core.settings import get_settings
from core.database.orm import CoinQuery
from core.database.models import Coin

router = APIRouter()
logger = logging.getLogger(__name__)

# Инициализация KuCoin клиента
kucoin_client = Market(
    key=get_settings().kucoin.api_key,
    secret=get_settings().kucoin.api_secret,
    passphrase=get_settings().kucoin.api_passphrase
)

coin_query = CoinQuery()


@router.get("/symbols")
async def get_symbols(market: Optional[str] = None):
    """Получить список всех торговых пар"""
    try:
        symbols = kucoin_client.get_symbol_list(market=market) if market else kucoin_client.get_symbol_list()
        return {"symbols": symbols}
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    """Получить тикер для конкретной торговой пары"""
    try:
        ticker = kucoin_client.get_ticker(symbol)
        return {"symbol": symbol, "ticker": ticker}
    except Exception as e:
        logger.error(f"Error getting ticker for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickers")
async def get_all_tickers():
    """Получить все тикеры"""
    try:
        tickers = kucoin_client.get_all_tickers()
        return tickers
    except Exception as e:
        logger.error(f"Error getting all tickers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{symbol}")
async def get_24h_stats(symbol: str):
    """Получить 24-часовую статистику для торговой пары"""
    try:
        stats = kucoin_client.get_24h_stats(symbol)
        return {"symbol": symbol, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting 24h stats for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str, 
    kline_type: str = "1min",
    start_at: Optional[int] = None,
    end_at: Optional[int] = None
):
    """Получить свечные данные (klines) для торговой пары"""
    try:
        kwargs = {}
        if start_at:
            kwargs["startAt"] = start_at
        if end_at:
            kwargs["endAt"] = end_at
            
        klines = kucoin_client.get_kline(symbol, kline_type, **kwargs)
        return {
            "symbol": symbol,
            "type": kline_type,
            "klines": klines
        }
    except Exception as e:
        logger.error(f"Error getting klines for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/currencies")
async def get_currencies():
    """Получить список всех валют"""
    try:
        currencies = kucoin_client.get_currencies()
        return {"currencies": currencies}
    except Exception as e:
        logger.error(f"Error getting currencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/currency/{currency}")
async def get_currency_detail(currency: str, chain: Optional[str] = None):
    """Получить детали валюты"""
    try:
        detail = kucoin_client.get_currency_detail_v2(currency, chain=chain)
        return {"currency": currency, "detail": detail}
    except Exception as e:
        logger.error(f"Error getting currency detail for {currency}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-ticker/{symbol}")
async def sync_ticker_to_db(symbol: str):
    """Синхронизировать тикер с базой данных"""
    try:
        # Получаем данные с биржи
        ticker = kucoin_client.get_ticker(symbol)
        stats = kucoin_client.get_24h_stats(symbol)
        
        # Извлекаем данные для сохранения
        coin_name = symbol.replace("-", "").replace("_", "").lower()
        
        coin_data = {
            "name": coin_name,
            "price_now": float(ticker.get("price", 0)),
            "max_price_now": float(stats.get("high", 0)),
            "min_price_now": float(stats.get("low", 0)),
            "open_price_now": float(stats.get("last", 0)),  # Используем last как open
            "volume_now": float(stats.get("vol", 0)),
            "parsed": True
        }
        
        # Сохраняем или обновляем в БД
        coin = await coin_query.get_or_create_coin(coin_data)
        
        return {
            "message": f"Ticker for {symbol} synced successfully",
            "coin_id": coin.id,
            "data": coin_data
        }
        
    except Exception as e:
        logger.error(f"Error syncing ticker for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all-tickers")
async def sync_all_tickers_to_db():
    """Синхронизировать все тикеры с базой данных"""
    try:
        tickers = kucoin_client.get_all_tickers()
        synced_count = 0
        errors = []
        
        for ticker_data in tickers.get("ticker", []):
            try:
                symbol = ticker_data.get("symbol")
                if not symbol:
                    continue
                    
                coin_name = symbol.replace("-", "").replace("_", "").lower()
                
                coin_data = {
                    "name": coin_name,
                    "price_now": float(ticker_data.get("last", 0)),
                    "max_price_now": float(ticker_data.get("high", 0)),
                    "min_price_now": float(ticker_data.get("low", 0)),
                    "open_price_now": float(ticker_data.get("last", 0)),
                    "volume_now": float(ticker_data.get("vol", 0)),
                    "parsed": True
                }
                
                await coin_query.get_or_create_coin(coin_data)
                synced_count += 1
                
            except Exception as e:
                errors.append(f"Error syncing {symbol}: {str(e)}")
                logger.error(f"Error syncing ticker {symbol}: {e}")
        
        return {
            "message": f"Synced {synced_count} tickers",
            "synced_count": synced_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error syncing all tickers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
