"""
KuCoin API Service с интеграцией лимитирования запросов
"""
import logging
import re
from typing import Dict, Any, Literal, Optional, List
from fastapi import HTTPException
from datetime import datetime, timedelta
import pandas as pd

from kucoin.client import Market, Trade, User
from core.database.orm import UserQuery, CoinQuery
from core.database.models import KucoinApiKey

logger = logging.getLogger(__name__)

class ExApiService:
    """Сервис для работы с KuCoin API с проверкой лимитов"""
    
    def __init__(self, api_key_id: int, api_credentials: Dict[str, str]):
        """
        Инициализация сервиса KuCoin API
        
        Args:
            api_key_id: ID API ключа для проверки лимитов
            api_credentials: Словарь с ключами api_key, api_secret, api_passphrase
        """
        self.api_key_id = api_key_id
        self.credentials = api_credentials
        
        # Инициализируем клиенты KuCoin
        self.market = Market(
            key=api_credentials['api_key'],
            secret=api_credentials['api_secret'],
            passphrase=api_credentials['api_passphrase']
        )
        
        self.trade = Trade(
            key=api_credentials['api_key'],
            secret=api_credentials['api_secret'],
            passphrase=api_credentials['api_passphrase']
        )
        
        self.user = User(
            key=api_credentials['api_key'],
            secret=api_credentials['api_secret'],
            passphrase=api_credentials['api_passphrase']
        )
    
    async def _check_rate_limit(self):
        """Проверить лимиты перед выполнением запроса"""
        can_proceed = await UserQuery.check_and_increment_request_count(self.api_key_id)
        
        if not can_proceed:
            usage_info = await UserQuery.get_api_key_usage_info(self.api_key_id)
            
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
            
    
    # Market Data Methods
    async def async_get_kline_spot(self, symbol: str, 
                             time: Literal["5min", "15min", "30min", "1hour", "4hour", "1day", "1week", "1mouth", "1year"] = "5min",
                             last_datetime: datetime = None) -> pd.DataFrame | None:

        # cls.logger.info(f"Get coin: {symbol} time: {time=} last_datetime: {last_datetime=}")

        try:
            data = await self.market.async_get_kline(symbol, time)
        except Exception as e:
            logger.error(f"Error get kline {symbol} - {e}")
            return None

        colums = ["datetime", "open", "close", "max", "min", "_", "volume"]

        df = pd.DataFrame(data, columns=colums).drop("_", axis=1)

        if len(df) == 0:
            logger.error(f"Error get kline {symbol} - {len(df)=}")
            return None

        df["datetime"] = df["datetime"].apply(lambda x: datetime.fromtimestamp(int(x)))
        
        df["datetime"] = pd.to_datetime(df['datetime'])

        if last_datetime:
            df = df[df["datetime"] >= last_datetime]

        if "day" in time or "week" in time:
            df["datetime"] = df["datetime"].dt.strftime('%Y-%m-%d')
        else:
            df["datetime"] = df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')

        df["volume"] = df["volume"].apply(float)

        # df = DatasetTimeseries(df)

        return symbol, df

    async def get_symbols(self, market: Optional[str] = None) -> Dict[str, Any]:
        """Получить список торговых пар"""
        await self._check_rate_limit()
        try:
            if market == "spot":
                data = self.market.get_symbol_list_spot()
            else:
                data = self.market.get_symbol_list_future()
        except Exception as e:
            logger.error(f"KuCoin API error in get_symbols: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
        
        await CoinQuery.coins_add(data, market)
        
        return data
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Получить тикер для символа"""
        await self._check_rate_limit()

        coin_orm = await CoinQuery.get_coin_by_symbol(symbol)

        if coin_orm and coin_orm.updated < datetime.now() - timedelta(minutes=1):
            type_market = "spot" if coin_orm.type == "spot" else "future"
            try:
                if type_market == "spot":
                    result = self.market.get_ticker_spot(symbol)
                else:
                    result = self.market.get_ticker_future(symbol)
            except Exception as e:
                logger.error(f"KuCoin API error in get_ticker_{type_market}: {e}")
                raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")

            # print(f"{symbol=} {result=}")
            await CoinQuery.update_price_coin(coin_orm.id, float(result.get('price')))

            data = {
                "symbol": symbol,
                "price": result.get('price'),
                "updated": datetime.now(),
            }

        else:
            data = {
                "symbol": symbol,
                "price": coin_orm.last_price,
                "updated": coin_orm.updated,
            }

        return data
    
    async def get_all_tickers(self, save_to_db: bool = False) -> Dict[str, Any]:
        """Получить все тикеры"""
        await self._check_rate_limit()
        
        try:
            response = self.market.get_all_tickers()
            
            # Сохраняем тикеры в БД если запрошено
            if save_to_db and 'ticker' in response:
                try:
                    await CoinQuery.bulk_update_tickers(response['ticker'])
                    logger.info(f"Saved {len(response['ticker'])} tickers to database")
                except Exception as db_error:
                    logger.error(f"Error saving tickers to database: {db_error}")
                    # Не прерываем выполнение, только логируем ошибку
            
            return response
        except Exception as e:
            logger.error(f"KuCoin API error in get_all_tickers: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
    
    async def get_24hr_stats(self, symbol: str) -> Dict[str, Any]:
        """Получить 24-часовую статистику"""
        await self._check_rate_limit()
        
        try:
            return self.market.get_24hr_stats(symbol)
        except Exception as e:
            logger.error(f"KuCoin API error in get_24hr_stats: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
    
    async def get_klines(self, symbol: str, kline_type: str = '1h', 
                        start_at: Optional[int] = None, end_at: Optional[int] = None) -> Dict[str, Any]:
        """Получить свечи (klines)"""
        await self._check_rate_limit()
        
        try:
            # Исправляем вызов метода get_kline - передаем параметры в правильном порядке
            kwargs = {}
            if start_at:
                kwargs['startAt'] = start_at
            if end_at:
                kwargs['endAt'] = end_at
            
            return self.market.get_kline(symbol, kline_type, **kwargs)
        except Exception as e:
            logger.error(f"KuCoin API error in get_klines: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
    
    # User Account Methods
    async def get_account_info(self) -> Dict[str, Any]:
        """Получить информацию об аккаунте"""
        await self._check_rate_limit()
        
        try:
            return self.user.get_account_list()
        except Exception as e:
            logger.error(f"KuCoin API error in get_account_info: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
    
    async def get_account_balance(self, currency: Optional[str] = None) -> Dict[str, Any]:
        """Получить баланс аккаунта"""
        await self._check_rate_limit()
        
        try:
            if currency:
                return self.user.get_account(currency)
            else:
                return self.user.get_account_list()
        except Exception as e:
            logger.error(f"KuCoin API error in get_account_balance: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
    
    # Trade Methods
    async def create_order(self, symbol: str, side: str, order_type: str, 
                          size: str, price: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Создать ордер"""
        await self._check_rate_limit()
        
        try:
            if order_type == 'limit':
                if not price:
                    raise ValueError("Price is required for limit orders")
                
                return self.trade.create_limit_order(symbol, side, size, price, **kwargs)
            
            elif order_type == 'market':
                
                return self.trade.create_market_order(symbol, side, size, **kwargs)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"KuCoin API error in create_order: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
    
    async def get_orders(self, symbol: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Получить список ордеров"""
        await self._check_rate_limit()
        
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            if status:
                params['status'] = status
            return self.trade.get_order_list(**params)
        except Exception as e:
            logger.error(f"KuCoin API error in get_orders: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Отменить ордер"""
        await self._check_rate_limit()
        
        try:
            return self.trade.cancel_order(order_id)
        except Exception as e:
            logger.error(f"KuCoin API error in cancel_order: {e}")
            raise HTTPException(status_code=500, detail=f"KuCoin API error: {str(e)}")


async def get_ex_service(api_key_id: int, user_id: int) -> ExApiService:
    """
    Фабричная функция для создания ExApiService
    
    Args:
        api_key_id: ID API ключа
        user_id: ID пользователя
        
    Returns:
        ExApiService: Инициализированный сервис
        
    Raises:
        HTTPException: Если API ключ не найден или не принадлежит пользователю
    """
    try:
        # Проверяем, что API ключ принадлежит пользователю
        user_api_keys = await UserQuery.get_kucoin_api_keys_by_user_id(user_id)
        api_key = next((key for key in user_api_keys if key.id == api_key_id), None)
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        if not api_key.is_active:
            raise HTTPException(status_code=403, detail="API key is inactive")
        
        # Подготавливаем credentials
        credentials = {
            'api_key': api_key.api_key,
            'api_secret': api_key.api_secret,
            'api_passphrase': api_key.api_passphrase
        }
        
        return ExApiService(api_key_id, credentials)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating KuCoin service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
