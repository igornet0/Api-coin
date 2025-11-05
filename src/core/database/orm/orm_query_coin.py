# файл для query запросов
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from src.core.database.models import (Coin, Timeseries, DataTimeseries)

class PriceData(BaseModel):
    price_now: float
    max_price_now: float
    min_price_now: float
    open_price_now: float
    volume_now:float

"""
ORM запросы для работы с монетами и тикерами KuCoin
"""

from src.core.database import get_db_helper

class CoinQuery:
    """Класс для работы с запросами к таблице монет"""

    @staticmethod
    async def add_coin(
            name: str,
            price_now: float = 0) -> Coin:

        async with get_db_helper().get_session() as session:
        
            query = select(Coin).where(Coin.name == name)
            result = await session.execute(query)

            if not result.scalars().first():
                coin = Coin(name=name,
                        price_now=price_now)
                session.add(coin)
                await session.commit()
                await session.refresh(coin)
                return coin
            
            raise ValueError(f"Coin {name} already exists")

    @staticmethod
    async def delete_coin(coin_name: str) -> bool:
        async with get_db_helper().get_session() as session:
            query = delete(Coin).where(Coin.name == coin_name)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def get_coin_by_id(coin_id: int) -> Optional[Coin]:
        """Получить монету по ID"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.id == coin_id)
            result = await session.execute(query)
            return result.scalar()

    @staticmethod
    async def get_coin_by_symbol(symbol: str, 
                                 parsed: bool = None) -> Optional[Coin]:
        """Получить монету по символу (например, BTC-USDT)"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.symbol == symbol)
            if parsed:
                query = query.where(Coin.parsed == parsed)

            result = await session.execute(query)

            return result.scalar()

    @staticmethod
    async def get_all_coins(limit: int = 100, offset: int = 0) -> List[Coin]:
        """Получить все монеты с пагинацией"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.parsed == True).offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_coins() -> List[Coin]:
        """Получить все монеты"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.parsed == True)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_coins_by_symbols(symbols: List[str]) -> List[Coin]:
        """Получить монеты по списку символов"""
        async with get_db_helper().get_session() as session:
            query = select(Coin).where(Coin.symbol.in_(symbols))
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def update_price_coin(coin_id: int, price: float) -> Coin:
        """Обновить цену монеты"""
        async with get_db_helper().get_session() as session:
            query = update(Coin).where(Coin.id == coin_id).values(last_price=price)
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def bulk_update_tickers(tickers_data: List[Dict[str, Any]]) -> List[Coin]:
        """
        Массовое обновление тикеров
        
        Args:
            tickers_data: Список данных тикеров от KuCoin API
            
        Returns:
            List[Coin]: Список обновленных монет
        """
        updated_coins = []
        
        for ticker_data in tickers_data:
            try:
                coin = await CoinQuery.create_or_update_coin_from_ticker(ticker_data)
                updated_coins.append(coin)
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку остальных
                print(f"Error updating ticker {ticker_data.get('symbol', 'unknown')}: {e}")
                continue
        
        return updated_coins
    
    @staticmethod
    async def coins_add(coins: List):
        async with get_db_helper().get_session() as session:
            for coin in coins:
                existing_coin = await CoinQuery.get_coin_by_symbol(coin.get('symbol'))
                if existing_coin:
                    continue
                session.add(Coin(name=coin.get('symbol', coin.get('name', "ERROR_SYMBOL"))))
            
                await session.commit()

    @staticmethod
    async def get_top_volume_coins(limit: int = 50) -> List[Coin]:
        """Получить топ монет по объему торгов"""
        async with get_db_helper().get_session() as session:
            query = (
                select(Coin)
                .where(Coin.parsed == True)
                .order_by(Coin.volume_now.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def update_coin_price(name: str, price_data: PriceData):
        async with get_db_helper().get_session() as session:
            query = update(Coin).where(Coin.name == name).values(price_now=price_data.price_now,
                                                                max_price_now=price_data.max_price_now,
                                                                min_price_now=price_data.min_price_now,
                                                                open_price_now=price_data.open_price_now,
                                                                volume_now=price_data.volume_now)
            await session.execute(query)
            await session.commit()

    # @staticmethod
    # async def get_top_gainers(limit: int = 50) -> List[Coin]:
    #     """Получить топ монеты по росту цены"""
    #     async with get_db_helper().get_session() as session:
    #         query = (
    #             select(Coin)
    #             .where(Coin.parsed == True)
    #             .order_by(Coin.change_rate.desc())
    #             .limit(limit)
    #         )
    #         result = await session.execute(query)
    #         return result.scalars().all()

    # @staticmethod
    # async def get_top_losers(limit: int = 50) -> List[Coin]:
    #     """Получить топ монеты по падению цены"""
    #     async with get_db_helper().get_session() as session:
    #         query = (
    #             select(Coin)
    #             .where(Coin.is_active == True)
    #             .order_by(Coin.change_rate.asc())
    #             .limit(limit)
    #         )
    #         result = await session.execute(query)
    #         return result.scalars().all()

    @staticmethod
    async def get_all_data_timeseries_by_coin(coin: Coin | str):
        """
        Получить все DataTimeseries для монеты через все её timeseries
        """
        if isinstance(coin, str):
            coin = await CoinQuery.get_coin_by_symbol(symbol=coin)
            
        if not coin:
            raise ValueError(f"Coin {coin} not found")
        
        # Получаем все timeseries для монеты
        timeseries_list = await CoinQuery.get_timeseries_by_coin(coin=coin)
        
        if not timeseries_list:
            return []
        
        # Получаем все DataTimeseries для всех timeseries
        timeseries_ids = [ts.id for ts in timeseries_list]
        
        query = select(DataTimeseries).where(
            DataTimeseries.timeseries_id.in_(timeseries_ids)
        ).order_by(DataTimeseries.datetime)
        
        async with get_db_helper().get_session() as session:
            result = await session.execute(query)

            return result.scalars().all()

    @staticmethod
    async def search_coins_by_symbol(search_term: str, limit: int = 20) -> List[Coin]:
        """Поиск монет по символу"""
        async with get_db_helper().get_session() as session:
            query = (
                select(Coin)
                .where(
                    Coin.parsed == True,
                    Coin.symbol.ilike(f"%{search_term.upper()}%")
                )
                .limit(limit)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def deactivate_old_coins(hours_threshold: int = 24) -> int:
        """
        Деактивировать монеты, которые не обновлялись более указанного времени
        
        Args:
            hours_threshold: Количество часов без обновления
            
        Returns:
            int: Количество деактивированных монет
        """
        async with get_db_helper().get_session() as session:

            threshold_time = datetime.now() - timedelta(hours=hours_threshold)
            
            query = (
                update(Coin)
                .where(
                    Coin.is_active == True,
                    Coin.last_updated < threshold_time
                )
                .values(is_active=False)
            )
            result = await session.execute(query)
            await session.commit()
            return result.rowcount

    @staticmethod
    async def get_timeseries_by_coin(coin: Coin | str, timestamp: str = None) -> List[Timeseries]:
        async with get_db_helper().get_session() as session:

            if isinstance(coin, str):
                coin = await CoinQuery.get_coin_by_symbol(symbol=coin)

                if not coin:
                    raise ValueError(f"Coin {coin} not found")

            query = select(Timeseries).options(joinedload(Timeseries.coin)).where(Timeseries.coin_id == coin.id)
            if timestamp:
                query = query.where(Timeseries.timestamp == timestamp)
            
            result = await session.execute(query)

            return result.scalars().all()

    @staticmethod
    async def get_data_timeseries(timeseries_id: int) -> List[DataTimeseries]:
        async with get_db_helper().get_session() as session:
            query = select(DataTimeseries).where(DataTimeseries.timeseries_id == timeseries_id)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_data_timeseries_by_datetime(timeseries_id: int, datetime: datetime) -> DataTimeseries:
        async with get_db_helper().get_session() as session:
            query = select(DataTimeseries).where(DataTimeseries.timeseries_id == timeseries_id, DataTimeseries.datetime == datetime)
            result = await session.execute(query)
            return result.scalar()

    @staticmethod
    async def add_timeseries(coin: Coin | str, timestamp: str, path_dataset: str) -> Timeseries:
        async with get_db_helper().get_session() as session:
            if isinstance(coin, str):
                coin = await CoinQuery.get_coin_by_symbol(symbol=coin)

            if not coin:
                raise ValueError(f"Coin {coin} not found")
            ts = Timeseries(coin_id=coin.id, timestamp=timestamp, path_dataset=path_dataset)
            session.add(ts)
            await session.commit()
            await session.refresh(ts)
            return ts

    @staticmethod
    async def add_data_timeseries(timeseries_id: int, data_timeseries: dict):
        async with get_db_helper().get_session() as session:
            dt = await CoinQuery.get_data_timeseries_by_datetime(timeseries_id, data_timeseries["datetime"])

            if dt:
                return False
            
            session.add(DataTimeseries(timeseries_id=timeseries_id, **data_timeseries))
            await session.commit()

            return True
